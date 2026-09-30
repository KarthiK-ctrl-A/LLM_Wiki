"""Lazy Nomic adapter. Model-specific prefixes live only at this boundary."""

import math
from typing import Any


class NomicEmbeddingService:
    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v2-moe",
        *,
        dimension: int = 768,
        revision: str | None = None,
        code_revision: str | None = None,
        encoder: Any = None,
    ):
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
        self.model_name = model_name
        self.dimension = dimension
        self.revision = revision
        self.code_revision = code_revision
        self._model = encoder

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name, revision=self.revision, trust_remote_code=True,
                model_kwargs={"code_revision": self.code_revision} if self.code_revision else None,
                config_kwargs={"code_revision": self.code_revision} if self.code_revision else None,
            )
        return self._model

    def _encode(self, texts: list[str], prefix: str):
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Provide at least one nonblank text")
        vectors = self.model.encode(
            [f"{prefix}{text}" for text in texts],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        if vectors.shape != (len(texts), self.dimension):
            raise ValueError(
                f"Expected ({len(texts)}, {self.dimension}) embeddings; got {vectors.shape}"
            )
        for row in vectors:
            if not all(math.isfinite(float(value)) for value in row):
                raise ValueError("Embedding contains nonfinite values")
            if not math.isclose(sum(float(v) ** 2 for v in row), 1, abs_tol=1e-4):
                raise ValueError("Embedding must have unit norm")
        return vectors

    def embed_documents(self, texts: list[str]):
        return self._encode(texts, "search_document: ")

    def embed_query(self, query: str):
        return self._encode([query], "search_query: ")[0]
