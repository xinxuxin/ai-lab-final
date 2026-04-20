"""Verification and submission-package tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image
from pytest import MonkeyPatch

from app.services.verification import build_submission_package, verify_repository


def test_verify_repository_full_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Full verification should pass for a complete artifact fixture."""
    fixture = _write_verification_fixture(tmp_path)
    _patch_verification_roots(monkeypatch, fixture)

    result = verify_repository(
        stage="full",
        processed_dir=fixture["processed_dir"],
        selected_products_path=fixture["selected_products_path"],
        frontend_root=fixture["frontend_root"],
        run_frontend_build=False,
    )

    assert result.passed is True
    assert result.summary["checks"]["q1"]["passed"] is True
    assert result.summary["checks"]["q2"]["passed"] is True
    assert result.summary["checks"]["q3"]["passed"] is True
    assert result.summary["checks"]["q4"]["passed"] is True


def test_verify_repository_q2_fails_when_profile_missing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Q2 verification should fail clearly when a required profile is missing."""
    fixture = _write_verification_fixture(tmp_path)
    _patch_verification_roots(monkeypatch, fixture)

    missing_path = (
        fixture["outputs_dir"]
        / "visual_profiles"
        / "sample-product-1"
        / "review_informed_rag.json"
    )
    missing_path.unlink()

    result = verify_repository(
        stage="q2",
        processed_dir=fixture["processed_dir"],
        selected_products_path=fixture["selected_products_path"],
        frontend_root=fixture["frontend_root"],
        run_frontend_build=False,
    )

    assert result.passed is False
    assert any("review-informed profile is missing" in issue for issue in result.summary["issues"])


def test_build_submission_package_copies_expected_paths(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Submission package builder should copy the required repository sections."""
    repo_root = tmp_path / "repo"
    _write_minimal_repo_for_package(repo_root)
    monkeypatch.setattr("app.services.verification.REPO_ROOT", repo_root)

    result = build_submission_package(output_dir=tmp_path / "submission_package")

    assert (result.output_dir / "README.md").exists()
    assert (result.output_dir / "backend").exists()
    assert (result.output_dir / "frontend").exists()
    assert result.manifest_path.exists()


def _patch_verification_roots(monkeypatch: MonkeyPatch, fixture: dict[str, Path]) -> None:
    monkeypatch.setattr("app.services.verification.DATA_DIR", fixture["data_dir"])
    monkeypatch.setattr("app.services.verification.OUTPUTS_DIR", fixture["outputs_dir"])
    monkeypatch.setattr("app.services.verification.PROMPTS_DIR", fixture["prompts_dir"])
    monkeypatch.setattr("app.services.verification.DOCS_DIR", fixture["docs_dir"])
    monkeypatch.setattr("app.services.verification.REPO_ROOT", fixture["repo_root"])
    monkeypatch.setattr(
        "app.services.verification.WORKFLOW_RUNS_DIR",
        fixture["outputs_dir"] / "workflow_runs",
    )
    monkeypatch.setattr(
        "app.workflow.orchestrator.WORKFLOW_RUNS_DIR",
        fixture["outputs_dir"] / "workflow_runs",
    )


def _write_verification_fixture(tmp_path: Path) -> dict[str, Path]:
    repo_root = tmp_path / "repo"
    data_dir = repo_root / "data"
    processed_dir = data_dir / "processed"
    outputs_dir = repo_root / "outputs"
    prompts_dir = repo_root / "prompts"
    docs_dir = repo_root / "docs"
    frontend_root = repo_root / "frontend"
    selected_products_path = data_dir / "selected_products.jsonl"
    (frontend_root / "src" / "pages").mkdir(parents=True, exist_ok=True)
    (prompts_dir / "q2").mkdir(parents=True, exist_ok=True)
    (docs_dir).mkdir(parents=True, exist_ok=True)
    (outputs_dir / "workflow_runs" / "run-1").mkdir(parents=True, exist_ok=True)

    for filename, api_call in {
        "ProductsPage.tsx": "api.getProducts();",
        "ReviewsPage.tsx": "api.getReviews('sample-product-1');",
        "ProfilesPage.tsx": "api.getProfiles('sample-product-1');",
        "GenerationPage.tsx": "api.getGeneration('sample-product-1');",
        "ComparisonPage.tsx": "api.getEvaluation('sample-product-1');",
        "WorkflowPage.tsx": "api.getWorkflow();",
    }.items():
        (frontend_root / "src" / "pages" / filename).write_text(api_call + "\n", encoding="utf-8")
    for prompt_name in [
        "aspect_evidence_extraction.md",
        "conflict_resolution.md",
        "final_visual_profile_synthesis.md",
    ]:
        (prompts_dir / "q2" / prompt_name).write_text("prompt", encoding="utf-8")
    (docs_dir / "agentic_workflow.md").write_text("# workflow", encoding="utf-8")
    (outputs_dir / "workflow_runs" / "run-1" / "trace.json").write_text(
        json.dumps(
            [
                {
                    "trace_id": "data_curation-sample-product-1",
                    "stage": "data_curation",
                    "status": "completed",
                    "started_at": "2026-04-20T12:00:00Z",
                    "finished_at": "2026-04-20T12:00:01Z",
                    "inputs": {"product_slug": "sample-product-1"},
                    "outputs": {"processed_product_dir": "data/processed/sample-product-1"},
                    "notes": ["DataCurationAgent"],
                }
            ]
        ),
        encoding="utf-8",
    )
    (outputs_dir / "workflow_runs" / "run-1" / "stage_status.json").write_text(
        json.dumps(
            [
                {
                    "stage_key": "data_curation",
                    "label": "Q1 Data Curation",
                    "agent_name": "DataCurationAgent",
                    "status": "completed",
                    "completed_count": 3,
                    "total_count": 3,
                    "products": ["sample-product-1", "sample-product-2", "sample-product-3"],
                    "detail": "Completed.",
                }
            ]
        ),
        encoding="utf-8",
    )
    (outputs_dir / "workflow_runs" / "run-1" / "artifact_links.json").write_text(
        json.dumps(
            [
                {
                    "from_stage": "data_curation",
                    "to_stage": "retrieval",
                    "label": "handoff",
                    "product_slug": "sample-product-1",
                    "artifact_paths": ["data/processed/sample-product-1/product.json"],
                }
            ]
        ),
        encoding="utf-8",
    )

    selected_lines: list[str] = []
    manifest_entries: list[dict[str, object]] = []
    categories = ["lighting", "audio", "home-appliance"]
    for index in range(1, 4):
        slug = f"sample-product-{index}"
        category = categories[index - 1]
        selected_lines.append(
            json.dumps(
                {
                    "marketplace": "target",
                    "category": category,
                    "product_url": f"https://example.com/{slug}",
                    "title_hint": f"Sample Product {index}",
                    "popularity_hint": "medium",
                    "rationale": "fixture",
                }
            )
        )
        product_dir = processed_dir / slug
        raw_dir = data_dir / "raw" / slug
        profile_dir = outputs_dir / "visual_profiles" / slug
        eval_dir = outputs_dir / "evaluations" / slug
        product_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "images").mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        eval_dir.mkdir(parents=True, exist_ok=True)

        description_path = product_dir / "description_clean.txt"
        reviews_path = product_dir / "reviews_clean.jsonl"
        image_manifest_path = product_dir / "image_manifest.json"
        stats_path = product_dir / "review_stats.json"
        description_path.write_text("Clean description", encoding="utf-8")
        reviews_path.write_text(
            "\n".join(
                json.dumps(
                    {
                        "review_id": f"r{review_index}",
                        "product_id": str(index),
                        "body": "This product has a grounded and detailed review body for testing.",
                        "source_url": f"https://example.com/{slug}",
                    }
                )
                for review_index in range(6)
            ),
            encoding="utf-8",
        )
        stats_path.write_text(
            json.dumps({"cleaned_review_count": 6, "visible_review_count": 10}),
            encoding="utf-8",
        )
        reference_image = raw_dir / "images" / "reference_01.png"
        _write_png(reference_image)
        image_manifest_path.write_text(
            json.dumps(
                [
                    {
                        "filename": "reference_01.png",
                        "local_path": str(reference_image),
                        "source": "reference",
                        "valid": True,
                    }
                ]
            ),
            encoding="utf-8",
        )
        (raw_dir / "product_meta.json").write_text(
            json.dumps({"title": f"Sample Product {index}", "category": category}),
            encoding="utf-8",
        )
        (raw_dir / "reviews.jsonl").write_text("{}", encoding="utf-8")

        (product_dir / "product.json").write_text(
            json.dumps(
                {
                    "product_slug": slug,
                    "product_id": str(index),
                    "title": f"Sample Product {index}",
                    "category": category,
                    "selected_category": category,
                    "marketplace": "target",
                    "source_url": f"https://example.com/{slug}",
                    "description_char_count": 20,
                    "spec_bullets": [],
                    "visible_review_count": 10,
                    "cleaned_review_count": 6,
                    "valid_image_count": 1,
                    "stats_path": str(stats_path),
                    "image_manifest_path": str(image_manifest_path),
                    "reviews_path": str(reviews_path),
                    "description_path": str(description_path),
                }
            ),
            encoding="utf-8",
        )

        profile_payload = {
            "product_name": f"Sample Product {index}",
            "category": category,
            "high_confidence_visual_attributes": [],
            "low_confidence_or_conflicting_attributes": [],
            "common_mismatches_between_expectation_and_reality": [],
            "prompt_ready_description": "A realistic studio product image.",
            "negative_constraints": ["avoid accessories"],
        }
        (profile_dir / "baseline_description_only.json").write_text(
            json.dumps(profile_payload),
            encoding="utf-8",
        )
        (profile_dir / "review_informed_rag.json").write_text(
            json.dumps(profile_payload),
            encoding="utf-8",
        )
        (profile_dir / "retrieval_evidence.json").write_text(
            json.dumps({"review_informed_rag": {"appearance_and_shape": []}}),
            encoding="utf-8",
        )
        for provider in ("openai", "stability"):
            provider_dir = outputs_dir / "generated_images" / slug / provider
            (provider_dir / "pilot").mkdir(parents=True, exist_ok=True)
            (provider_dir / "final").mkdir(parents=True, exist_ok=True)
            _write_png(provider_dir / "pilot" / "image_01.png")
            final_images = []
            for image_index in range(1, 4):
                image_path = provider_dir / "final" / f"image_0{image_index}.png"
                _write_png(image_path)
                final_images.append(
                    {
                        "filename": image_path.name,
                        "local_path": str(image_path),
                        "sha256": f"{provider}-{image_index}",
                        "width": 4,
                        "height": 4,
                        "byte_size": len(image_path.read_bytes()),
                        "content_type": "image/png",
                        "metadata": {},
                    }
                )
            (provider_dir / "prompt_versions.json").write_text(
                json.dumps({"versions": []}),
                encoding="utf-8",
            )
            (provider_dir / "generation_manifest.json").write_text(
                json.dumps(
                    {
                        "product_slug": slug,
                        "product_id": str(index),
                        "product_name": f"Sample Product {index}",
                        "provider": provider,
                        "model_name": provider,
                        "output_dir": str(provider_dir),
                        "prompt_versions_path": str(provider_dir / "prompt_versions.json"),
                        "pilot_generation": {
                            "generation_id": "pilot",
                            "product_id": str(index),
                            "provider": provider,
                            "model_name": provider,
                            "stage": "pilot",
                            "prompt_version_id": "pilot",
                            "prompt_source_mode": "baseline_description_only",
                            "output_paths": [str(provider_dir / "pilot" / "image_01.png")],
                            "images": [
                                {
                                    "filename": "image_01.png",
                                    "local_path": str(provider_dir / "pilot" / "image_01.png"),
                                    "sha256": "pilot",
                                    "width": 4,
                                    "height": 4,
                                    "byte_size": len((provider_dir / "pilot" / "image_01.png").read_bytes()),
                                    "content_type": "image/png",
                                    "metadata": {},
                                }
                            ],
                            "status": "completed",
                            "metadata": {},
                        },
                        "final_generation": {
                            "generation_id": "final",
                            "product_id": str(index),
                            "provider": provider,
                            "model_name": provider,
                            "stage": "final",
                            "prompt_version_id": "final",
                            "prompt_source_mode": "review_informed_rag",
                            "output_paths": [image["local_path"] for image in final_images],
                            "images": final_images,
                            "status": "completed",
                            "metadata": {},
                        },
                        "status": "completed",
                        "reused_existing": True,
                        "notes": [],
                    }
                ),
                encoding="utf-8",
            )
        (eval_dir / "summary.json").write_text(
            json.dumps({"status": "human_scoring_ready", "comparison_panel_count": 6}),
            encoding="utf-8",
        )
        manifest_entries.append(
            {
                "product_slug": slug,
                "product_id": str(index),
                "title": f"Sample Product {index}",
                "category": category,
                "source_url": f"https://example.com/{slug}",
                "processed_dir": str(product_dir),
                "cleaned_review_count": 6,
                "valid_image_count": 1,
                "description_char_count": 20,
                "passes_q1": True,
                "issues": [],
            }
        )

    selected_products_path.parent.mkdir(parents=True, exist_ok=True)
    selected_products_path.write_text("\n".join(selected_lines) + "\n", encoding="utf-8")
    (processed_dir / "manifest.json").write_text(
        json.dumps(
            {
                "raw_manifest_path": str(data_dir / "raw" / "raw_manifest.json"),
                "selected_products_path": str(selected_products_path),
                "output_dir": str(processed_dir),
                "product_count": 3,
                "min_review_count_threshold": 5,
                "entries": manifest_entries,
            }
        ),
        encoding="utf-8",
    )
    return {
        "repo_root": repo_root,
        "data_dir": data_dir,
        "processed_dir": processed_dir,
        "outputs_dir": outputs_dir,
        "prompts_dir": prompts_dir,
        "docs_dir": docs_dir,
        "frontend_root": frontend_root,
        "selected_products_path": selected_products_path,
    }


def _write_minimal_repo_for_package(repo_root: Path) -> None:
    for relative in [
        "backend",
        "frontend",
        "configs",
        "data",
        "outputs",
        "prompts",
        "docs",
        "scripts",
    ]:
        (repo_root / relative).mkdir(parents=True, exist_ok=True)
    (repo_root / "README.md").write_text("# repo", encoding="utf-8")
    (repo_root / ".env.example").write_text("OPENAI_API_KEY=\n", encoding="utf-8")
    (repo_root / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")


def _write_png(path: Path) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(buffer, format="PNG")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buffer.getvalue())
