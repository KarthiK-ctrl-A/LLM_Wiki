# P&C Insurance LLM Wiki

A Python foundation for a persistent, source-grounded knowledge wiki about property and casualty insurance. Current capabilities are source collection, corpus auditing, and reusable embedding/chat adapters. Wiki generation and question answering are planned, not implemented. See [manifest.md](manifest.md) for the audited status and delivery sequence.

## Setup

Use Python 3.11 or newer from the repository root. The legacy `genai/` environment points to a missing Python 3.10 executable; it is preserved but should not be used.

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.venv/Scripts/python.exe -m llm_wiki --help
```

Copy `.env.example` only when you do not already have a `.env`. Process environment variables override the selected file. Relative configuration paths resolve against the `.env` directory. Explicit CLI paths resolve against the working directory. To run from another directory, supply an absolute `--env-file` path. The base installation does not install or download model runtimes.

Install only the optional integrations you need:

```powershell
.venv/Scripts/python.exe -m pip install -e ".[embeddings]"
.venv/Scripts/python.exe -m pip install -e ".[agents]"
# Future Oracle adapter dependency; no Oracle repository exists yet:
.venv/Scripts/python.exe -m pip install -e ".[oracle]"
```

`pip install -r requirements.txt` installs all integration extras. Dependency ranges are declared once in `pyproject.toml`; a fully resolved, integration-tested deployment lock is still a release requirement.

## Commands available now

```powershell
# Read-only: reports JSON and returns 1 when the corpus has issues.
.venv/Scripts/python.exe -m llm_wiki audit-corpus

# Explicit network operation: download missing sources, skip valid existing files.
.venv/Scripts/python.exe -m llm_wiki download

# Refetch sources; changed responses become additional immutable versions.
.venv/Scripts/python.exe -m llm_wiki download --refresh

# Use another six-column manifest and archive directory.
.venv/Scripts/python.exe -m llm_wiki download --manifest ./sources.md --output ./data/archive

# Explicit live checks, after installing the relevant extras and model.
.venv/Scripts/python.exe -m llm_wiki smoke embeddings
.venv/Scripts/python.exe -m llm_wiki smoke llm
```

The installed `llm-wiki` executable provides the same commands. Exit codes: `0` success, `1` corpus issues or individual download failures, `2` configuration/provider/unexpected command errors. Legacy scripts (`embedding_consumer.py`, `test_nomic.py`, `test_ollama.py`, and `llm_wiki_data/downlaod_data.py`) now delegate to the same CLI. The `embedding_service.NomicEmbeddingService` import remains available from the repository root. Legacy downloader helper functions are replaced by the typed API below; the old script remains an executable entry point.

For Ollama, install/start Ollama separately and pull the model named in `WIKI_OLLAMA_MODEL`; the default is `qwen2.5:7b`, matching the previous installation notes. Change this setting to use another installed model. For Nomic, the first embedding call downloads model weights and custom model code unless cached. Pin `WIKI_EMBEDDING_REVISION` to a reviewed commit for repeatable deployments.

The [Nomic model card](https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe) specifies 768-dimensional output, task prefixes, and a 512-token input limit. This adapter checks vector dimensions, finite values, and normalization; it does not yet implement long-document chunking. Do not embed full manuals and assume all text was represented. Chat access uses the official [LangChain Ollama integration](https://docs.langchain.com/oss/python/integrations/chat/ollama).

## Reusing the library

```python
from pathlib import Path
from llm_wiki.config import Settings
from llm_wiki.corpus import audit_corpus, parse_manifest

settings = Settings.load(Path(".env"))
sources = parse_manifest(settings.corpus_manifest.read_text(encoding="utf-8"))
report = audit_corpus(sources, settings.corpus_dir)
```

`NomicEmbeddingService` accepts an injected encoder; `OllamaChatService` accepts an injected chat client; `CorpusDownloader` accepts an injected HTTP session. Future services should depend on `EmbeddingProvider` and `ChatProvider` from `ports.py`. Provider failures propagate to callers; the CLI converts them into a nonzero exit status.

## Archive behavior

The original corpus, metadata, datasets, and notebook are retained in their existing locations. New downloads use SHA-256-addressed versions, write to temporary files before publishing, and record checksums and relative paths in `_metadata/download_events.jsonl`. Existing `_metadata/metadata.jsonl` is historical evidence and is never truncated. A normal rerun skips a source with a file that passes the format check; use `--refresh` to request updated remote content. New versions are retained together; selecting the active version is a future ingestion responsibility.

Only one downloader may write an archive at a time. A `.download.lock` prevents overlapping runs. After a crashed process, verify that no writer is running before removing a stale lock. Journal writes are flushed per source, but source publication and journal append are not one transaction; a rerun can recover a published file by recording it as skipped.

The audit checks presence and file signatures. It does not establish readability, licensing, factual quality, or whether an HTML page is an access-denied page. Downloading a landing page does not follow its embedded PDF links. These quality checks belong to the next corpus-normalization milestone.

## Validation

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/python.exe -m pip check
```

The tests use temporary archives and injected providers, with no model downloads, database, or external network. A GitHub Actions workflow runs the offline checks when this directory is placed in a GitHub repository. No Git repository was present during this refactor.

Oracle setup is intentionally separate: [sqls/db_queries.sql](sqls/db_queries.sql) is a manual development-user bootstrap, not the application schema. Put runtime credentials in environment configuration. The refactor removes the old example password from setup files without changing any live database account.

See [docs/architecture.md](docs/architecture.md) for module boundaries and rules for the next implementation.
