"""API tests for artifact-backed endpoints."""

from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from pytest import MonkeyPatch

from app.main import app


def test_health_endpoint() -> None:
    """Health endpoint should respond with status ok."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_artifact_backed_endpoints(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Products, profiles, generation, evaluation, and workflow endpoints should render."""
    _write_api_fixture(tmp_path)

    monkeypatch.setattr("app.services.dashboard_data.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("app.services.dashboard_data.RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(
        "app.services.dashboard_data.PROCESSED_DIR", tmp_path / "data" / "processed"
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.SELECTED_PRODUCTS_PATH",
        tmp_path / "data" / "selected_products.jsonl",
    )
    monkeypatch.setattr("app.services.dashboard_data.OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(
        "app.services.dashboard_data.VISUAL_PROFILES_DIR",
        tmp_path / "outputs" / "visual_profiles",
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.GENERATED_IMAGES_DIR",
        tmp_path / "outputs" / "generated_images",
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.EVALUATIONS_DIR",
        tmp_path / "outputs" / "evaluations",
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.artifact_api_url", lambda path: f"/api/assets/{path.name}"
    )
    monkeypatch.setattr("app.api.routes.REPO_ROOT", tmp_path)
    monkeypatch.setattr("app.api.routes.is_repo_artifact_path", lambda path: True)

    client = TestClient(app)

    products = client.get("/api/products")
    assert products.status_code == 200
    assert products.json()["items"][0]["slug"] == "sample-product"

    reviews = client.get("/api/reviews/sample-product/stats")
    assert reviews.status_code == 200
    assert reviews.json()["stats"]["cleaned_review_count"] == 2

    profiles = client.get("/api/profiles/sample-product")
    assert profiles.status_code == 200
    assert profiles.json()["modes"]["baseline_description_only"]["status"] == "available"

    generation = client.get("/api/generation/sample-product")
    assert generation.status_code == 200
    assert generation.json()["models"]["openai"]["status"] == "available"

    evaluation = client.get("/api/evaluation/sample-product")
    assert evaluation.status_code == 200
    assert evaluation.json()["summary"]["status"] == "human_scoring_ready"

    workflow = client.get("/api/workflow/latest")
    assert workflow.status_code == 200
    assert workflow.json()["stages"]


def _write_api_fixture(tmp_path: Path) -> None:
    """Create a minimal artifact tree for API tests."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed" / "sample-product"
    raw_dir = data_dir / "raw" / "sample-product"
    outputs_dir = tmp_path / "outputs"
    profiles_dir = outputs_dir / "visual_profiles" / "sample-product"
    generation_dir = outputs_dir / "generated_images" / "sample-product" / "openai"
    evaluation_dir = outputs_dir / "evaluations" / "sample-product"

    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "images").mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (generation_dir / "pilot").mkdir(parents=True, exist_ok=True)
    (generation_dir / "final").mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "selected_products.jsonl").write_text(
        json.dumps(
            {
                "marketplace": "target",
                "category": "home",
                "product_url": "https://www.target.com/p/sample-product/-/A-1",
                "title_hint": "Sample Product",
                "popularity_hint": "medium",
                "rationale": "Fixture rationale.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "processed" / "manifest.json").write_text(
        json.dumps(
            {
                "raw_manifest_path": str(data_dir / "raw" / "raw_manifest.json"),
                "selected_products_path": str(data_dir / "selected_products.jsonl"),
                "output_dir": str(data_dir / "processed"),
                "product_count": 1,
                "min_review_count_threshold": 5,
                "entries": [
                    {
                        "product_slug": "sample-product",
                        "product_id": "1",
                        "title": "Sample Product",
                        "category": "Air Purifiers",
                        "source_url": "https://www.target.com/p/sample-product/-/A-1",
                        "processed_dir": str(processed_dir),
                        "cleaned_review_count": 2,
                        "valid_image_count": 1,
                        "description_char_count": 100,
                        "passes_q1": True,
                        "issues": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (processed_dir / "product.json").write_text(
        json.dumps(
            {
                "product_slug": "sample-product",
                "product_id": "1",
                "title": "Sample Product",
                "category": "Air Purifiers",
                "selected_category": "home",
                "marketplace": "target",
                "source_url": "https://www.target.com/p/sample-product/-/A-1",
                "description_char_count": 100,
                "spec_bullets": ["Color: White"],
                "visible_review_count": 10,
                "cleaned_review_count": 2,
                "valid_image_count": 1,
                "stats_path": str(processed_dir / "review_stats.json"),
                "image_manifest_path": str(processed_dir / "image_manifest.json"),
                "reviews_path": str(processed_dir / "reviews_clean.jsonl"),
                "description_path": str(processed_dir / "description_clean.txt"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (processed_dir / "description_clean.txt").write_text("Sample description.", encoding="utf-8")
    (processed_dir / "review_stats.json").write_text(
        json.dumps(
            {"cleaned_review_count": 2, "visible_review_count": 10, "rating": 4.5}, indent=2
        ),
        encoding="utf-8",
    )
    (processed_dir / "reviews_clean.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "review_id": "r1",
                        "product_id": "1",
                        "rating": 5,
                        "title": "Great",
                        "body": "Looks clean and compact.",
                        "posted_at": "2026-04-01T00:00:00Z",
                        "source_url": "https://www.target.com/p/sample-product/-/A-1",
                    }
                ),
                json.dumps(
                    {
                        "review_id": "r2",
                        "product_id": "1",
                        "rating": 4,
                        "title": "Good",
                        "body": "Matte white finish.",
                        "posted_at": "2026-04-02T00:00:00Z",
                        "source_url": "https://www.target.com/p/sample-product/-/A-1",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    reference_image = raw_dir / "images" / "reference_01.png"
    _write_png(reference_image)
    (processed_dir / "image_manifest.json").write_text(
        json.dumps(
            [
                {
                    "filename": "reference_01.png",
                    "local_path": str(reference_image),
                    "source": "reference",
                    "valid": True,
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    (raw_dir / "product_meta.json").write_text(
        json.dumps(
            {
                "product_id": "1",
                "title": "Sample Product",
                "category": "home",
                "marketplace": "target",
                "source_url": "https://www.target.com/p/sample-product/-/A-1",
                "rating": 4.5,
                "visible_review_count": 10,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (data_dir / "raw" / "raw_manifest.json").write_text("{}", encoding="utf-8")

    baseline_profile = {
        "product_name": "Sample Product",
        "category": "Air Purifiers",
        "high_confidence_visual_attributes": [],
        "low_confidence_or_conflicting_attributes": [],
        "common_mismatches_between_expectation_and_reality": [],
        "prompt_ready_description": "A compact white purifier.",
        "negative_constraints": ["avoid glossy finish"],
    }
    (profiles_dir / "baseline_description_only.json").write_text(
        json.dumps(baseline_profile, indent=2),
        encoding="utf-8",
    )
    (profiles_dir / "review_informed_rag.json").write_text(
        json.dumps(baseline_profile, indent=2),
        encoding="utf-8",
    )
    (profiles_dir / "retrieval_evidence.json").write_text(
        json.dumps(
            {
                "review_informed_rag": {
                    "color_and_finish": [
                        {
                            "snippet": "matte white finish",
                            "score": 0.9,
                        }
                    ]
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (profiles_dir / "llm_trace.json").write_text(json.dumps({}, indent=2), encoding="utf-8")

    pilot_image = generation_dir / "pilot" / "image_01.png"
    final_image = generation_dir / "final" / "image_01.png"
    _write_png(pilot_image)
    _write_png(final_image)
    (generation_dir / "prompt_versions.json").write_text(
        json.dumps(
            {
                "versions": [
                    {
                        "prompt_version_id": "pilot-1",
                        "strategy": "pilot",
                        "prompt_source_mode": "baseline_description_only",
                        "prompt_text": "Pilot prompt.",
                    },
                    {
                        "prompt_version_id": "final-1",
                        "strategy": "final",
                        "prompt_source_mode": "review_informed_rag",
                        "prompt_text": "Final prompt.",
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (generation_dir / "generation_manifest.json").write_text(
        json.dumps(
            {
                "product_slug": "sample-product",
                "product_id": "1",
                "product_name": "Sample Product",
                "provider": "openai",
                "model_name": "openai",
                "output_dir": str(generation_dir),
                "prompt_versions_path": str(generation_dir / "prompt_versions.json"),
                "pilot_generation": {
                    "generation_id": "g1",
                    "product_id": "1",
                    "provider": "openai",
                    "model_name": "openai",
                    "stage": "pilot",
                    "prompt_version_id": "pilot-1",
                    "prompt_source_mode": "baseline_description_only",
                    "output_paths": [str(pilot_image)],
                    "images": [
                        {
                            "filename": "image_01.png",
                            "local_path": str(pilot_image),
                            "sha256": "abc",
                            "width": 4,
                            "height": 4,
                            "byte_size": 128,
                            "content_type": "image/png",
                            "metadata": {},
                        }
                    ],
                    "status": "completed",
                    "metadata": {},
                },
                "final_generation": {
                    "generation_id": "g2",
                    "product_id": "1",
                    "provider": "openai",
                    "model_name": "openai",
                    "stage": "final",
                    "prompt_version_id": "final-1",
                    "prompt_source_mode": "review_informed_rag",
                    "output_paths": [str(final_image)],
                    "images": [
                        {
                            "filename": "image_01.png",
                            "local_path": str(final_image),
                            "sha256": "def",
                            "width": 4,
                            "height": 4,
                            "byte_size": 128,
                            "content_type": "image/png",
                            "metadata": {},
                        }
                    ],
                    "status": "completed",
                    "metadata": {},
                },
                "status": "completed",
                "reused_existing": False,
                "notes": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (evaluation_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "human_scoring_ready",
                "product_slug": "sample-product",
                "product_name": "Sample Product",
                "category": "home",
                "reference_image_count": 1,
                "comparison_panel_count": 1,
                "available_models": ["openai"],
                "missing_models": ["stability"],
                "vision_assisted_status": "not_run",
                "aggregate_scores": {},
                "summary_text": "Ready for scoring.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "comparison_panels_manifest.json").write_text(
        json.dumps(
            {
                "panels": [
                    {
                        "panel_id": "panel-1",
                        "provider": "openai",
                        "model_name": "openai",
                        "reference_image_path": str(reference_image),
                        "generated_image_path": str(final_image),
                        "prompt_source_mode": "review_informed_rag",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "vision_assisted_eval.json").write_text("{}", encoding="utf-8")
    (evaluation_dir / "human_score_sheet.csv").write_text("panel_id\npanel-1\n", encoding="utf-8")


def _write_png(path: Path) -> None:
    """Write a tiny valid PNG image."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())
