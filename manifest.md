# Project manifest: Property & Casualty Insurance LLM Wiki

Audit date: **2026-09-29**. Scope: the files under this project directory, the supplied statement, and the [linked challenge](https://codingchallenges.substack.com/p/coding-challenge-122-database-driven). The URL says `122`; the page heading currently says challenge **123**. This roadmap identifies requirements by step rather than challenge number.

## Goal and current position

Build a P&C insurance knowledge base that accumulates source-grounded, interconnected markdown knowledge, then uses Oracle retrieval and LangGraph/LangChain workflows to answer questions with traceable evidence. Initial subject areas: homeowners, auto liability, flood/NFIP, cyber, reinsurance, underwriting, and claims.

**The original code reaches part of Step Zero only. No challenge step is fully verified end to end.** This refactor establishes a tested engineering foundation; it does not turn source downloading into wiki ingestion or count a model experiment as a working search system.

Status meanings: **Complete** = implementation and stated acceptance evidence exist; **Partial** = some deliverables exist but the exit criteria are unmet; **Not started** = no implementation found; **Unverified** = requires runtime evidence not obtained in this audit. Checkboxes track deliverables, not percentages.

## Evidence from the original code

| Area | Evidence | Assessment |
|---|---|---|
| Domain selection | `llm_wiki_data/property_casualty_insurance_corpus_manifest.md` | P&C insurance chosen; 63 curated entries |
| Collected sources | Existing archive and `_metadata/metadata.jsonl` | 59 downloaded, four failed with recorded HTTP 403; no normalized text corpus |
| File validity | Byte-signature audit | 42 `.pdf` filenames and 17 `.html`; three of the PDFs contain HTML, leaving 39 PDF signatures and 20 HTML signatures |
| Embeddings | Original `embedding_service.py`, `embedding_consumer.py`, `test_nomic.py` | Nomic prefixes and normalized vectors prototyped; no persistent page index |
| LLM | Original `test_ollama.py` | Direct Ollama experiment; configured model differed from setup notes |
| Oracle | `sqls/db_queries.sql`, previous installation notes | User/bootstrap instructions only; no page tables, migrations, or Oracle adapter |
| Orchestration | Original `requirements.txt` | Dependencies listed; no LangGraph nodes or compiled workflows |
| Notebook/datasets | `test.ipynb`, `datasets/*.csv` | Notebook has two markdown cells, no executable pipeline; CSV datasets are unused |
| Environment | `genai/pyvenv.cfg` | References unavailable Python 3.10 installation; a separate Python 3.11 `.venv` now validates the refactor |

Corpus exceptions: missing source IDs **22, 23, 27, 28**; HTML saved under PDF names for IDs **25, 40, 41**. See the saved [corpus audit](docs/corpus-audit.json). Originals and historical metadata are preserved. A format-valid download still needs content-quality review; the count alone does not establish a usable corpus.

## Phase map

| Phase | Challenge alignment | Original state | After this refactor | Depends on |
|---|---|---|---|---|
| F | Engineering foundation | Loose scripts | Complete for the bounded refactor; live providers unverified | — |
| 0 | Environment and corpus | Partial | Partial | F |
| 1 | Wiki directories, schema, frontmatter, links, management CLI | Not started | Not started | 0 |
| 2 | Agent ingestion and knowledge integration | Not started | Not started | 1 |
| 3 | Navigable index and chronological operation log | Not started | Not started | 2 |
| 4 | Oracle page metadata, vector and full-text search | Not started | Not started | 1–3 |
| 5 | Cited answers, follow-ups, optional answer filing | Not started | Not started | 4 |
| 6 | Persistent, isolated wiki projects | Not started | Not started | 4–5 |
| 7 | Interactive wiki health checks and accepted fixes | Not started | Not started | 2–6 |
| 8 | Chat interface, page browsing, standalone ingestion command | Not started | Not started | 5–7 |
| R | Operational release gate | Not started | Partial tooling only | All core phases |

## F — Refactor delivered

- [x] Installable `src/llm_wiki` package and `llm-wiki` CLI; old executable entry points delegate to it.
- [x] Environment-backed configuration, validation, explicit paths, optional integration extras.
- [x] Typed manifest entries and provider contracts; injectable HTTP/model clients.
- [x] Lazy model loading, finite normalized vector checks, timeout configuration, honest error exits.
- [x] Streaming downloads, transient HTTP retries, byte limits, immutable versions, writer lock, durable per-source event append.
- [x] Read-only corpus audit and regression coverage for mislabeling, interruption, failures, and preservation.
- [x] Remove example passwords from setup/SQL; add setup and architecture documentation, offline CI definition.

Evidence: `src/llm_wiki/`, `tests/test_foundations.py`, `README.md`, `docs/architecture.md`, `.github/workflows/ci.yml`. CI is defined but has not run remotely. This directory was not a Git checkout.

## 0 — Complete the development environment and usable corpus

- [x] Preserve the selected insurance domain and curated archive.
- [x] Install and validate the lightweight package in a fresh Python 3.11 environment.
- [ ] Install integration extras, select a model revision, and record actual Nomic and Ollama smoke results.
- [ ] Start/verify Oracle, connect using environment credentials, and prove create/read/drop of a disposable test table.
- [ ] Resolve or explicitly replace/exclude the four failed sources; distinguish landing pages from documents.
- [ ] Add PDF/HTML-to-text adapters with page/section provenance. Keep originals intact; store derived text separately with source checksum, extraction version, retrieval date, and quality status.
- [ ] Review 50–100 readable sources, with jurisdiction/effective-date metadata where available. Flag scanned or empty documents for OCR/manual attention.

**Exit evidence:** live provider results, DB probe, and a corpus report linking each accepted source to readable derived text. Do not call this phase complete based only on installed dependencies.

## 1 — Create the markdown storage boundary

Implement `domain/pages.py`, `storage/markdown.py`, and `services/projects.py`. Use a stable project identifier from the first page onward, even before the Oracle project registry exists. Define entity/concept/summary/overview records, YAML serialization, timestamps, tags, and source references. Add `create`, `list`, and `inspect` commands with per-project schema settings and link resolution.

- [ ] Create project directories and schema conventions.
- [ ] Round-trip page metadata and content; enforce safe project-relative paths and atomic writes.
- [ ] Validate links and independently configurable projects.

**Exit evidence:** temporary-directory tests for two differently configured projects, malformed frontmatter, path escape rejection, page updates, and listing after project removal.

## 2 — Deliver one complete ingestion flow

Build `workflows/ingest.py` around typed state and small application operations. Start with two reviewed insurance sources; inject the current provider interfaces. Extract structured claims before drafting pages. Merge by canonical entity identity and include policy context, dates, and jurisdiction in contradiction decisions. Treat source instructions as document data. Present proposed updates in interactive mode and preserve raw bytes.

- [ ] Read normalized source, extract validated claims/entities, generate source summary, merge knowledge pages, and record gaps.
- [ ] Preserve competing sourced claims; do not replace older evidence silently.
- [ ] Introduce ingestion IDs, staged changes, checkpoint/retry behavior, and explicit failure records.

**Exit evidence:** ingest the same source twice without duplicate pages; interrupt and resume; integrate a conflicting source while retaining both references; reject malformed model output without publishing it.

## 3 — Make changes discoverable and auditable

Add deterministic index generation from stored pages and an append-only operation journal. Wire both into ingestion completion/failure handling; make recent operations available to subsequent sessions. Keep this wiki log separate from the downloader's provenance journal.

- [ ] Maintain category links and concise descriptions in `index.md`.
- [ ] Record operations in `log.md` using `## [YYYY-MM-DD] type | Description`.
- [ ] Reconcile deleted pages without retaining stale index entries.

**Exit evidence:** two ingestions, a failed ingestion, and a manually removed page produce correct index/log state. Replaying an operation must not duplicate successful work.

## 4 — Add Oracle as the searchable projection

Create versioned migrations and a pooled Oracle repository with bind variables. Suggested records: `projects`, `source_versions`, `wiki_pages`, `page_embeddings`, `index_jobs`. Use `(project_id, page_path)` uniqueness; store content hashes, embedding model/revision, dimension, and indexing state. Design an outbox/reconciliation mechanism for markdown writes that precede a failed DB update.

- [ ] Persist page metadata and searchable content; exclude raw files and navigation files from embeddings.
- [ ] Add cosine vector and Oracle Text indexes plus type/tag filters.
- [ ] Combine lexical/vector rankings with a tested fusion strategy; scope every operation by project.
- [ ] Re-index only changed content or changed model versions; reconcile removed pages.
- [ ] Respect the embedding model's token limit through an evaluated page-summary/chunk strategy.

**Exit evidence:** real Oracle integration tests for semantic matches, exact insurance terms, filters, unchanged-page reuse, deletion reconciliation, and recovery after indexing failure.

## 5 — Query accumulated knowledge

Implement `workflows/query.py` using index context, hybrid retrieval, full-page reads, and grounded synthesis. Return structured citations referencing existing page sections. Introduce a retrieval budget, session IDs, and an explicit insufficient-evidence response. File a requested answer through the same page/index/log/embedding path used by ingestion.

- [ ] Cite supported answers and validate links before displaying them.
- [ ] Preserve follow-up context and choose useful response formats.
- [ ] Persist an answer only after the user chooses to save it.

**Exit evidence:** a reviewed P&C question set covers paraphrases, multi-page comparison, follow-ups, unanswerable questions, invalid citations, and saved-answer discoverability. Score grounding and retrieval separately.

## 6 — Prove project isolation and restart behavior

Finish the Oracle project registry and explicit project selection. Scope files, retrieval, workflow checkpoints, and chat history consistently. Derive counts from committed data and reconcile metadata after interrupted jobs.

- [ ] Persist project metadata and allow create/list/select.
- [ ] Keep results and session memory isolated across projects and restarts.

**Exit evidence:** two projects deliberately use identical page names and similar text; searches, retries, and restarted sessions never mix their data.

## 7 — Maintain knowledge quality

Build `workflows/lint.py` with deterministic structural checks first, then evidence-based semantic analysis. Findings should be typed records containing severity, affected paths, evidence, and proposed changes. Revalidate the current page version before applying an accepted fix.

- [ ] Report broken links, orphan/missing pages, conflicting/stale claims, and knowledge gaps.
- [ ] Support accept/reject/edit decisions; make automatic fixes an explicit option.

**Exit evidence:** seeded defects are reported with locations; rejecting suggestions leaves content hashes unchanged; accepted fixes update dependent indexes and embeddings.

## 8 — Expose the complete workflow

Choose CLI chat first to keep the delivery small; add a web client later if useful. Reuse application services for project selection, markdown responses, citation navigation, page browsing, saved answers, and visible progress. Keep source ingestion independently runnable.

- [ ] Implement `llm-wiki ingest <project> <source>` and interactive chat with the completed workflows.
- [ ] Validate page browsing, citation opening, follow-ups, and progress/error reporting.

**Exit evidence:** a fresh installation can ingest a source, ask a cited question, save an answer, restart, and retrieve it without notebooks or ad hoc scripts.

## R — Production readiness

- [x] Offline checks and CI definition exist.
- [ ] Resolve and lock all runtime integrations on supported platforms; pin model revisions and deployment images.
- [ ] Test migrations, backup/restore of files plus Oracle, durable retries, and concurrent workflow behavior.
- [ ] Add operation IDs, structured logs, latency/failure metrics, context/token budgets, and health checks.
- [ ] Establish source quality and answer-grounding regression evaluations with reviewed fixtures.
- [ ] Define deployment-specific access controls and retention rules before multi-user exposure.

**Exit evidence:** reproducible clean deployment, passing integration/evaluation suite, documented recovery rehearsal, and stated capacity limits. Passing offline unit tests alone does not satisfy this phase.

## Recommended delivery order

1. **Next change:** normalize three representative sources (one actual PDF, one HTML page, one mislabeled legacy file), preserving provenance and reporting extraction quality. Repair the corpus acceptance list and run live provider checks.
2. **Next vertical slice:** markdown storage plus one resumable ingestion with index/log updates. Finish phases 1–3 before broad corpus ingestion.
3. **Retrieval slice:** Oracle migrations, incremental indexing, and a cited single-session query. Introduce project keys now; prove full isolation in phase 6.
4. **Usability slice:** follow-ups, saved answers, project switching, interactive lint, and CLI chat.
5. **Release slice:** integration locks, recovery tests, evaluations, and operating documentation. Batch ingestion and richer source formats can expand afterward.

## Verification record and maintenance

Local validation for this refactor: **22 offline unit tests passed**; Ruff lint and formatting checks, Python compilation, CLI help, and `pip check` passed. The corpus audit reports **63 entries / 59 present / seven issues**, as expected from the retained archive. The audit returns exit code 1 to surface those existing issues. Reproduction commands are in `README.md`.

**Not verified:** live Nomic inference, Ollama availability/model quality, Oracle connectivity/indexes, full integration dependency resolution, and remote CI. No production corpus download or ingestion was run during this refactor.

When updating this manifest, change checkboxes only alongside implementation evidence. Record the relevant test command/result, migration or fixture, remaining limitation, and next dependency. Keep baseline observations separate from newly completed work.
