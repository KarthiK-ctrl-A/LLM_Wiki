"""Compatibility import; new code should import llm_wiki.embeddings."""

from llm_wiki.embeddings import NomicEmbeddingService

__all__ = ["NomicEmbeddingService"]
