# Architecture and extension guide

## Current implementation

```text
CLI / compatibility scripts
  -> Settings + typed Source records
  -> manifest parser / read-only corpus audit
  -> CorpusDownloader -> injected HTTP session -> immutable archive + event journal
  -> NomicEmbeddingService -> lazy SentenceTransformer
  -> OllamaChatService -> lazy LangChain ChatOllama
```

| Module | Responsibility |
|---|---|
| `src/llm_wiki/config.py` | Load and validate configuration explicitly; no module-level environment mutation |
| `src/llm_wiki/corpus.py` | Typed source records, six-column manifest validation, format detection, archive audit |
| `src/llm_wiki/downloader.py` | HTTP policy, streaming limits, immutable file publication, single-writer lock, provenance |
| `src/llm_wiki/ports.py` | Provider contracts for embedding and text completion |
| `src/llm_wiki/embeddings.py` | Nomic loading, document/query prefixes, output validation |
| `src/llm_wiki/llm.py` | LangChain/Ollama integration and response validation |
| `src/llm_wiki/cli.py` | Construct dependencies, handle user input, render results and exit codes |
| `tests/test_foundations.py` | Deterministic tests for boundary failures and data preservation |

Keep the package small until features need additional boundaries. There are no empty repository classes, pretend graph implementations, or database tables in this foundation.

## Boundaries for subsequent work

Introduce `domain/` when adding wiki pages, source versions, citations, claims, and project IDs. These records should not import LangChain, Oracle, or filesystem code. Validate LLM output against typed schemas before permitting writes. Insurance claims should carry source reference, jurisdiction, effective period, and policy/product context so differences are not automatically labeled contradictions.

Introduce `storage/markdown.py` for page serialization and path handling. Keep original source bytes immutable and derived normalized text separate. Require paths to remain inside their project directory, including resolved symlink targets. Write pages atomically, preserve creation dates, and version page schemas. Implement link resolution and round-trip tests before giving agents write access.

Introduce application services that receive repositories and providers through constructors. Put LangGraph nodes in `workflows/`; each node calls one application operation and returns typed state. Build graphs explicitly at startup. Save checkpoints and operation IDs so retries can resume rather than create duplicate pages. Keep prompts as versioned resources, with source text clearly delimited as data.

Introduce `storage/oracle.py` and ordered SQL migrations when page storage exists. Scope every lookup, update, and uniqueness constraint by project ID. Use bind parameters, managed connections, explicit commit/rollback, and migration tests. Store page content hashes and model revisions; use a durable indexing queue to recover from filesystem/database partial failure. Files remain the readable wiki; Oracle is the searchable projection.

The future UI should call application services, never issue Oracle SQL or construct model prompts itself. CLI and UI should share ingestion/query services. Query responses should carry structured citations so links can be validated before rendering.

## Change checklist

1. Record the affected goal and acceptance evidence in `manifest.md`.
2. Add behavior to the owning module; create a new interface only when a service needs it.
3. Make resource acquisition explicit and release files, sessions, and connections deterministically.
4. Test meaningful failure cases: invalid model JSON, interrupted writes, retries, and project isolation.
5. Run offline checks. Run integration checks when changing an actual external boundary.
6. Update commands and configuration examples when behavior changes.

This is a maintainable foundation, not a production deployment. Outstanding release work includes tested integration locks, model revision pinning, migration/restore checks, workflow recovery, observability, evaluation, and concurrency beyond a single archive writer. Public URL ingestion would also need a deliberate network access policy; the current downloader is for locally curated manifests.
