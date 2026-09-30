import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from llm_wiki.config import Settings
from llm_wiki.corpus import Source
from llm_wiki.normalization import extract_html, extract_pdf, normalize_corpus
from llm_wiki.verification import verify_oracle


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.raw = self.root / "raw"
        self.out = self.root / "normalized"
        self.source = Source(1, "Flood insurance", "FEMA", "PDF", "Coverage", "https://example.org")
        self.path = self.raw / self.source.folder / (self.source.filename_stem + ".pdf")
        self.path.parent.mkdir(parents=True)
        self.body = "Flood insurance covers damage caused by rising water. " * 25
        self.path.write_text(
            f"<html><head><title>Flood</title></head><body><nav>MENU</nav><main>"
            f"<h1>Coverage</h1><p>{self.body}</p></main><footer>FOOTER</footer></body></html>",
            encoding="utf-8",
        )
        self.review = self.root / "review.json"
        self.write_review({})

    def write_review(self, entry):
        self.review.write_text(json.dumps({"sources": {"1": entry}}), encoding="utf-8")

    def accept(self):
        record = self.run_normalizer()["sources"][0]
        self.write_review(
            {
                "decision": "accept",
                "note": "Reviewed for readable coverage content",
                "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
                "normalized_sha256": record["normalized_sha256"],
            }
        )

    def run_normalizer(self):
        return normalize_corpus([self.source], self.raw, self.out, self.review)

    def test_html_removes_navigation_and_preserves_heading(self):
        sections, warnings = extract_html(self.path)
        self.assertEqual(warnings, [])
        self.assertEqual(sections[0]["locator"], "Coverage")
        self.assertNotIn("MENU", sections[0]["text"])
        self.assertNotIn("FOOTER", sections[0]["text"])

    def test_html_forms_and_definition_lists_retain_content(self):
        self.path.write_text(
            "<html><body><form><main><dl><dt>Deductible</dt><dd>The retained amount.</dd>"
            "</dl></main></form></body></html>"
        )
        sections, _ = extract_html(self.path)
        self.assertEqual(sections, [{"locator": "Deductible", "text": "The retained amount."}])

    def test_reviewed_selector_excludes_unrelated_content(self):
        self.path.write_text(
            '<html><main><div id="source"><h1>Coverage</h1><p>Source text</p></div>'
            "<p>Advertising</p></main></html>"
        )
        sections, _ = extract_html(self.path, "#source")
        self.assertEqual(sections[0]["text"], "Source text")
        with self.assertRaises(ValueError):
            extract_html(self.path, "#missing")

    def test_mislabeled_pdf_is_extracted_by_signature_and_preserved(self):
        original = self.path.read_bytes()
        self.accept()
        report = self.run_normalizer()
        record = report["sources"][0]
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["detected_format"], "html")
        self.assertIsNone(record["retrieved_at"])
        self.assertTrue(record["warnings"])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertIn("## Coverage", (self.out / record["normalized_path"]).read_text())

    def test_unreviewed_or_changed_source_is_never_autoaccepted(self):
        self.assertEqual(self.run_normalizer()["accepted_count"], 0)
        self.accept()
        self.path.write_text(self.path.read_text() + "<!-- changed -->")
        self.assertEqual(self.run_normalizer()["accepted_count"], 0)

    def test_review_can_accept_cached_extraction_without_reparsing(self):
        self.run_normalizer()
        self.accept()
        with patch("llm_wiki.normalization.extract_html", side_effect=AssertionError("reparsed")):
            self.assertEqual(self.run_normalizer()["accepted_count"], 1)

    def test_corrupt_cached_artifact_is_regenerated(self):
        self.accept()
        record = self.run_normalizer()["sources"][0]
        target = self.out / record["normalized_path"]
        target.write_text("corrupt")
        self.assertEqual(self.run_normalizer()["accepted_count"], 1)
        self.assertIn("## Coverage", target.read_text())

    def test_exclusion_requires_reason_and_does_not_extract(self):
        self.write_review({"decision": "exclude"})
        with self.assertRaises(ValueError):
            self.run_normalizer()
        self.write_review({"decision": "exclude", "note": "Landing page only"})
        self.assertEqual(self.run_normalizer()["counts"], {"excluded": 1})

    def test_raw_output_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_corpus([self.source], self.raw, self.raw / "output", self.review)

    def test_missing_and_ambiguous_sources_require_review(self):
        self.path.unlink()
        self.assertEqual(self.run_normalizer()["counts"], {"needs_review": 1})
        self.path.write_text("<html>first</html>")
        self.path.with_suffix(".html").write_text("<html>second</html>")
        self.assertEqual(self.run_normalizer()["counts"], {"needs_review": 1})

    def test_access_denied_html_cannot_be_accepted(self):
        self.path.write_text(f"<html><title>Access Denied</title><main>{self.body}</main></html>")
        self.accept()
        self.assertEqual(self.run_normalizer()["accepted_count"], 0)

    def test_pdf_page_locators_and_sparse_page_warning(self):
        reader = SimpleNamespace(
            is_encrypted=False,
            pages=[
                Mock(extract_text=Mock(return_value=self.body)),
                Mock(extract_text=Mock(return_value="")),
            ],
        )
        with patch("pypdf.PdfReader", return_value=reader):
            sections, warnings = extract_pdf(self.path)
        self.assertEqual([s["locator"] for s in sections], ["PDF page 1", "PDF page 2"])
        self.assertIn("PDF page 2", warnings[0])


class OracleVerificationTests(unittest.TestCase):
    def test_credentials_are_hidden_in_settings_repr(self):
        settings = Settings(Path("manifest"), Path("raw"), oracle_password="private-test-value")
        self.assertNotIn("private-test-value", repr(settings))

    def test_oracle_cleans_up_created_table_if_insert_fails(self):
        settings = Settings(Path("manifest"), Path("raw"), oracle_password="test")
        cursor = Mock()
        cursor.execute.side_effect = [None, RuntimeError("insert failed"), None]
        connection = Mock()
        connection.cursor.return_value = Mock(
            __enter__=Mock(return_value=cursor), __exit__=Mock(return_value=False)
        )
        with patch("oracledb.connect") as connect:
            connect.return_value.__enter__.return_value = connection
            with self.assertRaisesRegex(RuntimeError, "insert failed"):
                verify_oracle(settings)
        self.assertTrue(
            cursor.execute.call_args_list[-1].args[0].startswith("DROP TABLE WIKI_CHECK_")
        )


if __name__ == "__main__":
    unittest.main()
