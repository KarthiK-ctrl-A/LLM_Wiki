"""Explicit live checks. Reports contain evidence, never connection passwords."""

from datetime import datetime, timezone
from importlib.metadata import version
from typing import TypedDict
from uuid import uuid4

from llm_wiki.config import Settings


def verify_oracle(settings: Settings) -> dict:
    import oracledb

    if not settings.oracle_password:
        raise ValueError("Set ORACLE_PASSWORD in the selected .env or process environment")
    table = "WIKI_CHECK_" + uuid4().hex[:16].upper()
    with oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password,
        dsn=settings.oracle_dsn,
        tcp_connect_timeout=10,
    ) as connection:
        connection.call_timeout = 15000
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE TABLE {table} (id NUMBER PRIMARY KEY, label VARCHAR2(40))")
            try:
                cursor.execute(f"INSERT INTO {table} (id, label) VALUES (:1, :2)", [1, "step-zero"])
                connection.commit()
                cursor.execute(f"SELECT label FROM {table} WHERE id = :1", [1])
                if cursor.fetchone() != ("step-zero",):
                    raise ValueError("Oracle round-trip mismatch")
                cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CON_NAME') FROM dual")
                pdb = cursor.fetchone()[0]
            finally:
                cursor.execute(f"DROP TABLE {table} PURGE")
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", [table])
            if cursor.fetchone()[0] != 0:
                raise ValueError("Oracle smoke table cleanup failed")
        return {
            "database_version": connection.version,
            "pdb": pdb,
            "create_insert_select_drop": True,
            "driver": version("oracledb"),
        }


def verify_embeddings(settings: Settings) -> dict:
    import numpy as np

    from llm_wiki.embeddings import NomicEmbeddingService

    service = NomicEmbeddingService(
        settings.embedding_model,
        dimension=settings.embedding_dimension,
        revision=settings.embedding_revision,
        code_revision=settings.embedding_code_revision,
    )
    documents = service.embed_documents(
        [
            "Reinsurance transfers risk between insurers.",
            "A deductible is the amount retained by a policyholder.",
        ]
    )
    query = service.embed_query("How do insurers transfer risk?")
    scores = documents @ query
    if int(np.argmax(scores)) != 0:
        raise ValueError("Embedding semantic smoke query did not rank the expected document first")
    return {
        "model": settings.embedding_model,
        "revision": settings.embedding_revision,
        "code_revision": settings.embedding_code_revision,
        "document_shape": list(documents.shape),
        "query_shape": list(query.shape),
        "cosine_scores": scores.tolist(),
        "expected_document_ranked_first": True,
        "sentence_transformers": version("sentence-transformers"),
    }


def verify_llm(settings: Settings) -> dict:
    import requests

    from llm_wiki.llm import OllamaChatService

    response = requests.get(settings.ollama_url.rstrip("/") + "/api/tags", timeout=10)
    response.raise_for_status()
    model = next((m for m in response.json()["models"] if m["name"] == settings.ollama_model), None)
    if model is None:
        raise ValueError("Configured Ollama model is not installed")
    service = OllamaChatService(
        settings.ollama_model,
        base_url=settings.ollama_url,
        timeout=settings.llm_timeout,
    )
    answer = service.complete("Reply with one short sentence confirming that you can respond.")
    return {
        "model": settings.ollama_model,
        "digest": model["digest"],
        "response": answer,
        "langchain_ollama": version("langchain-ollama"),
    }


class ProbeState(TypedDict):
    value: int


def verify_graph() -> dict:
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(ProbeState)
    builder.add_node("increment", lambda state: {"value": state["value"] + 1})
    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)
    result = builder.compile().invoke({"value": 0})
    if result["value"] != 1:
        raise ValueError("LangGraph execution failed")
    return {"langgraph": version("langgraph"), "langchain": version("langchain"), "result": result}


def verify(provider: str, settings: Settings) -> dict:
    checks = {
        "oracle": lambda: verify_oracle(settings),
        "embeddings": lambda: verify_embeddings(settings),
        "llm": lambda: verify_llm(settings),
        "graph": verify_graph,
    }
    result = checks[provider]()
    return {
        "provider": provider,
        "status": "passed",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }
