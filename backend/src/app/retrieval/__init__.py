"""Retrieval abstractions and default backends."""

from app.retrieval.base import EmbeddingClient, RetrievalQuery, Retriever, RetrieverFactory
from app.retrieval.local import KeywordOverlapRetriever, LocalEmbeddingRetriever
from app.retrieval.managed import ManagedVectorDBRetriever

__all__ = [
    "EmbeddingClient",
    "KeywordOverlapRetriever",
    "RetrievalQuery",
    "Retriever",
    "RetrieverFactory",
    "LocalEmbeddingRetriever",
    "ManagedVectorDBRetriever",
]
