"""Explicit configuration loading; process environment overrides the selected .env."""

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    corpus_manifest: Path
    corpus_dir: Path
    domain: str = "property_casualty_insurance"
    http_timeout: float = 60
    download_delay: float = 1
    max_download_bytes: int = 104857600
    embedding_model: str = "nomic-ai/nomic-embed-text-v2-moe"
    embedding_dimension: int = 768
    embedding_revision: str | None = None
    embedding_code_revision: str | None = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:latest"
    llm_timeout: float = 300
    oracle_dsn: str = "localhost:1521/FREEPDB1"
    oracle_user: str = "WIKI_APP"
    oracle_password: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        for name in ("http_timeout", "llm_timeout", "download_delay"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0 or (name != "download_delay" and value == 0):
                raise ValueError(f"Invalid {name}: must be finite and within the allowed range")
        if self.max_download_bytes <= 0 or self.embedding_dimension <= 0:
            raise ValueError("Download limit and embedding dimension must be positive")
        if not all(x.strip() for x in (self.domain, self.embedding_model, self.ollama_model)):
            raise ValueError("Domain and model names must not be blank")
        url = urlparse(self.ollama_url)
        if url.scheme not in {"http", "https"} or not url.hostname:
            raise ValueError("WIKI_OLLAMA_URL must be an HTTP(S) URL")

    @classmethod
    def load(
        cls, env_file: Path = Path(".env"), environ: Mapping[str, str] | None = None
    ) -> "Settings":
        from dotenv import dotenv_values

        env_file = env_file.resolve()
        values = {
            k: v for k, v in dotenv_values(env_file, interpolate=False).items() if v is not None
        }
        values.update(os.environ if environ is None else environ)

        def path(key: str, default: str) -> Path:
            return (env_file.parent / Path(values.get(key, default))).resolve()

        return cls(
            corpus_manifest=path(
                "WIKI_CORPUS_MANIFEST",
                "llm_wiki_data/property_casualty_insurance_corpus_manifest.md",
            ),
            corpus_dir=path(
                "WIKI_CORPUS_DIR", "llm_wiki_data/llm_wiki/data/sources/property_casualty_insurance"
            ),
            domain=values.get("WIKI_DOMAIN", "property_casualty_insurance"),
            http_timeout=float(values.get("WIKI_HTTP_TIMEOUT", "60")),
            download_delay=float(values.get("WIKI_DOWNLOAD_DELAY", "1")),
            max_download_bytes=int(values.get("WIKI_MAX_DOWNLOAD_BYTES", "104857600")),
            embedding_model=values.get("WIKI_EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v2-moe"),
            embedding_dimension=int(values.get("WIKI_EMBEDDING_DIMENSION", "768")),
            embedding_revision=values.get("WIKI_EMBEDDING_REVISION") or None,
            embedding_code_revision=values.get("WIKI_EMBEDDING_CODE_REVISION") or None,
            ollama_url=values.get("WIKI_OLLAMA_URL", "http://localhost:11434"),
            ollama_model=values.get("WIKI_OLLAMA_MODEL", "gemma4:latest"),
            llm_timeout=float(values.get("WIKI_LLM_TIMEOUT", "300")),
            oracle_dsn=values.get("ORACLE_DSN", "localhost:1521/FREEPDB1"),
            oracle_user=values.get("ORACLE_USER", "WIKI_APP"),
            oracle_password=values.get("ORACLE_PASSWORD", ""),
        )
