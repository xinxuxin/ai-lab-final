"""Target public product-page adapter backed by public page and RedSky JSON."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
from pydantic import HttpUrl, TypeAdapter

from app.collectors.product_pages.base import (
    ParsedProduct,
    ProductImageCandidate,
    ProductPageAdapter,
    ProductScrapeSnapshot,
    canonicalize_url,
    extract_tcin,
    normalize_text,
    review_text_hash,
    slugify,
)
from app.models.schemas import ReviewRecord

HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


class TargetProductPageAdapter(ProductPageAdapter):
    """Scrape public Target product pages and associated JSON payloads."""

    marketplace = "target"
    supported_domains = ("target.com",)
    base_url = "https://www.target.com"
    pdp_endpoint = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"

    def product_slug(self, url: str) -> str:
        """Build a stable slug from the canonical URL and TCIN."""
        canonical_url = canonicalize_url(url)
        tcin = extract_tcin(canonical_url) or "unknown"
        path_parts = [part for part in urlsplit(canonical_url).path.split("/") if part]
        readable = next(
            (part for part in path_parts if part not in {"p", "-"} and not part.startswith("A-")),
            f"target-product-{tcin}",
        )
        return f"{slugify(readable)}-{tcin}"

    def fetch_snapshot(
        self,
        *,
        client: httpx.Client,
        url: str,
        user_agent: str,
        pricing_store_id: str,
        api_key: str,
    ) -> ProductScrapeSnapshot:
        """Fetch the public product page HTML plus Target's public PDP JSON."""
        canonical_url = canonicalize_url(url)
        tcin = extract_tcin(canonical_url)
        if tcin is None:
            raise ValueError(f"Could not extract TCIN from Target URL: {url}")

        page_response = client.get(
            canonical_url,
            headers=self.default_headers(user_agent),
        )
        page_response.raise_for_status()

        params = {
            "key": api_key,
            "tcin": tcin,
            "pricing_store_id": pricing_store_id,
        }
        pdp_response = client.get(
            f"{self.pdp_endpoint}?{urlencode(params)}",
            headers={**self.default_headers(user_agent), "accept": "application/json"},
        )
        pdp_response.raise_for_status()

        return ProductScrapeSnapshot(
            source_url=canonical_url,
            canonical_url=canonical_url,
            product_id=tcin,
            page_html=page_response.text,
            pdp_payload=pdp_response.json(),
            fetched_at=datetime.now(UTC),
            request_log=[canonical_url, str(pdp_response.request.url)],
        )

    def parse_snapshot(
        self,
        *,
        snapshot: ProductScrapeSnapshot,
        max_reviews: int,
        min_review_chars: int,
    ) -> ParsedProduct:
        """Parse Target's PDP payload into durable product, review, and image artifacts."""
        product = snapshot.pdp_payload["data"]["product"]
        item = product["item"]
        description = item["product_description"]

        title = normalize_text(description.get("title", snapshot.product_id))
        category = normalize_text(
            product.get("category", {}).get("name")
            or item.get("product_classification", {}).get("item_type", {}).get("name", "unknown")
        )
        description_text = normalize_text(description.get("downstream_description", ""))
        bullet_text = [
            normalize_text(entry)
            for entry in description.get("bullet_descriptions", [])
            if normalize_text(entry)
        ]

        reviews = self._parse_reviews(
            raw_reviews=product.get("ratings_and_reviews", {}).get("most_recent", []),
            product_id=snapshot.product_id,
            source_url=snapshot.canonical_url,
            min_review_chars=min_review_chars,
            max_reviews=max_reviews,
        )

        image_candidates = self._parse_images(item.get("enrichment", {}))
        notes: list[str] = []
        visible_review_count = _coerce_int(
            product.get("ratings_and_reviews", {}).get("statistics", {}).get("review_count")
        )
        if visible_review_count is not None and len(reviews) < min(
            visible_review_count, max_reviews
        ):
            notes.append(
                "Only the publicly exposed most_recent review block was available "
                "from Target's PDP JSON."
            )

        return ParsedProduct(
            product_id=snapshot.product_id,
            title=title,
            category=category,
            marketplace=self.marketplace,
            source_url=snapshot.canonical_url,
            description=description_text,
            bullet_text=bullet_text,
            rating=_coerce_float(
                product.get("ratings_and_reviews", {})
                .get("statistics", {})
                .get("rating", {})
                .get("average")
            ),
            visible_review_count=visible_review_count,
            reviews=reviews,
            image_candidates=image_candidates,
            notes=notes,
        )

    def _parse_reviews(
        self,
        *,
        raw_reviews: list[dict[str, Any]],
        product_id: str,
        source_url: str,
        min_review_chars: int,
        max_reviews: int,
    ) -> list[ReviewRecord]:
        """Normalize, deduplicate, and filter public review records."""
        deduped_reviews: list[ReviewRecord] = []
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()

        for raw_review in raw_reviews:
            body = normalize_text(str(raw_review.get("text", "")))
            title = normalize_text(str(raw_review.get("title", ""))) or None
            combined_text = " ".join(part for part in [title or "", body] if part).strip()
            if len(combined_text) < min_review_chars:
                continue

            review_id = normalize_text(str(raw_review.get("id", ""))) or review_text_hash(
                title, body
            )
            content_hash = review_text_hash(title, body)
            if review_id in seen_ids or content_hash in seen_hashes:
                continue

            seen_ids.add(review_id)
            seen_hashes.add(content_hash)
            deduped_reviews.append(
                ReviewRecord(
                    review_id=review_id,
                    product_id=product_id,
                    author=normalize_text(str(raw_review.get("author", {}).get("nickname", "")))
                    or None,
                    rating=_coerce_float(raw_review.get("rating", {}).get("value")),
                    title=title,
                    body=body,
                    posted_at=_parse_datetime(raw_review.get("rating", {}).get("submitted_at")),
                    helpful_votes=_coerce_int(raw_review.get("helpful_votes")),
                    verified=_coerce_bool(raw_review.get("is_verified")),
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )
            if len(deduped_reviews) >= max_reviews:
                break

        return deduped_reviews

    def _parse_images(self, enrichment: dict[str, Any]) -> list[ProductImageCandidate]:
        """Extract unique reference image URLs from the public PDP payload."""
        image_info = enrichment.get("image_info", {})
        image_urls: list[ProductImageCandidate] = []
        seen_urls: set[str] = set()

        primary_url = normalize_text(str(image_info.get("primary_image", {}).get("url", "")))
        if primary_url:
            seen_urls.add(primary_url)
            image_urls.append(ProductImageCandidate(url=primary_url))

        for entry in image_info.get("alternate_images", []):
            url = normalize_text(str(entry.get("url", "")))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            image_urls.append(
                ProductImageCandidate(
                    url=url,
                    alt_text=normalize_text(str(entry.get("alt_text", ""))) or None,
                )
            )

        return image_urls


def _coerce_float(value: Any) -> float | None:
    """Convert optional API values to float."""
    if value is None or value == "":
        return None
    return float(value)


def _coerce_int(value: Any) -> int | None:
    """Convert optional API values to int."""
    if value is None or value == "":
        return None
    return int(value)


def _coerce_bool(value: Any) -> bool | None:
    """Convert optional API values to bool."""
    if value is None or value == "":
        return None
    return bool(value)


def _parse_datetime(value: Any) -> datetime | None:
    """Parse ISO timestamps emitted by Target's public APIs."""
    if value is None or value == "":
        return None
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)
