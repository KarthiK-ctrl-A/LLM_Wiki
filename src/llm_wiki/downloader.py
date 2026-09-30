"""Bounded HTTP downloads, immutable source versions, and append-only provenance.

One writer per output directory. Existing legacy source files are never rewritten.
"""

import hashlib
import json
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from llm_wiki.config import Settings
from llm_wiki.corpus import Source, detect_extension, source_files

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "pc-llm-wiki/0.1 corpus-downloader"})
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


@contextmanager
def corpus_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".download.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError(
            f"Corpus is locked: {lock}. If a download crashed, verify no writer is running "
            "before removing this lock."
        ) from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


class CorpusDownloader:
    def __init__(self, settings: Settings, session: requests.Session):
        self.settings = settings
        self.session = session

    def download(self, source: Source, *, refresh: bool = False) -> dict:
        """Caller must hold corpus_lock when invoking this method directly."""
        root = self.settings.corpus_dir
        if not refresh:
            for path in source_files(root, source):
                with path.open("rb") as stream:
                    prefix = stream.read(4096)
                try:
                    if detect_extension(prefix) == path.suffix.lower():
                        return self._record(path, "skipped", None, None)
                except ValueError:
                    continue
        folder = root / source.folder
        folder.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with self.session.get(
                source.url,
                timeout=self.settings.http_timeout,
                stream=True,
                allow_redirects=True,
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                digest = hashlib.sha256()
                size = 0
                prefix = b""
                with tempfile.NamedTemporaryFile(dir=folder, suffix=".part", delete=False) as out:
                    temporary = Path(out.name)
                    for chunk in response.iter_content(chunk_size=65536):
                        if not chunk:
                            continue
                        size += len(chunk)
                        if size > self.settings.max_download_bytes:
                            raise ValueError("Download exceeds configured byte limit")
                        prefix = (prefix + chunk)[:4096]
                        digest.update(chunk)
                        out.write(chunk)
                    out.flush()
                    os.fsync(out.fileno())
                extension = detect_extension(prefix, content_type)
                # Keep paths short on Windows; verify the full hash before reusing a name.
                path = folder / f"{source.filename_stem}_{digest.hexdigest()[:16]}{extension}"
                if path.exists():
                    if self._checksum(path) != digest.hexdigest():
                        raise ValueError(
                            "Existing content-addressed file failed checksum validation"
                        )
                else:
                    os.replace(temporary, path)
                return self._record(path, "downloaded", content_type, response.url)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _checksum(path: Path) -> str:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    def _record(self, path: Path, status: str, content_type: str | None, url: str | None) -> dict:
        return {
            "status": status,
            "local_path": path.relative_to(self.settings.corpus_dir).as_posix(),
            "content_type": content_type,
            "final_url": url,
            "file_size_bytes": path.stat().st_size,
            "sha256": self._checksum(path),
            "error": None,
        }

    def run(self, sources: list[Source], *, refresh: bool = False) -> dict[str, int]:
        counts = {"downloaded": 0, "skipped": 0, "failed": 0}
        root = self.settings.corpus_dir
        with corpus_lock(root):
            metadata = root / "_metadata"
            metadata.mkdir(exist_ok=True)
            # Separate versioned event schema preserves the original metadata.jsonl.
            with (metadata / "download_events.jsonl").open("a", encoding="utf-8") as journal:
                for source in sources:
                    try:
                        result = self.download(source, refresh=refresh)
                    except (requests.RequestException, OSError, ValueError) as exc:
                        logger.warning(
                            "Download failed for source %s: %s", source.source_number, exc
                        )
                        result = {"status": "failed", "error": str(exc), "local_path": None}
                    event = {
                        **asdict(source),
                        **result,
                        "schema_version": 1,
                        "domain": self.settings.domain,
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    }
                    journal.write(json.dumps(event, ensure_ascii=False) + "\n")
                    journal.flush()
                    os.fsync(journal.fileno())
                    counts[result["status"]] += 1
                    if result["status"] != "skipped":
                        time.sleep(self.settings.download_delay)
        return counts
