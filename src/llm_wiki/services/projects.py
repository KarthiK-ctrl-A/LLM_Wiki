"""Create, discover, and inspect isolated filesystem wiki projects."""

import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from llm_wiki.domain.pages import LINK_STYLES, ProjectConfig, slugify, validate_field_name
from llm_wiki.storage.markdown import MarkdownPageStore

PROJECT_FILE = ".wiki-project.json"
SCHEMA_FILE = "SCHEMA.md"
DEFAULT_PAGE_DIRECTORIES = {
    "entity": "entities",
    "concept": "concepts",
    "summary": "summaries",
    "overview": "topics",
}


def _atomic_json(path: Path, data: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            suffix=".part",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def schema_markdown(config: ProjectConfig) -> str:
    link_example = (
        "`[[Actual Cash Value]]` or `[[Actual Cash Value|ACV]]`"
        if config.link_style == "wikilink"
        else "`[Actual Cash Value](../concepts/actual-cash-value.md)`"
    )
    extra = "\n".join(f"- `{field}` (required)" for field in config.extra_frontmatter_fields)
    if not extra:
        extra = "- No project-specific fields."
    directories = "\n".join(
        f"- `{directory}/`: `{page_type}` pages."
        for page_type, directory in config.page_directories.items()
    )
    return f"""# Wiki Schema: {config.name}

Schema version: `{config.schema_version}`  
Project ID: `{config.project_id}`  
Link style: `{config.link_style}`

## Directories

{directories}
- `raw/`: immutable original source files; page-writing code must never modify them.

## File names

Page files use lowercase kebab-case names derived from their titles. Every page is a UTF-8
Markdown file. A page must remain inside the directory assigned to its type.

## Required YAML frontmatter

- `title`: nonblank display title.
- `type`: one of `entity`, `concept`, `summary`, or `overview`.
- `date_created`: ISO-8601 timestamp with timezone; preserved across updates.
- `date_updated`: ISO-8601 timestamp with timezone; refreshed on updates.
- `tags`: YAML list of strings.
- `sources`: YAML list of source identifiers, paths, or URLs.
{extra}

Unknown frontmatter fields are rejected so schema changes remain deliberate.

## Cross-references

Use {link_example}. Internal links must resolve to an existing page inside this project.
External HTTP(S) links are permitted with normal Markdown syntax. Links must not escape the
project directory.

## Raw-source rule

Files under `raw/` are source-of-truth inputs. Copy sources into that directory and never
rewrite them during page creation or maintenance. Derived wiki knowledge belongs in page
directories and must cite its sources in frontmatter.
"""


class ProjectService:
    def __init__(self, projects_root: Path):
        self.root = projects_root.resolve()

    def _project_path(self, slug: str) -> Path:
        normalized = slugify(slug)
        path = (self.root / normalized).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Project path escapes the projects directory")
        return path

    def create(
        self,
        name: str,
        *,
        slug: str | None = None,
        link_style: str = "wikilink",
        extra_frontmatter_fields: tuple[str, ...] = (),
    ) -> ProjectConfig:
        project_slug = slugify(slug or name)
        extras = tuple(validate_field_name(value) for value in extra_frontmatter_fields)
        if link_style not in LINK_STYLES:
            raise ValueError(f"Unsupported link style: {link_style}")
        config = ProjectConfig(
            project_id=str(uuid4()),
            name=name.strip(),
            slug=project_slug,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            link_style=link_style,
            page_directories=dict(DEFAULT_PAGE_DIRECTORIES),
            extra_frontmatter_fields=extras,
        )
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self._project_path(project_slug)
        if destination.exists():
            raise FileExistsError(f"Wiki project already exists: {project_slug}")
        temporary = self.root / f".{project_slug}.{uuid4().hex}.part"
        try:
            temporary.mkdir()
            for directory in config.directories:
                (temporary / directory).mkdir()
            _atomic_json(temporary / PROJECT_FILE, config.to_dict())
            (temporary / SCHEMA_FILE).write_text(
                schema_markdown(config), encoding="utf-8", newline="\n"
            )
            temporary.rename(destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return config

    def load(self, slug: str) -> tuple[Path, ProjectConfig]:
        path = self._project_path(slug)
        metadata = path / PROJECT_FILE
        if not metadata.is_file():
            raise FileNotFoundError(f"Wiki project not found: {slugify(slug)}")
        try:
            data = json.loads(metadata.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid project metadata: {metadata}") from exc
        config = ProjectConfig.from_dict(data)
        if config.slug != path.name:
            raise ValueError("Project metadata slug does not match its directory")
        return path, config

    def list(self) -> list[ProjectConfig]:
        if not self.root.is_dir():
            return []
        projects = []
        for metadata in sorted(self.root.glob(f"*/{PROJECT_FILE}")):
            try:
                data = json.loads(metadata.read_text(encoding="utf-8"))
                config = ProjectConfig.from_dict(data)
                if config.slug != metadata.parent.name:
                    raise ValueError("Project metadata slug does not match its directory")
                projects.append(config)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid registered wiki project: {metadata.parent.name}"
                ) from exc
        return projects

    def inspect(self, slug: str) -> dict:
        path, config = self.load(slug)
        schema = path / SCHEMA_FILE
        if not schema.is_file():
            raise ValueError(f"Wiki schema is missing: {schema}")
        store = MarkdownPageStore(path, config)
        pages = store.iter_pages()
        counts = Counter(store.read(page).metadata.type for page in pages)
        directories = {
            directory: {
                "exists": (path / directory).is_dir(),
                "markdown_files": len(list((path / directory).glob("*.md")))
                if (path / directory).is_dir()
                else 0,
            }
            for directory in config.directories
        }
        return {
            **config.to_dict(),
            "path": str(path),
            "schema_path": str(schema),
            "schema_summary": {
                "required_frontmatter": [
                    "title",
                    "type",
                    "date_created",
                    "date_updated",
                    "tags",
                    "sources",
                    *config.extra_frontmatter_fields,
                ],
                "link_style": config.link_style,
            },
            "directories": directories,
            "page_count": len(pages),
            "page_counts_by_type": {
                page_type: counts[page_type] for page_type in config.page_directories
            },
            "link_issues": store.validate_links(),
        }
