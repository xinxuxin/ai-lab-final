"""Base classes and helpers for public product-page scraping adapters."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from typing import Any, Final
from urllib.parse import urlsplit, urlunsplit

import httpx

from app.models.schemas import ReviewRecord

FAILURE_BLOCKED: Final[str] = "blocked"
FAILURE_PARSE_FAILED: Final[str] = "parse_failed"
FAILURE_NO_REVIEWS_ACCESSIBLE: Final[str] = "no_reviews_accessible"
FAILURE_IMAGE_DOWNLOAD_FAILED: Final[str] = "image_download_failed"
FAILURE_PARTIAL_SUCCESS: Final[str] = "partial_success"

TCIN_PATTERN: Final[re.Pattern[str]] = re.compile(r"/A-(?P<tcin>\d+)")


def canonicalize_url(url: str) -> str:
    """Strip query strings and fragments from a product URL."""
    split = urlsplit(url)
    return urlunsplit((split.scheme, split.netloc, split.path.rstrip("/"), "", ""))


def slugify(value: str) -> str:
    """Create a filesystem-safe slug from arbitrary text."""
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    compact = "-".join(part for part in normalized.split("-") if part)
    return compact or "product"


def extract_tcin(url: str) -> str | None:
    """Extract Target's TCIN identifier from a public product URL."""
    match = TCIN_PATTERN.search(url)
    if match is None:
        return None
    return match.group("tcin")


def normalize_text(value: str) -> str:
    """Collapse whitespace and decode HTML entities for durable comparisons."""
    return " ".join(unescape(value).split())


def review_text_hash(title: str | None, body: str) -> str:
    """Hash normalized review content when no durable review ID is available."""
    normalized = f"{normalize_text(title or '')}\n{normalize_text(body)}".strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class ProductImageCandidate:
    """One publicly visible reference image candidate."""

    url: str
    alt_text: str | None = None


@dataclass(slots=True)
class ParsedProduct:
    """Structured product-page scrape output before filesystem persistence."""

    product_id: str
    title: str
    category: str
    marketplace: str
    source_url: str
    description: str
    bullet_text: list[str]
    rating: float | None
    visible_review_count: int | None
    reviews: list[ReviewRecord] = field(default_factory=list)
    image_candidates: list[ProductImageCandidate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProductScrapeSnapshot:
    """Raw network responses collected for one product."""

    source_url: str
    canonical_url: str
    product_id: str
    page_html: str
    pdp_payload: dict[str, Any]
    fetched_at: datetime
    request_log: list[str] = field(default_factory=list)


class ProductPageAdapter(ABC):
    """Base interface for marketplace-specific product-page scrapers."""

    marketplace: str
    supported_domains: tuple[str, ...]

    def matches_url(self, url: str) -> bool:
        """Return whether this adapter handles the given product URL."""
        hostname = urlsplit(url).netloc.lower()
        return any(hostname.endswith(domain) for domain in self.supported_domains)

    def default_headers(self, user_agent: str) -> dict[str, str]:
        """Return polite default request headers."""
        return {
            "user-agent": user_agent,
            "accept-language": "en-US,en;q=0.9",
        }

    def is_blocked_response(self, response: httpx.Response) -> bool:
        """Classify clearly blocked responses."""
        return response.status_code in {401, 403, 429, 503}

    @abstractmethod
    def product_slug(self, url: str) -> str:
        """Return a durable filesystem slug for the product URL."""

    @abstractmethod
    def fetch_snapshot(
        self,
        *,
        client: httpx.Client,
        url: str,
        user_agent: str,
        pricing_store_id: str,
        api_key: str,
    ) -> ProductScrapeSnapshot:
        """Fetch the raw public resources needed for one product."""

    @abstractmethod
    def parse_snapshot(
        self,
        *,
        snapshot: ProductScrapeSnapshot,
        max_reviews: int,
        min_review_chars: int,
    ) -> ParsedProduct:
        """Convert raw responses into structured product and review artifacts."""
