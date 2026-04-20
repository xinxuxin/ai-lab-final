"""Q3 evaluation pipeline tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image

from app.services.evaluation import evaluate_images_for_product


def test_evaluate_images_writes_artifacts(tmp_path: Path) -> None:
    """Evaluation should write score sheet, summary, and panel manifest."""
    product_slug = "sample-product"
    raw_dir = tmp_path / "data" / "raw" / product_slug
    generated_dir = tmp_path / "outputs" / "generated_images" / product_slug / "openai"
    (raw_dir / "images").mkdir(parents=True, exist_ok=True)
    (generated_dir / "pilot").mkdir(parents=True, exist_ok=True)
    (generated_dir / "final").mkdir(parents=True, exist_ok=True)

    reference_image = raw_dir / "images" / "reference_01.png"
    final_image = generated_dir / "final" / "image_01.png"
    _write_png(reference_image)
    _write_png(final_image)

    (raw_dir / "product_meta.json").write_text(
        json.dumps({"title": "Sample Product", "category": "home"}, indent=2),
        encoding="utf-8",
    )
    (generated_dir / "generation_manifest.json").write_text(
        json.dumps(
            {
                "product_slug": product_slug,
                "product_id": "1",
                "product_name": "Sample Product",
                "provider": "openai",
                "model_name": "openai",
                "output_dir": str(generated_dir),
                "prompt_versions_path": str(generated_dir / "prompt_versions.json"),
                "pilot_generation": {
                    "generation_id": "g1",
                    "product_id": "1",
                    "provider": "openai",
                    "model_name": "openai",
                    "stage": "pilot",
                    "prompt_version_id": "pilot-1",
                    "prompt_source_mode": "baseline_description_only",
                    "output_paths": [],
                    "images": [],
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
                            "sha256": "abc",
                            "width": 4,
                            "height": 4,
                            "byte_size": len(final_image.read_bytes()),
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

    result = evaluate_images_for_product(
        product_slug=product_slug,
        raw_root=tmp_path / "data" / "raw",
        generated_root=tmp_path / "outputs" / "generated_images",
        outputs_root=tmp_path / "outputs" / "evaluations",
        vision_assisted=False,
    )

    assert result.human_score_sheet_path.exists()
    assert result.comparison_panels_manifest_path.exists()
    assert result.summary_path.exists()
    assert result.summary["status"] == "human_scoring_ready"


def _write_png(path: Path) -> None:
    """Write a tiny valid PNG image."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())
