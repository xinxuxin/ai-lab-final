"""Discovery parser and ranking tests."""

from pathlib import Path

from app.collectors.discovery.bestbuy import BestBuyDiscoveryAdapter
from app.collectors.discovery.service import (
    compute_candidate_score,
    dedupe_candidates,
    rank_candidates,
)
from app.models.schemas import DiscoveryCandidate, DiscoveryQuerySeed


def test_bestbuy_parser_extracts_candidates() -> None:
    """Best Buy parser should extract core candidate fields from fixture HTML."""
    fixture_path = Path(__file__).parent / "fixtures" / "discovery" / "bestbuy_search_fixture.html"
    adapter = BestBuyDiscoveryAdapter()
    query = DiscoveryQuerySeed(query="insulated tumbler", category_guess="drinkware")
    page = adapter.create_page(
        query_seed=query,
        html=fixture_path.read_text(encoding="utf-8"),
        raw_html_path=fixture_path,
        status_code=200,
    )

    result = adapter.parse_search_results(page)

    assert len(result.candidates) == 2
    first = result.candidates[0]
    assert first.title == "Example Brand - Insulated Tumbler - Blue"
    assert (
        str(first.canonical_url)
        == "https://www.bestbuy.com/product/example-insulated-tumbler/sku/1111111"
    )
    assert first.price == 29.99
    assert first.rating == 4.6
    assert first.visible_review_count == 210


def test_dedupe_and_rank_candidates() -> None:
    """Ranking should favor review count and merge duplicate canonical URLs."""
    first = DiscoveryCandidate(
        title="Candidate A",
        canonical_url="https://www.bestbuy.com/product/a/sku/1",
        marketplace="bestbuy",
        query="desk lamp",
        category_guess="lighting",
        visible_review_count=50,
        rating=4.2,
        matched_queries=["desk lamp"],
    )
    duplicate = DiscoveryCandidate(
        title="Candidate A duplicate",
        canonical_url="https://www.bestbuy.com/product/a/sku/1?skuId=1",
        marketplace="bestbuy",
        query="table lamp",
        category_guess="lighting",
        visible_review_count=120,
        rating=4.7,
        matched_queries=["table lamp"],
    )
    second = DiscoveryCandidate(
        title="Candidate B",
        canonical_url="https://www.bestbuy.com/product/b/sku/2",
        marketplace="bestbuy",
        query="desk lamp",
        category_guess="lighting",
        visible_review_count=30,
        rating=4.9,
        matched_queries=["desk lamp"],
    )

    deduped, duplicate_count = dedupe_candidates([first, duplicate, second])
    ranked = rank_candidates(deduped)

    assert duplicate_count == 1
    assert len(deduped) == 2
    assert sorted(ranked[0].matched_queries) == ["desk lamp", "table lamp"]
    assert compute_candidate_score(ranked[0]) >= compute_candidate_score(ranked[1])
