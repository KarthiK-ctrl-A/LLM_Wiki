"""Safe, atomic Markdown page storage with strict YAML frontmatter."""

import os
import re
import tempfile
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml

from llm_wiki.domain.pages import (
    CORE_FRONTMATTER_FIELDS,
    LinkResolution,
    PageMetadata,
    ProjectConfig,
    WikiPage,
    slugify,
)

FRONTMATTER_BOUNDARY = "---"
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


class StrictSafeLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently accepting the last value."""


def _construct_unique_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate frontmatter field: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _string_timestamp(value: Any, name: str) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"{name} must include a timezone")
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        raise ValueError(f"{name} must include a time and timezone")
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 string")
    return value


def parse_page(text: str, config: ProjectConfig) -> WikiPage:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith(FRONTMATTER_BOUNDARY + "\n"):
        raise ValueError("Page must begin with YAML frontmatter")
    closing = normalized.find("\n---\n", 4)
    if closing < 0:
        raise ValueError("Page frontmatter is missing its closing boundary")
    try:
        raw = yaml.load(normalized[4:closing], Loader=StrictSafeLoader)
    except yaml.YAMLError as exc:
        raise ValueError("Invalid YAML frontmatter") from exc
    if not isinstance(raw, dict):
        raise ValueError("Page frontmatter must be a mapping")
    expected = set(CORE_FRONTMATTER_FIELDS) | set(config.extra_frontmatter_fields)
    missing, unknown = expected - set(raw), set(raw) - expected
    if missing or unknown:
        raise ValueError(
            f"Frontmatter fields differ from schema; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )
    if not isinstance(raw["tags"], list) or not isinstance(raw["sources"], list):
        raise ValueError("tags and sources must be YAML lists")
    metadata = PageMetadata(
        title=raw["title"],
        type=raw["type"],
        date_created=_string_timestamp(raw["date_created"], "date_created"),
        date_updated=_string_timestamp(raw["date_updated"], "date_updated"),
        tags=tuple(raw["tags"]),
        sources=tuple(raw["sources"]),
        extra={name: raw[name] for name in config.extra_frontmatter_fields},
    )
    metadata.validate(config.extra_frontmatter_fields)
    return WikiPage(metadata=metadata, body=normalized[closing + 5 :])


def render_page(page: WikiPage, config: ProjectConfig) -> str:
    page.metadata.validate(config.extra_frontmatter_fields)
    frontmatter = yaml.safe_dump(
        page.metadata.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False
    ).strip()
    return f"---\n{frontmatter}\n---\n{page.body.rstrip()}\n"


class MarkdownPageStore:
    def __init__(
        self,
        project_root: Path,
        config: ProjectConfig,
        *,
        clock: Callable[[], str] = utc_now,
    ):
        self.root = project_root.resolve()
        self.config = config
        self.clock = clock

    def _confined(self, path: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError(f"Path escapes project directory: {path}")
        return resolved

    def _managed_page_type(self, path: Path) -> str:
        safe = self._confined(path)
        relative = safe.relative_to(self.root)
        if safe.suffix.casefold() != ".md" or len(relative.parts) < 2:
            raise ValueError(f"Path is not a managed wiki page: {relative}")
        page_types = {
            directory: page_type for page_type, directory in self.config.page_directories.items()
        }
        try:
            return page_types[relative.parts[0]]
        except KeyError as exc:
            raise ValueError(f"Path is not a managed wiki page: {relative}") from exc

    def page_path(self, page_type: str, title: str) -> Path:
        if page_type not in self.config.page_directories:
            raise ValueError(f"Unsupported page type: {page_type}")
        return self._confined(
            self.root / self.config.page_directories[page_type] / f"{slugify(title)}.md"
        )

    def read(self, path: Path) -> WikiPage:
        safe = self._confined(path if path.is_absolute() else self.root / path)
        expected_type = self._managed_page_type(safe)
        if not safe.is_file():
            raise ValueError(f"Wiki page does not exist: {path}")
        page = parse_page(safe.read_text(encoding="utf-8"), self.config)
        if page.metadata.type != expected_type:
            raise ValueError(
                f"Page type {page.metadata.type!r} does not match directory "
                f"{safe.relative_to(self.root).parts[0]!r}"
            )
        return page

    def create(
        self,
        title: str,
        page_type: str,
        body: str,
        *,
        tags: tuple[str, ...] = (),
        sources: tuple[str, ...] = (),
        extra: dict[str, Any] | None = None,
    ) -> Path:
        path = self.page_path(page_type, title)
        if path.exists():
            raise FileExistsError(f"Page already exists: {path.relative_to(self.root)}")
        timestamp = self.clock()
        page = WikiPage(
            metadata=PageMetadata(
                title=title,
                type=page_type,
                date_created=timestamp,
                date_updated=timestamp,
                tags=tags,
                sources=sources,
                extra=extra or {},
            ),
            body=body,
        )
        self._write(path, render_page(page, self.config), exclusive=True)
        return path

    def update(
        self,
        path: Path,
        *,
        body: str | None = None,
        tags: tuple[str, ...] | None = None,
        sources: tuple[str, ...] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> WikiPage:
        safe = self._confined(path if path.is_absolute() else self.root / path)
        current = self.read(safe)
        updated = WikiPage(
            metadata=PageMetadata(
                title=current.metadata.title,
                type=current.metadata.type,
                date_created=current.metadata.date_created,
                date_updated=self.clock(),
                tags=current.metadata.tags if tags is None else tags,
                sources=current.metadata.sources if sources is None else sources,
                extra=current.metadata.extra if extra is None else extra,
            ),
            body=current.body if body is None else body,
        )
        self._write(safe, render_page(updated, self.config), exclusive=False)
        return updated

    def _write(self, path: Path, text: str, *, exclusive: bool) -> None:
        safe = self._confined(path)
        safe.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=safe.parent,
                suffix=".part",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            if exclusive:
                # Reserve the destination atomically before replacing the empty placeholder.
                descriptor = os.open(safe, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(descriptor)
            os.replace(temporary, safe)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def iter_pages(self) -> list[Path]:
        pages = []
        for directory in dict.fromkeys(self.config.page_directories.values()):
            folder = self._confined(self.root / directory)
            if folder.is_dir():
                pages.extend(path for path in folder.rglob("*.md") if path.is_file())
        return sorted(pages)

    def resolve_links(self, path: Path) -> list[LinkResolution]:
        safe = self._confined(path if path.is_absolute() else self.root / path)
        page = self.read(safe)
        if self.config.link_style == "wikilink":
            raw_links = [match.group(1) for match in WIKILINK_PATTERN.finditer(page.body)]
            return [self._resolve_wikilink(value) for value in raw_links]
        raw_links = [match.group(1) for match in MARKDOWN_LINK_PATTERN.finditer(page.body)]
        return [self._resolve_markdown_link(safe, value) for value in raw_links]

    def _resolve_wikilink(self, value: str) -> LinkResolution:
        target = value.split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            return LinkResolution(value, target, False)
        candidate = Path(target)
        if candidate.suffix.casefold() == ".md" or len(candidate.parts) > 1:
            if not candidate.suffix:
                candidate = candidate.with_suffix(".md")
            try:
                safe = self._confined(self.root / candidate)
                self._managed_page_type(safe)
            except ValueError:
                return LinkResolution(value, target, False)
            return LinkResolution(
                value,
                target,
                safe.is_file(),
                safe.relative_to(self.root).as_posix() if safe.is_file() else None,
            )
        expected_slug = slugify(target)
        matches = []
        for path in self.iter_pages():
            if path.stem.casefold() == expected_slug.casefold():
                matches.append(path)
                continue
            try:
                if self.read(path).metadata.title.casefold() == target.casefold():
                    matches.append(path)
            except ValueError:
                continue
        unique = sorted(set(matches))
        return LinkResolution(
            value,
            target,
            len(unique) == 1,
            unique[0].relative_to(self.root).as_posix() if len(unique) == 1 else None,
            ambiguous=len(unique) > 1,
        )

    def _resolve_markdown_link(self, source: Path, value: str) -> LinkResolution:
        target = unquote(value.strip().strip("<>").split("#", 1)[0])
        parsed = urlparse(target)
        if parsed.scheme in {"http", "https"} or target.startswith("//"):
            return LinkResolution(value, target, True, external=True)
        if parsed.scheme:
            return LinkResolution(value, target, False)
        if not target:
            return LinkResolution(value, target, True, source.relative_to(self.root).as_posix())
        try:
            safe = self._confined(source.parent / target)
            self._managed_page_type(safe)
        except ValueError:
            return LinkResolution(value, target, False)
        return LinkResolution(
            value,
            target,
            safe.is_file(),
            safe.relative_to(self.root).as_posix() if safe.is_file() else None,
        )

    def validate_links(self) -> list[dict[str, Any]]:
        issues = []
        for page in self.iter_pages():
            for link in self.resolve_links(page):
                if not link.exists or link.ambiguous:
                    issues.append(
                        {
                            "page": page.relative_to(self.root).as_posix(),
                            "target": link.target,
                            "issue": "ambiguous" if link.ambiguous else "broken",
                        }
                    )
        return issues
