"""Best Buy search page discovery adapter."""

from __future__ import annotations

import re
from typing import Final

from bs4 import BeautifulSoup, Tag

from app.collectors.discovery.base import (
    DiscoveryAdapter,
    DiscoveryPage,
    DiscoveryParseResult,
    canonicalize_url,
    join_url,
)
from app.models.schemas import DiscoveryCandidate

BESTBUY_PRODUCT_PATH: Final[str] = "/product/"
RATING_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"Rating\s+(?P<rating>\d+(?:\.\d+)?)\s+out of 5 stars with\s+(?P<count>[\d,]+)\s+reviews",
    re.IGNORECASE,
)
PRICE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\$(?P<price>\d+(?:\.\d{2})?)")


class BestBuyDiscoveryAdapter(DiscoveryAdapter):
    """Parse publicly accessible Best Buy search results."""

    marketplace = "bestbuy"
    base_url = "https://www.bestbuy.com"

    def build_search_url(self, query: str) -> str:
        """Build a Best Buy search URL."""
        normalized_query = query.replace(" ", "+")
        return f"{self.base_url}/site/searchpage.jsp?st={normalized_query}"

    def parse_search_results(self, page: DiscoveryPage) -> DiscoveryParseResult:
        """Extract candidate product cards from the search result page."""
        soup = BeautifulSoup(page.html, "html.parser")
        cards = soup.select("div.list-item.wrapper")
        candidates: list[DiscoveryCandidate] = []

        for card in cards:
            title_link = card.select_one("a.sku-title")
            image = card.select_one("a.image-section img")
            if title_link is None:
                continue

            href = title_link.get("href")
            title = " ".join(title_link.get_text(" ", strip=True).split())
            if not href or not title:
                continue

            canonical_url = join_url(self.base_url, str(href))
            review_text = ""
            review_node = card.select_one(".nc-rating-review-wrapper p.visually-hidden")
            if review_node is not None:
                review_text = " ".join(review_node.get_text(" ", strip=True).split())

            rating: float | None = None
            visible_review_count: int | None = None
            rating_match = RATING_PATTERN.search(review_text)
            if rating_match:
                rating = float(rating_match.group("rating"))
                visible_review_count = int(rating_match.group("count").replace(",", ""))

            price = self._extract_price_for_card(card=card, soup=soup)

            thumbnail_url: str | None = None
            if image is not None and image.get("src"):
                thumbnail_url = canonicalize_url(join_url(self.base_url, str(image["src"])))

            candidates.append(
                DiscoveryCandidate(
                    title=title,
                    canonical_url=canonical_url,
                    marketplace=self.marketplace,
                    query=page.query.query,
                    category_guess=page.query.category_guess,
                    price=price,
                    rating=rating,
                    visible_review_count=visible_review_count,
                    thumbnail_url=thumbnail_url,
                    is_product_page=BESTBUY_PRODUCT_PATH in canonical_url
                    and "/sku/" in canonical_url,
                    raw_html_path=str(page.raw_html_path),
                    matched_queries=[page.query.query],
                )
            )

        notes: list[str] = []
        if not candidates:
            notes.append("no sku-title product cards were parsed from the search page")

        return DiscoveryParseResult(candidates=candidates, notes=notes)

    def _extract_price_for_card(self, card: Tag, soup: BeautifulSoup) -> float | None:
        """Resolve the hydrated price block for a card if present."""
        template = card.select_one("template[id^='B:']")
        if template is None:
            return None

        template_id = template.get("id")
        if not template_id or ":" not in template_id:
            return None

        suffix = str(template_id).split(":", maxsplit=1)[1]
        hidden_price_block = soup.find("div", id=f"S:{suffix}")
        if hidden_price_block is None:
            return None

        text = " ".join(hidden_price_block.get_text(" ", strip=True).split())
        price_match = PRICE_PATTERN.search(text)
        if price_match is None:
            return None

        return float(price_match.group("price"))
