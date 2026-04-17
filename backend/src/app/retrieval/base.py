"""Simple retrieval interface."""

from typing import Protocol


class Retriever(Protocol):
    """Protocol for retrieval backends."""

    def search(self, query: str, top_k: int = 5) -> list[str]:
        """Return evidence snippets."""
