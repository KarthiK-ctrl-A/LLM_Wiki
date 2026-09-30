"""Small provider contracts for future application services and graph nodes."""

from typing import Protocol, Sequence


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> Sequence[Sequence[float]]: ...

    def embed_query(self, query: str) -> Sequence[float]: ...


class ChatProvider(Protocol):
    def complete(self, prompt: str) -> str: ...
