"""Default local embedding-cache retriever."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import cast

from app.models.schemas import RetrievedEvidence, ReviewChunk
from app.retrieval.base import EmbeddingClient, RetrievalQuery, Retriever
from app.utils.artifacts import OUTPUTS_DIR

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def review_embedding_cache_path(product_slug: str) -> Path:
    """Return the per-product local embedding cache path."""
    return OUTPUTS_DIR / "visual_profiles" / product_slug / "embedding_cache.json"


@dataclass(slots=True)
class LocalEmbeddingRetriever(Retriever):
    """Retriever backed by on-disk embedding cache plus cosine similarity."""

    product_slug: str
    chunks: list[ReviewChunk]
    embedding_client: EmbeddingClient
    cache_path: Path | None = None

    def __post_init__(self) -> None:
        """Materialize or reuse the local embedding cache."""
        self._cache_path = self.cache_path or review_embedding_cache_path(self.product_slug)
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._chunk_embeddings = self._load_or_build_embeddings()

    def search(self, query: RetrievalQuery, top_k: int = 5) -> list[RetrievedEvidence]:
        """Rank review chunks with cosine similarity against the query embedding."""
        query_embedding = self.embedding_client.embed_texts([query.query])[0]
        scored = [
            (
                _cosine_similarity(query_embedding, embedding),
                chunk,
            )
            for chunk, embedding in zip(self.chunks, self._chunk_embeddings, strict=True)
        ]
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        return [
            RetrievedEvidence(
                aspect_key=query.aspect_key,
                query=query.query,
                chunk_id=chunk.chunk_id,
                source_review_id=chunk.source_review_id,
                score=score,
                snippet=chunk.text,
            )
            for score, chunk in ranked
        ]

    def _load_or_build_embeddings(self) -> list[list[float]]:
        """Reuse cached embeddings when chunk hashes match, else recompute."""
        chunk_hashes = {chunk.chunk_id: _chunk_hash(chunk) for chunk in self.chunks}
        cached_embeddings = self._load_cache()
        missing_chunks = [
            chunk
            for chunk in self.chunks
            if chunk.chunk_id not in cached_embeddings
            or cached_embeddings[chunk.chunk_id]["chunk_hash"] != chunk_hashes[chunk.chunk_id]
        ]

        if missing_chunks:
            vectors = self.embedding_client.embed_texts([chunk.text for chunk in missing_chunks])
            for chunk, vector in zip(missing_chunks, vectors, strict=True):
                cached_embeddings[chunk.chunk_id] = {
                    "chunk_hash": chunk_hashes[chunk.chunk_id],
                    "embedding": vector,
                }
            self._cache_path.write_text(
                json.dumps(
                    {
                        "product_slug": self.product_slug,
                        "embeddings": cached_embeddings,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        result: list[list[float]] = []
        for chunk in self.chunks:
            raw_embedding = cached_embeddings[chunk.chunk_id]["embedding"]
            vector = cast(list[float], raw_embedding)
            result.append(list(vector))
        return result

    def _load_cache(self) -> dict[str, dict[str, object]]:
        """Load the local embedding cache if present."""
        if not self._cache_path.exists():
            return {}
        payload = json.loads(self._cache_path.read_text(encoding="utf-8"))
        embeddings = payload.get("embeddings", {})
        if not isinstance(embeddings, dict):
            return {}
        return {
            str(chunk_id): value
            for chunk_id, value in embeddings.items()
            if isinstance(value, dict)
        }


@dataclass(slots=True)
class KeywordOverlapRetriever(Retriever):
    """Fallback lexical retriever when embeddings are unavailable."""

    chunks: list[ReviewChunk]

    def search(self, query: RetrievalQuery, top_k: int = 5) -> list[RetrievedEvidence]:
        """Rank chunks by normalized keyword overlap."""
        query_tokens = set(TOKEN_PATTERN.findall(query.query.lower()))
        scored = [
            (
                _keyword_overlap_score(query_tokens, chunk.text),
                chunk,
            )
            for chunk in self.chunks
        ]
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        return [
            RetrievedEvidence(
                aspect_key=query.aspect_key,
                query=query.query,
                chunk_id=chunk.chunk_id,
                source_review_id=chunk.source_review_id,
                score=score,
                snippet=chunk.text,
            )
            for score, chunk in ranked
            if score > 0.0
        ]


def _chunk_hash(chunk: ReviewChunk) -> str:
    """Create a durable text hash for cache invalidation."""
    return sha256(chunk.text.encode("utf-8")).hexdigest()


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two dense vectors."""
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _keyword_overlap_score(query_tokens: set[str], text: str) -> float:
    """Score a chunk by token overlap with the retrieval query."""
    text_tokens = set(TOKEN_PATTERN.findall(text.lower()))
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    return overlap / float(len(query_tokens))
