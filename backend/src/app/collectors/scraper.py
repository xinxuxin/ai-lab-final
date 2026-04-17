"""Placeholder scraping routines."""

from app.models.schemas import ProductRecord, ReviewRecord


def scrape_product(seed_url: str) -> tuple[ProductRecord | None, list[ReviewRecord]]:
    """Return placeholder scrape outputs."""
    del seed_url
    return None, []
