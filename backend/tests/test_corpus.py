"""Processed corpus cleaning and Q1 validation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from PIL import Image
from pydantic import HttpUrl, TypeAdapter

from app.models.schemas import ProcessedManifest, ReviewRecord
from app.services.corpus import build_processed_corpus, clean_reviews, validate_q1_artifacts

HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


class FixtureProduct(TypedDict):
    """Typed product fixture entry used for corpus tests."""

    slug: str
    id: str
    category: str
    description: str
    review_count: int


def test_clean_reviews_removes_duplicates_and_short_reviews() -> None:
    """Cleaning should deduplicate repeated reviews and drop short reviews."""
    reviews = [
        ReviewRecord(
            review_id="a",
            product_id="1",
            title="Great sound",
            body="Great sound quality and comfortable fit for long listening sessions.",
            source_url=HTTP_URL_ADAPTER.validate_python("https://example.com/product"),
        ),
        ReviewRecord(
            review_id="a",
            product_id="1",
            title="Great sound",
            body="Great sound quality and comfortable fit for long listening sessions.",
            source_url=HTTP_URL_ADAPTER.validate_python("https://example.com/product"),
        ),
        ReviewRecord(
            review_id="b",
            product_id="1",
            title=None,
            body="Good",
            source_url=HTTP_URL_ADAPTER.validate_python("https://example.com/product"),
        ),
    ]

    cleaned, stats = clean_reviews(raw_reviews=reviews, min_review_chars=25)

    assert len(cleaned) == 1
    assert stats.duplicates_removed == 1
    assert stats.short_reviews_removed == 1


def test_q1_validation_requires_distinct_categories(tmp_path: Path) -> None:
    """Q1 validation should fail when selected products are not category-unique."""
    selected_path = tmp_path / "selected_products.jsonl"
    selected_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "marketplace": "target",
                        "category": "audio",
                        "product_url": "https://www.target.com/p/product-one/-/A-1",
                        "title_hint": "One",
                    }
                ),
                json.dumps(
                    {
                        "marketplace": "target",
                        "category": "audio",
                        "product_url": "https://www.target.com/p/product-two/-/A-2",
                        "title_hint": "Two",
                    }
                ),
                json.dumps(
                    {
                        "marketplace": "target",
                        "category": "lighting",
                        "product_url": "https://www.target.com/p/product-three/-/A-3",
                        "title_hint": "Three",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = ProcessedManifest(
        raw_manifest_path=str(tmp_path / "raw_manifest.json"),
        selected_products_path=str(selected_path),
        output_dir=str(tmp_path / "processed"),
        product_count=3,
        min_review_count_threshold=5,
        entries=[],
    )

    validation = validate_q1_artifacts(
        processed_manifest=manifest,
        selected_products_path=selected_path,
        min_review_count=5,
    )

    assert not validation.passed
    assert any("distinct categories" in issue for issue in validation.issues)


def test_build_processed_corpus_flags_empty_description(tmp_path: Path) -> None:
    """An empty cleaned description should fail Q1 validation."""
    raw_dir, selected_path = _write_raw_fixture(
        tmp_path=tmp_path,
        empty_description_slug="product-two-2",
    )

    result = build_processed_corpus(
        raw_dir=raw_dir,
        output_dir=tmp_path / "processed",
        selected_products_path=selected_path,
        docs_root=tmp_path / "docs",
        min_review_count=2,
    )

    assert not result.q1_validation.passed
    assert any("empty cleaned description" in issue for issue in result.q1_validation.issues)


def test_build_processed_corpus_flags_min_review_threshold(tmp_path: Path) -> None:
    """Q1 validation should fail when a product falls below the cleaned review threshold."""
    raw_dir, selected_path = _write_raw_fixture(
        tmp_path=tmp_path,
        low_review_slug="product-three-3",
    )

    result = build_processed_corpus(
        raw_dir=raw_dir,
        output_dir=tmp_path / "processed",
        selected_products_path=selected_path,
        docs_root=tmp_path / "docs",
        min_review_count=3,
    )

    assert not result.q1_validation.passed
    assert any("below threshold 3" in issue for issue in result.q1_validation.issues)


def _write_raw_fixture(
    *,
    tmp_path: Path,
    empty_description_slug: str | None = None,
    low_review_slug: str | None = None,
) -> tuple[Path, Path]:
    """Create a minimal raw artifact tree for corpus-building tests."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    selected_path = tmp_path / "selected_products.jsonl"

    typed_products: list[FixtureProduct] = [
        {
            "slug": "product-one-1",
            "id": "1",
            "category": "audio",
            "description": "Long clean description for product one.",
            "review_count": 3,
        },
        {
            "slug": "product-two-2",
            "id": "2",
            "category": "lighting",
            "description": (
                ""
                if empty_description_slug == "product-two-2"
                else "Useful lamp description."
            ),
            "review_count": 3,
        },
        {
            "slug": "product-three-3",
            "id": "3",
            "category": "home-appliance",
            "description": "Air purifier description with enough detail.",
            "review_count": 1 if low_review_slug == "product-three-3" else 3,
        },
    ]

    selected_lines: list[str] = []
    manifest_entries: list[dict[str, object]] = []
    for product in typed_products:
        product_dir = raw_dir / product["slug"]
        images_dir = product_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        _write_test_image(images_dir / "reference_01.png")
        (product_dir / "product_meta.json").write_text(
            json.dumps(
                {
                    "product_id": product["id"],
                    "title": f"Product {product['id']}",
                    "category": product["category"],
                    "marketplace": "target",
                    "source_url": f"https://www.target.com/p/{product['slug']}/-/A-{product['id']}",
                    "rating": 4.5,
                    "visible_review_count": product["review_count"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (product_dir / "description.json").write_text(
            json.dumps(
                {
                    "product_id": product["id"],
                    "title": f"Product {product['id']}",
                    "category": product["category"],
                    "description_text": product["description"],
                    "bullet_text": ["<B>Material:</B> Metal"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        review_lines = []
        for index in range(product["review_count"]):
            review_lines.append(
                ReviewRecord(
                    review_id=f"{product['id']}-{index}",
                    product_id=str(product["id"]),
                    title=f"Review {index}",
                    body="This is a sufficiently detailed review body for corpus cleaning.",
                    source_url=HTTP_URL_ADAPTER.validate_python(
                        f"https://www.target.com/p/{product['slug']}/-/A-{product['id']}"
                    ),
                ).model_dump_json()
            )
        (product_dir / "reviews.jsonl").write_text(
            "\n".join(review_lines) + ("\n" if review_lines else ""),
            encoding="utf-8",
        )
        (product_dir / "scrape_report.json").write_text(
            json.dumps(
                {
                    "product_slug": product["slug"],
                    "product_id": product["id"],
                    "source_url": f"https://www.target.com/p/{product['slug']}/-/A-{product['id']}",
                    "category": product["category"],
                    "marketplace": "target",
                    "title": f"Product {product['id']}",
                    "status": "completed",
                    "artifact_completeness": {
                        "product_meta": True,
                        "description": True,
                        "reviews": True,
                        "images": True,
                        "raw_html": True,
                        "scrape_report": True,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raw_html_dir = product_dir / "raw_html"
        raw_html_dir.mkdir(exist_ok=True)
        (raw_html_dir / "product_page.html").write_text("<html></html>", encoding="utf-8")

        selected_lines.append(
            json.dumps(
                {
                    "marketplace": "target",
                    "category": product["category"],
                    "product_url": f"https://www.target.com/p/{product['slug']}/-/A-{product['id']}",
                    "title_hint": f"Product {product['id']}",
                }
            )
        )
        manifest_entries.append(
            {
                "product_slug": product["slug"],
                "product_id": product["id"],
                "source_url": f"https://www.target.com/p/{product['slug']}/-/A-{product['id']}",
                "category": product["category"],
                "artifact_completeness": {
                    "product_meta": True,
                    "description": True,
                    "reviews": True,
                    "images": True,
                    "raw_html": True,
                    "scrape_report": True,
                },
                "pages_fetched": 2,
                "review_count": product["review_count"],
                "image_count": 1,
                "status": "completed",
            }
        )

    selected_path.write_text("\n".join(selected_lines) + "\n", encoding="utf-8")
    (raw_dir / "raw_manifest.json").write_text(
        json.dumps(
            {
                "raw_manifest_path": str(raw_dir / "raw_manifest.json"),
                "input_path": str(selected_path),
                "output_dir": str(raw_dir),
                "product_count": 3,
                "entries": manifest_entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return raw_dir, selected_path


def _write_test_image(path: Path) -> None:
    """Write a tiny valid local image."""
    image = Image.new("RGB", (2, 2), color=(255, 255, 255))
    image.save(path, format="PNG")
