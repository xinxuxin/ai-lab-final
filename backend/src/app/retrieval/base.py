"""Retrieval abstractions for local and managed evidence stores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.schemas import RetrievedEvidence, ReviewChunk


@dataclass(slots=True)
class RetrievalQuery:
    """One aspect-specific retrieval query."""

    aspect_key: str
    query: str


class EmbeddingClient(Protocol):
    """Protocol for embedding providers."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class Retriever(Protocol):
    """Protocol for retrieval backends."""

    def search(self, query: RetrievalQuery, top_k: int = 5) -> list[RetrievedEvidence]:
        """Return ranked evidence snippets for one aspect query."""


class RetrieverFactory(Protocol):
    """Protocol for constructing retrievers from prepared chunks."""

    def build(
        self,
        *,
        product_slug: str,
        chunks: list[ReviewChunk],
        embedding_client: EmbeddingClient,
    ) -> Retriever:
        """Create a retriever for one product corpus."""
