"""Base classes and helpers for marketplace discovery adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

import httpx

from app.models.schemas import DiscoveryCandidate, DiscoveryQuerySeed

FAILURE_BLOCKED: Final[str] = "blocked"
FAILURE_PARSE_FAILED: Final[str] = "parse_failed"
FAILURE_NO_RESULTS: Final[str] = "no_results"
FAILURE_DUPLICATE_REMOVED: Final[str] = "duplicate_removed"


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug from a query string."""
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    compact = "-".join(part for part in normalized.split("-") if part)
    return compact or "query"


def canonicalize_url(url: str) -> str:
    """Strip query strings and fragments from URLs for deduplication."""
    split = urlsplit(url)
    return urlunsplit((split.scheme, split.netloc, split.path.rstrip("/"), "", ""))


def join_url(base_url: str, url: str) -> str:
    """Resolve relative URLs against a base URL."""
    return canonicalize_url(urljoin(base_url, url))


@dataclass(slots=True)
class DiscoveryContext:
    """Runtime context for one adapter invocation."""

    query: DiscoveryQuerySeed
    output_dir: Path
    raw_html_dir: Path


@dataclass(slots=True)
class DiscoveryPage:
    """Fetched search page plus metadata for parsing and persistence."""

    query: DiscoveryQuerySeed
    marketplace: str
    url: str
    html: str
    raw_html_path: Path
    status_code: int


@dataclass(slots=True)
class DiscoveryParseResult:
    """Parsed candidates plus adapter-level notes."""

    candidates: list[DiscoveryCandidate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class DiscoveryAdapter(ABC):
    """Base interface for discovery adapters."""

    marketplace: str
    base_url: str

    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """Build the search URL for a plain-text query."""

    @abstractmethod
    def parse_search_results(self, page: DiscoveryPage) -> DiscoveryParseResult:
        """Parse a search result page into candidate products."""

    def build_query_plan(
        self,
        query_seed: DiscoveryQuerySeed,
        raw_html_dir: Path,
        ordinal: int,
    ) -> tuple[str, Path]:
        """Return the search URL and raw HTML path for a query."""
        search_url = self.build_search_url(query_seed.query)
        filename = f"{ordinal:02d}_{self.marketplace}_{slugify(query_seed.query)}.html"
        return search_url, raw_html_dir / filename

    def create_page(
        self,
        query_seed: DiscoveryQuerySeed,
        html: str,
        raw_html_path: Path,
        status_code: int,
    ) -> DiscoveryPage:
        """Wrap fetched HTML in a typed container for parsing."""
        return DiscoveryPage(
            query=query_seed,
            marketplace=self.marketplace,
            url=self.build_search_url(query_seed.query),
            html=html,
            raw_html_path=raw_html_path,
            status_code=status_code,
        )

    def default_headers(self, user_agent: str) -> dict[str, str]:
        """Return polite default request headers."""
        return {
            "user-agent": user_agent,
            "accept-language": "en-US,en;q=0.9",
        }

    def is_blocked_response(self, response: httpx.Response) -> bool:
        """Classify clearly blocked responses."""
        return response.status_code in {401, 403, 429, 503}

    def robots_url(self) -> str:
        """Return the robots.txt URL for this adapter."""
        return urljoin(self.base_url, "/robots.txt")

    def encoded_query(self, query: str) -> str:
        """URL-encode a query term."""
        return urlencode({"q": query})
