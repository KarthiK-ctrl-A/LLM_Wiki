"""Pure manifest parsing and a read-only audit of the existing source corpus."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

FOLDER_MAP = {
    "NAIC": "naic",
    "FEMA": "fema_nfip",
    "FloodSmart / FEMA": "fema_nfip",
    "Triple-I": "triple_i",
    "Triple-I / ISO sample": "triple_i",
    "California Department of Insurance": "regulators",
    "North Carolina Department of Insurance": "regulators",
    "Reinsurance Association of America": "reinsurance",
    "Investopedia": "reinsurance",
}


@dataclass(frozen=True)
class Source:
    source_number: int
    title: str
    publisher: str
    source_type: str
    description: str
    url: str

    @property
    def folder(self) -> str:
        return FOLDER_MAP.get(self.publisher, "other")

    @property
    def filename_stem(self) -> str:
        title = re.sub(r"[^a-z0-9]+", "_", self.title.lower()).strip("_")[:90].strip("_")
        # Keep legacy URL IDs for stable matching; this is not a security digest.
        suffix = hashlib.md5(self.url.encode(), usedforsecurity=False).hexdigest()[:10]
        return f"{self.source_number:02d}_{title}_{suffix}"


def parse_manifest(markdown: str) -> list[Source]:
    sources = []
    seen_numbers: set[int] = set()
    seen_urls: set[str] = set()
    for number, line in enumerate(markdown.splitlines(), 1):
        columns = [part.strip() for part in line.strip().strip("|").split("|")]
        if not line.strip().startswith("|") or not columns[0].isdigit():
            continue
        if len(columns) != 6:
            raise ValueError(f"Manifest line {number}: expected six columns")
        source = Source(int(columns[0]), *columns[1:])
        url = urlparse(source.url)
        if url.scheme not in {"http", "https"} or not url.hostname:
            raise ValueError(f"Manifest line {number}: invalid HTTP(S) URL")
        if not source.title or source.source_number <= 0:
            raise ValueError(f"Manifest line {number}: invalid source title or number")
        if source.source_number in seen_numbers or source.url in seen_urls:
            raise ValueError(f"Manifest line {number}: duplicate source number or URL")
        seen_numbers.add(source.source_number)
        seen_urls.add(source.url)
        sources.append(source)
    if not sources:
        raise ValueError("Manifest contains no source rows")
    return sources


def detect_extension(prefix: bytes, content_type: str = "") -> str:
    """Inspect response bytes; a landing page mentioning PDF is still HTML."""
    sample = prefix.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if sample.startswith(b"%pdf-"):
        return ".pdf"
    if b"<html" in sample or sample.startswith((b"<!doctype html", b"<?xml")):
        return ".html"
    if "text/html" in content_type.lower() and "application/pdf" not in content_type.lower():
        return ".html"
    raise ValueError("Response is neither a PDF nor an HTML document")


def source_files(root: Path, source: Source) -> list[Path]:
    folder = root / source.folder
    # Include immutable content-addressed versions produced by the new downloader.
    return sorted(
        p
        for p in folder.glob(source.filename_stem + "*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".html"}
    )


def audit_corpus(sources: list[Source], root: Path) -> dict:
    """Validate file presence and signatures without changing any source bytes."""
    issues = []
    counts: dict[str, int] = {".pdf": 0, ".html": 0}
    present = 0
    for source in sources:
        files = source_files(root, source)
        if not files:
            issues.append({"source_number": source.source_number, "issue": "missing"})
            continue
        present += 1
        for path in files:
            counts[path.suffix.lower()] += 1
            with path.open("rb") as stream:
                prefix = stream.read(4096)
            try:
                actual = detect_extension(prefix)
                if actual != path.suffix.lower():
                    issues.append(
                        {
                            "source_number": source.source_number,
                            "issue": "extension_mismatch",
                            "path": path.relative_to(root).as_posix(),
                            "detected_extension": actual,
                        }
                    )
            except ValueError:
                issues.append(
                    {
                        "source_number": source.source_number,
                        "issue": "unknown_format",
                        "path": path.relative_to(root).as_posix(),
                    }
                )
    return {"sources": len(sources), "present": present, "file_counts": counts, "issues": issues}
