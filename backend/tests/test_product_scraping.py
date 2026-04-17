"""Product scraping parser and persistence tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image
from pytest import MonkeyPatch

from app.collectors.product_pages.base import ProductScrapeSnapshot
from app.collectors.product_pages.service import artifacts_complete, run_scrape_product
from app.collectors.product_pages.target import TargetProductPageAdapter
from app.config.settings import Settings


def test_target_parser_extracts_product_data() -> None:
    """Target adapter should parse title, reviews, and image candidates from a fixture."""
    fixture_dir = Path(__file__).parent / "fixtures" / "product_pages"
    html = (fixture_dir / "target_product_page.html").read_text(encoding="utf-8")
    payload = json.loads((fixture_dir / "target_pdp_response.json").read_text(encoding="utf-8"))
    adapter = TargetProductPageAdapter()

    parsed = adapter.parse_snapshot(
        snapshot=ProductScrapeSnapshot(
            source_url="https://www.target.com/p/levoit-core-300-air-purifier-white/-/A-81910071",
            canonical_url="https://www.target.com/p/levoit-core-300-air-purifier-white/-/A-81910071",
            product_id="81910071",
            page_html=html,
            pdp_payload=payload,
            fetched_at=datetime.now(UTC),
            request_log=["html", "pdp"],
        ),
        max_reviews=100,
        min_review_chars=25,
    )

    assert parsed.title == "Levoit Core 300 Air Purifier White"
    assert parsed.category == "Air Purifiers"
    assert parsed.visible_review_count == 210
    assert len(parsed.reviews) == 2
    assert parsed.reviews[0].review_id == "review-1"
    assert len(parsed.image_candidates) == 3


def test_run_scrape_product_writes_artifacts_with_mocked_network(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """Product scraping should persist all required artifacts when network calls succeed."""
    fixture_dir = Path(__file__).parent / "fixtures" / "product_pages"
    html = (fixture_dir / "target_product_page.html").read_text(encoding="utf-8")
    payload = (fixture_dir / "target_pdp_response.json").read_bytes()
    image_bytes = _build_test_image_bytes()

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            del exc_type, exc, tb

        def get(self, url: str, headers: dict[str, str] | None = None) -> httpx.Response:
            del headers
            request = httpx.Request("GET", url)
            if "pdp_client_v1" in url:
                return httpx.Response(200, request=request, content=payload)
            if "scene7.com" in url:
                return httpx.Response(
                    200,
                    request=request,
                    content=image_bytes,
                    headers={"content-type": "image/png"},
                )
            return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr("app.collectors.product_pages.service.httpx.Client", FakeClient)
    monkeypatch.setattr("app.collectors.product_pages.service.time.sleep", lambda seconds: None)

    settings = Settings(
        SCRAPING_MAX_RETRIES=1,
        SCRAPING_REQUEST_DELAY_SECONDS=0,
        SCRAPING_MIN_REVIEW_CHARS=25,
        TARGET_PRICING_STORE_ID="2077",
    )
    result = run_scrape_product(
        url="https://www.target.com/p/levoit-core-300-air-purifier-white/-/A-81910071",
        max_reviews=100,
        refresh=True,
        reuse_existing=False,
        output_dir=tmp_path / "data" / "raw",
        settings=settings,
        category_hint="home-appliance",
    )

    assert result.report.status == "partial_success"
    assert result.report.collected_review_count == 2
    assert result.report.image_count == 3
    assert artifacts_complete(result.output_dir)
    assert (result.output_dir / "product_meta.json").exists()
    assert (result.output_dir / "description.json").exists()
    assert (result.output_dir / "reviews.jsonl").exists()
    assert (result.output_dir / "raw_html" / "product_page.html").exists()
    assert (result.output_dir / "raw_html" / "pdp_client_v1.json").exists()


def _build_test_image_bytes() -> bytes:
    """Create a tiny valid PNG image for image-download tests."""
    buffer = BytesIO()
    image = Image.new("RGB", (2, 2), color=(255, 255, 255))
    image.save(buffer, format="PNG")
    return buffer.getvalue()
