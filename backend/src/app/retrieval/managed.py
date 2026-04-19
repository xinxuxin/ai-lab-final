"""Optional managed vector database adapter placeholder."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import RetrievedEvidence, ReviewChunk
from app.retrieval.base import EmbeddingClient, RetrievalQuery, Retriever


@dataclass(slots=True)
class ManagedVectorDBRetriever(Retriever):
    """Placeholder adapter for a managed vector DB integration."""

    provider_name: str
    product_slug: str
    chunks: list[ReviewChunk]
    embedding_client: EmbeddingClient

    def search(self, query: RetrievalQuery, top_k: int = 5) -> list[RetrievedEvidence]:
        """Managed retrieval is optional and intentionally not wired by default."""
        del query, top_k
        raise NotImplementedError(
            f"Managed retriever '{self.provider_name}' is not configured in this repository."
        )
