"""Validated wiki page and project records."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Literal
from uuid import UUID

PageType = Literal["entity", "concept", "summary", "overview"]
LinkStyle = Literal["wikilink", "markdown"]
PAGE_TYPES = ("entity", "concept", "summary", "overview")
LINK_STYLES = ("wikilink", "markdown")
CORE_FRONTMATTER_FIELDS = (
    "title",
    "type",
    "date_created",
    "date_updated",
    "tags",
    "sources",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug or len(slug) > 80:
        raise ValueError("A slug must contain 1-80 ASCII letters, numbers, or separators")
    return slug


def validate_field_name(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", value):
        raise ValueError(f"Invalid frontmatter field name: {value!r}")
    if value in CORE_FRONTMATTER_FIELDS:
        raise ValueError(f"Extra field duplicates a core field: {value}")
    return value


def validate_timestamp(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return value


@dataclass(frozen=True)
class ProjectConfig:
    project_id: str
    name: str
    slug: str
    created_at: str
    link_style: LinkStyle
    page_directories: dict[str, str]
    extra_frontmatter_fields: tuple[str, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Project name must not be blank")
        try:
            UUID(self.project_id)
        except (ValueError, TypeError) as exc:
            raise ValueError("project_id must be a UUID") from exc
        if slugify(self.slug) != self.slug:
            raise ValueError("Project slug must already be normalized")
        validate_timestamp(self.created_at, "created_at")
        if self.link_style not in LINK_STYLES:
            raise ValueError(f"Unsupported link style: {self.link_style}")
        if set(self.page_directories) != set(PAGE_TYPES):
            raise ValueError(f"Page directory keys must be exactly: {', '.join(PAGE_TYPES)}")
        for directory in self.page_directories.values():
            path = PurePosixPath(directory)
            if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
                raise ValueError(f"Page directory must be one safe relative segment: {directory}")
        if len(set(self.page_directories.values())) != len(self.page_directories):
            raise ValueError("Each page type must use a distinct directory")
        extras = tuple(validate_field_name(value) for value in self.extra_frontmatter_fields)
        if len(set(extras)) != len(extras):
            raise ValueError("Extra frontmatter fields must be unique")
        if self.schema_version != 1:
            raise ValueError(f"Unsupported project schema version: {self.schema_version}")

    @property
    def directories(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.page_directories.values(), "raw")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "name": self.name,
            "slug": self.slug,
            "created_at": self.created_at,
            "link_style": self.link_style,
            "page_directories": self.page_directories,
            "extra_frontmatter_fields": list(self.extra_frontmatter_fields),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        try:
            return cls(
                schema_version=data["schema_version"],
                project_id=data["project_id"],
                name=data["name"],
                slug=data["slug"],
                created_at=data["created_at"],
                link_style=data["link_style"],
                page_directories=dict(data["page_directories"]),
                extra_frontmatter_fields=tuple(data.get("extra_frontmatter_fields", [])),
            )
        except (KeyError, TypeError) as exc:
            raise ValueError("Invalid project metadata") from exc


@dataclass(frozen=True)
class PageMetadata:
    title: str
    type: PageType
    date_created: str
    date_updated: str
    tags: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self, required_extra_fields: tuple[str, ...] = ()) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Page title must not be blank")
        if self.type not in PAGE_TYPES:
            raise ValueError(f"Unsupported page type: {self.type}")
        validate_timestamp(self.date_created, "date_created")
        validate_timestamp(self.date_updated, "date_updated")
        if datetime.fromisoformat(
            self.date_updated.replace("Z", "+00:00")
        ) < datetime.fromisoformat(self.date_created.replace("Z", "+00:00")):
            raise ValueError("date_updated must not be before date_created")
        for name, values in (("tags", self.tags), ("sources", self.sources)):
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"{name} must contain nonblank strings")
        unknown = set(self.extra) - set(required_extra_fields)
        missing = set(required_extra_fields) - set(self.extra)
        if unknown or missing:
            raise ValueError(
                f"Extra frontmatter fields differ from schema; missing={sorted(missing)}, "
                f"unknown={sorted(unknown)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "type": self.type,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "tags": list(self.tags),
            "sources": list(self.sources),
            **self.extra,
        }


@dataclass(frozen=True)
class WikiPage:
    metadata: PageMetadata
    body: str


@dataclass(frozen=True)
class LinkResolution:
    original: str
    target: str
    exists: bool
    resolved_path: str | None = None
    external: bool = False
    ambiguous: bool = False
