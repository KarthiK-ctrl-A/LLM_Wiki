# Step Zero completion evidence

Step Zero was completed locally on 2026-09-29 America/New_York (machine reports use UTC on September 30).

- Oracle 26ai Free `23.26.2.0.0`, PDB `FREEPDB1`: create/insert/select/drop passed in [oracle.json](verification/oracle.json).
- Nomic Embed v2: pinned weights and code revisions produced normalized 768-dimensional vectors and ranked the expected passage first in [embeddings.json](verification/embeddings.json).
- Ollama `gemma4:latest`: returned a non-empty LangChain response in [llm.json](verification/llm.json).
- LangGraph: a compiled state graph executed successfully in [graph.json](verification/graph.json).
- Corpus: 52 reviewed sources (41 PDF, 11 HTML), 11 explicit exclusions, and `ready: true` in [corpus.json](verification/corpus.json).
- Credentials remain in ignored `.env`; no password is stored in the reports.

The corpus review covers readability, provenance, domain relevance, and representative visual PDF checks. It is not an exhaustive claim-level audit. Table extraction can lose layout, sparse pages remain flagged, and no OCR is claimed. Future ingestion must use only records whose status is `accepted`.
