import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from llm_wiki.cli import main
from llm_wiki.services.projects import PROJECT_FILE, SCHEMA_FILE, ProjectService
from llm_wiki.storage.markdown import MarkdownPageStore, parse_page


class StepOneTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "wikis"
        self.service = ProjectService(self.root)

    def test_create_scaffolds_project_and_schema(self):
        config = self.service.create("Property & Casualty Insurance")
        project = self.root / config.slug
        self.assertEqual(config.slug, "property-casualty-insurance")
        self.assertEqual(str(UUID(config.project_id)), config.project_id)
        self.assertEqual(config.link_style, "wikilink")
        self.assertEqual(
            set(config.directories), {"entities", "concepts", "summaries", "topics", "raw"}
        )
        self.assertTrue(all((project / directory).is_dir() for directory in config.directories))
        self.assertTrue((project / PROJECT_FILE).is_file())
        schema = (project / SCHEMA_FILE).read_text(encoding="utf-8")
        self.assertIn("[[Actual Cash Value]]", schema)
        self.assertIn("date_created", schema)
        self.assertIn("immutable original source files", schema)
        _, loaded = self.service.load(config.slug)
        self.assertEqual(loaded.project_id, config.project_id)

    def test_two_projects_keep_independent_schema_settings(self):
        first = self.service.create("Insurance", link_style="wikilink")
        second = self.service.create(
            "Database Notes", link_style="markdown", extra_frontmatter_fields=("jurisdiction",)
        )
        listed = {project.slug: project for project in self.service.list()}
        self.assertEqual(set(listed), {first.slug, second.slug})
        self.assertEqual(listed[first.slug].link_style, "wikilink")
        self.assertEqual(listed[second.slug].link_style, "markdown")
        self.assertEqual(listed[second.slug].extra_frontmatter_fields, ("jurisdiction",))
        self.assertIn(
            "[Actual Cash Value]",
            (self.root / second.slug / SCHEMA_FILE).read_text(encoding="utf-8"),
        )

    def test_listing_reflects_manual_project_deletion(self):
        first = self.service.create("First")
        second = self.service.create("Second")
        shutil.rmtree(self.root / first.slug)
        self.assertEqual([project.slug for project in self.service.list()], [second.slug])

    def test_duplicate_project_and_invalid_configuration_are_rejected(self):
        self.service.create("Insurance")
        with self.assertRaises(FileExistsError):
            self.service.create("Insurance")
        for field in ("Title", "bad-field", "title"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.service.create("Another " + field, extra_frontmatter_fields=(field,))
        with self.assertRaises(ValueError):
            self.service.create("Bad style", link_style="html")

    def test_page_round_trip_and_update_preserve_creation_time(self):
        config = self.service.create("Insurance")
        times = iter(["2026-09-30T10:00:00Z", "2026-09-30T11:00:00Z"])
        store = MarkdownPageStore(self.root / config.slug, config, clock=lambda: next(times))
        path = store.create(
            "Actual Cash Value",
            "concept",
            "The depreciated value of covered property.",
            tags=("property", "claims"),
            sources=("source-55",),
        )
        created = store.read(path)
        self.assertEqual(
            path.relative_to(self.root / config.slug).as_posix(), "concepts/actual-cash-value.md"
        )
        self.assertEqual(created.metadata.date_created, "2026-09-30T10:00:00Z")
        updated = store.update(path, body="Updated sourced explanation.")
        self.assertEqual(updated.metadata.date_created, "2026-09-30T10:00:00Z")
        self.assertEqual(updated.metadata.date_updated, "2026-09-30T11:00:00Z")
        self.assertEqual(store.read(path).body, "Updated sourced explanation.\n")

    def test_project_specific_frontmatter_is_required_and_round_trips(self):
        config = self.service.create("Regulation", extra_frontmatter_fields=("jurisdiction",))
        store = MarkdownPageStore(self.root / config.slug, config)
        with self.assertRaisesRegex(ValueError, "missing=.*jurisdiction"):
            store.create("North Carolina", "entity", "State regulator")
        path = store.create(
            "North Carolina",
            "entity",
            "State regulator",
            extra={"jurisdiction": "US-NC"},
        )
        self.assertEqual(store.read(path).metadata.extra, {"jurisdiction": "US-NC"})

    def test_wikilinks_resolve_and_broken_links_are_reported(self):
        config = self.service.create("Insurance")
        store = MarkdownPageStore(self.root / config.slug, config)
        target = store.create("Actual Cash Value", "concept", "A valuation concept.")
        source = store.create(
            "Homeowners Insurance",
            "overview",
            "See [[Actual Cash Value|ACV]] and [[Missing Concept]].",
        )
        links = store.resolve_links(source)
        self.assertEqual(links[0].resolved_path, target.relative_to(store.root).as_posix())
        self.assertFalse(links[1].exists)
        self.assertEqual(
            store.validate_links(),
            [
                {
                    "page": "topics/homeowners-insurance.md",
                    "target": "Missing Concept",
                    "issue": "broken",
                }
            ],
        )

    def test_markdown_links_and_external_links_resolve(self):
        config = self.service.create("Markdown Wiki", link_style="markdown")
        store = MarkdownPageStore(self.root / config.slug, config)
        store.create("NFIP", "entity", "Federal flood insurance program.")
        source = store.create(
            "Flood Insurance",
            "overview",
            "See [NFIP](../entities/nfip.md) and [FEMA](https://www.fema.gov/).",
        )
        links = store.resolve_links(source)
        self.assertTrue(links[0].exists)
        self.assertFalse(links[0].external)
        self.assertTrue(links[1].external)
        self.assertEqual(store.validate_links(), [])

    def test_markdown_links_reject_non_web_schemes_and_raw_files(self):
        config = self.service.create("Markdown Wiki", link_style="markdown")
        project = self.root / config.slug
        raw = project / "raw/source.md"
        raw.write_text("source material", encoding="utf-8")
        store = MarkdownPageStore(project, config)
        source = store.create(
            "Unsafe links",
            "overview",
            "See [script](javascript:alert(1)) and [raw](../raw/source.md).",
        )
        links = store.resolve_links(source)
        self.assertFalse(links[0].exists)
        self.assertFalse(links[0].external)
        self.assertFalse(links[1].exists)

    def test_ambiguous_wikilink_is_reported(self):
        config = self.service.create("Insurance")
        store = MarkdownPageStore(self.root / config.slug, config)
        store.create("Flood", "entity", "Entity page")
        store.create("Flood", "concept", "Concept page")
        source = store.create("Flood Overview", "overview", "See [[Flood]].")
        resolution = store.resolve_links(source)[0]
        self.assertTrue(resolution.ambiguous)
        self.assertFalse(resolution.exists)

    def test_malformed_frontmatter_and_duplicate_keys_are_rejected(self):
        config = self.service.create("Insurance")
        missing = "---\ntitle: Test\n---\nBody\n"
        duplicate = (
            "---\ntitle: First\ntitle: Second\ntype: concept\n"
            "date_created: '2026-09-30T10:00:00Z'\ndate_updated: '2026-09-30T10:00:00Z'\n"
            "tags: []\nsources: []\n---\nBody\n"
        )
        for text in ("Body only", missing, duplicate):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_page(text, config)

    def test_path_escape_is_rejected_and_raw_source_is_untouched(self):
        config = self.service.create("Insurance")
        project = self.root / config.slug
        raw = project / "raw/source.txt"
        raw.write_text("immutable source", encoding="utf-8")
        store = MarkdownPageStore(project, config)
        with self.assertRaises(ValueError):
            store.read(Path("../outside.md"))
        with self.assertRaisesRegex(ValueError, "not a managed wiki page"):
            store.update(raw)
        store.create("Deductible", "concept", "A policyholder retention.")
        self.assertEqual(raw.read_text(encoding="utf-8"), "immutable source")

    def test_page_type_must_match_its_directory(self):
        config = self.service.create("Insurance")
        project = self.root / config.slug
        store = MarkdownPageStore(project, config)
        path = store.create("Carrier", "entity", "An insurer.")
        text = path.read_text(encoding="utf-8").replace("type: entity", "type: concept")
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match directory"):
            store.read(path)

    def test_inspect_counts_pages_directories_schema_and_links(self):
        config = self.service.create("Insurance")
        store = MarkdownPageStore(self.root / config.slug, config)
        store.create("Deductible", "concept", "See [[Missing]].")
        report = self.service.inspect(config.slug)
        self.assertEqual(report["page_count"], 1)
        self.assertEqual(report["page_counts_by_type"]["concept"], 1)
        self.assertTrue(report["directories"]["raw"]["exists"])
        self.assertEqual(report["schema_summary"]["link_style"], "wikilink")
        self.assertEqual(report["link_issues"][0]["target"], "Missing")

    def test_cli_create_list_and_inspect(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(
                [
                    "wiki",
                    "create",
                    "Insurance Research",
                    "--projects-dir",
                    str(self.root),
                ]
            )
        self.assertEqual(result, 0)
        self.assertTrue(json.loads(output.getvalue())["created"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["wiki", "list", "--projects-dir", str(self.root)])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["projects"][0]["slug"], "insurance-research")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(
                ["wiki", "inspect", "insurance-research", "--projects-dir", str(self.root)]
            )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["page_count"], 0)


if __name__ == "__main__":
    unittest.main()
