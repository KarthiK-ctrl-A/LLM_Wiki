"""Convert immutable PDF/HTML sources to reviewable markdown with provenance."""

import hashlib
import json
import logging
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from llm_wiki.corpus import Source, detect_extension, source_files
from llm_wiki.downloader import corpus_lock

logger = logging.getLogger(__name__)
EXTRACTOR_VERSION = "2"


def is_accepted(decision: dict, record: dict) -> bool:
    return (
        decision.get("decision") == "accept"
        and decision.get("sha256") == record["raw_sha256"]
        and decision.get("normalized_sha256") == record["normalized_sha256"]
        and bool(decision.get("note"))
        and record["word_count"] >= 100
        and "Possible error or bot-challenge page" not in record["warnings"]
    )


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, suffix=".part", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def extract_pdf(path: Path) -> tuple[list[dict], list[str]]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("Encrypted PDF requires a password")
    sections = []
    warnings = []
    for page_number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        sections.append({"locator": f"PDF page {page_number}", "text": text})
        if len(text.split()) < 10:
            warnings.append(f"PDF page {page_number}: sparse text; check for images or OCR needs")
    return sections, warnings


def extract_html(path: Path, selector: str | None = None) -> tuple[list[dict], list[str]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for tag in soup.select(
        "script, style, noscript, nav, header, footer, input, button, select, aside, svg"
    ):
        tag.decompose()
    if selector:
        main = soup.select_one(selector)
        if main is None:
            raise ValueError(f"Reviewed HTML selector no longer matches: {selector}")
    else:
        main = soup.select_one("main, [role='main'], article") or soup.body or soup
    sections = []
    heading = title or "Document"
    paragraphs = []
    for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "table", "dt", "dd"]):
        # Parent tables/list items already include descendants; avoid duplicated text.
        if any(
            parent.name in {"table", "li", "dd"} for parent in tag.parents if parent is not main
        ):
            continue
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if not text:
            continue
        if tag.name.startswith("h") or tag.name == "dt":
            if paragraphs:
                sections.append({"locator": heading, "text": "\n\n".join(paragraphs)})
                paragraphs = []
            heading = text
        else:
            paragraphs.append(text)
    if paragraphs:
        sections.append({"locator": heading, "text": "\n\n".join(paragraphs)})
    if not sections:
        sections = [{"locator": heading, "text": main.get_text(" ", strip=True)}]
    warnings = []
    combined = (title + " " + " ".join(s["text"] for s in sections)).lower()
    if any(
        s in combined[:1500]
        for s in (
            "access denied",
            "request blocked",
            "verify you are human",
            "page not found",
            "enable javascript and cookies",
            "403 forbidden",
        )
    ):
        warnings.append("Possible error or bot-challenge page")
    return sections, warnings


def normalize_corpus(sources: list[Source], root: Path, output: Path, review_file: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("Normalized output and raw archive must be separate directories")
    review = json.loads(review_file.read_text(encoding="utf-8"))
    decisions = review.get("sources", {})
    unknown = set(decisions) - {str(s.source_number) for s in sources}
    if unknown:
        raise ValueError(f"Review contains unknown source IDs: {sorted(unknown)}")
    records = []
    now = datetime.now(timezone.utc).isoformat()
    dependencies = {name: version(name) for name in ("pypdf", "beautifulsoup4", "fonttools")}
    retrievals = {}
    journal = root / "_metadata/download_events.jsonl"
    if journal.exists():
        for line in journal.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("status") == "downloaded":
                retrievals[event["local_path"]] = event["recorded_at"]
    with corpus_lock(output):
        previous_file = output / "corpus.json"
        previous = (
            json.loads(previous_file.read_text(encoding="utf-8")) if previous_file.exists() else {}
        )
        cached = {
            r["source_number"]: r
            for r in previous.get("sources", [])
            if previous.get("dependencies") == dependencies
        }
        for source in sources:
            decision = decisions.get(str(source.source_number), {})
            record = {
                "source_number": source.source_number,
                "title": source.title,
                "publisher": source.publisher,
                "url": source.url,
                "jurisdiction": decision.get("jurisdiction"),
                "effective_date": decision.get("effective_date"),
                "retrieved_at": None,  # Historical downloads did not record retrieval timestamps.
                "normalized_at": now,
                "extractor_version": EXTRACTOR_VERSION,
                "review_note": decision.get("note"),
                "warnings": [],
                "html_selector": decision.get("html_selector"),
                "landing_url": decision.get("landing_url"),
            }
            if decision.get("decision") == "exclude":
                if not decision.get("note"):
                    raise ValueError(f"Excluded source {source.source_number} requires a reason")
                records.append({**record, "status": "excluded"})
                continue
            files = source_files(root, source)
            selected = decision.get("raw_path")
            if selected:
                files = [p for p in files if p.relative_to(root).as_posix() == selected]
            if len(files) != 1:
                records.append(
                    {
                        **record,
                        "status": "needs_review",
                        "warnings": [
                            "Missing source"
                            if not files
                            else "Select one raw_path from multiple versions"
                        ],
                    }
                )
                continue
            path = files[0].resolve()
            if not path.is_relative_to(root):
                raise ValueError("Source path escapes the raw archive")
            record["raw_path"] = path.relative_to(root).as_posix()
            record["retrieved_at"] = retrievals.get(record["raw_path"])
            with path.open("rb") as stream:
                record["raw_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                stream.seek(0)
                prefix = stream.read(4096)
            old = cached.get(source.source_number, {})
            cached_path = (output / old.get("normalized_path", "missing")).resolve()
            if (
                old.get("raw_sha256") == record["raw_sha256"]
                and all(old.get(key) == record[key] for key in ("title", "publisher", "url"))
                and old.get("extractor_version") == EXTRACTOR_VERSION
                and old.get("html_selector") == record["html_selector"]
                and cached_path.is_relative_to(output)
                and cached_path.is_file()
                and hashlib.sha256(cached_path.read_bytes()).hexdigest()
                == old.get("normalized_sha256")
            ):
                for key in (
                    "normalized_path",
                    "normalized_sha256",
                    "word_count",
                    "section_count",
                    "detected_format",
                    "warnings",
                    "locators",
                ):
                    record[key] = old[key]
                record["status"] = "accepted" if is_accepted(decision, record) else "needs_review"
                records.append(record)
                continue
            try:
                logger.info("Extracting source %s: %s", source.source_number, source.title)
                detected = detect_extension(prefix)
                sections, warnings = (
                    extract_pdf(path)
                    if detected == ".pdf"
                    else extract_html(path, record["html_selector"])
                )
                if detected != path.suffix.lower():
                    warnings.append("Legacy extension mismatch; parsed by actual content signature")
                text = "\n\n".join(section["text"] for section in sections)
                words = len(text.split())
                if words < 100:
                    warnings.append("Fewer than 100 extracted words")
                if text.count("\ufffd") > max(5, len(text) // 1000):
                    warnings.append("High replacement-character count; inspect encoding")
                identity = hashlib.sha256(
                    json.dumps(
                        {
                            "raw": record["raw_sha256"],
                            "extractor": EXTRACTOR_VERSION,
                            "dependencies": dependencies,
                            "html_selector": record["html_selector"],
                            "title": source.title, "publisher": source.publisher, "url": source.url,
                        },
                        sort_keys=True,
                    ).encode()
                ).hexdigest()[:16]
                target = Path(f"{source.source_number:03d}-{identity}.md")
                markdown = (
                    f"# {source.title}\n\nSource: {source.url}\n\n"
                    f"Publisher: {source.publisher}\n\nRaw SHA-256: {record['raw_sha256']}\n\n"
                    "This is extracted source text, not an LLM summary.\n\n"
                    + "\n\n".join(f"## {s['locator']}\n\n{s['text']}" for s in sections)
                    + "\n"
                )
                atomic_text(output / target, markdown)
                record.update(
                    {
                        "detected_format": detected[1:],
                        "warnings": warnings,
                        "word_count": words,
                        "section_count": len(sections),
                        "normalized_path": target.as_posix(),
                        "normalized_sha256": hashlib.sha256(markdown.encode()).hexdigest(),
                        "locators": [s["locator"] for s in sections],
                    }
                )
                record["status"] = "accepted" if is_accepted(decision, record) else "needs_review"
            except Exception as exc:
                logger.warning("Extraction failed for source %s: %s", source.source_number, exc)
                record.update({"status": "failed", "warnings": [str(exc)]})
            records.append(record)
        counts = dict(Counter(r["status"] for r in records))
        report = {
            "schema_version": 1,
            "generated_at": now,
            "dependencies": dependencies,
            "counts": counts,
            "accepted_count": counts.get("accepted", 0),
            "ready": 50 <= counts.get("accepted", 0) <= 100
            and not any(r["status"] in {"failed", "needs_review"} for r in records),
            "sources": records,
        }
        atomic_text(output / "corpus.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report
