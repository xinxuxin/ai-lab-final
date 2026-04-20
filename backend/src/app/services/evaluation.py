"""Q3 evaluation pipeline for comparison analytics and report artifacts."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError, field_validator

from app.config.settings import Settings, get_settings
from app.imagegen.base import ImageGenerationError
from app.llm import Q2_SYSTEM_PROMPT, OpenAITextAnalysisClient
from app.llm.client import LLMClientError
from app.models.schemas import GenerationManifest
from app.utils.artifacts import DATA_DIR, OUTPUTS_DIR, ensure_project_dirs

RAW_DIR = DATA_DIR / "raw"
GENERATED_DIR = OUTPUTS_DIR / "generated_images"
EVALUATIONS_DIR = OUTPUTS_DIR / "evaluations"

RUBRIC_DIMENSIONS = [
    "color_accuracy",
    "material_finish_accuracy",
    "shape_silhouette_accuracy",
    "component_completeness",
    "size_proportion_impression",
    "overall_recognizability",
]


class VisionDimensionScores(BaseModel):
    """Per-dimension evaluation scores."""

    color_accuracy: float
    material_finish_accuracy: float
    shape_silhouette_accuracy: float
    component_completeness: float
    size_proportion_impression: float
    overall_recognizability: float


class VisionPanelEvaluation(BaseModel):
    """One vision-assisted comparison result."""

    panel_id: str
    provider: str
    scores: VisionDimensionScores
    worked: list[str]
    failed: list[str]
    summary: str

    @field_validator("worked", "failed", mode="before")
    @classmethod
    def _normalize_issue_lists(cls, value: Any) -> list[str]:
        """Accept either a plain list or a rubric-keyed dict from the model."""
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, dict):
            normalized: list[str] = []
            for key, item in value.items():
                if isinstance(item, bool):
                    if item:
                        normalized.append(str(key))
                    continue
                text = str(item).strip()
                if text:
                    normalized.append(f"{key}: {text}")
            return normalized
        return []


class EvaluationError(RuntimeError):
    """Raised when evaluation artifacts cannot be built."""


@dataclass(slots=True)
class EvaluateImagesResult:
    """Return value for one evaluation run."""

    product_slug: str
    evaluation_dir: Path
    human_score_sheet_path: Path
    vision_assisted_eval_path: Path
    summary_path: Path
    comparison_panels_manifest_path: Path
    summary: dict[str, Any]


def evaluate_images_for_product(
    *,
    product_slug: str,
    raw_root: Path | None = None,
    generated_root: Path | None = None,
    outputs_root: Path | None = None,
    settings: Settings | None = None,
    vision_assisted: bool = False,
    llm_client: OpenAITextAnalysisClient | None = None,
) -> EvaluateImagesResult:
    """Build durable evaluation artifacts for one product slug."""
    ensure_project_dirs()
    settings = settings or get_settings()
    resolved_raw_root = raw_root or RAW_DIR
    resolved_generated_root = generated_root or GENERATED_DIR
    resolved_outputs_root = outputs_root or EVALUATIONS_DIR

    raw_product_dir = resolved_raw_root / product_slug
    if not raw_product_dir.exists():
        raise EvaluationError(f"Raw product directory is missing: {raw_product_dir}")

    evaluation_dir = resolved_outputs_root / product_slug
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    reference_images = sorted((raw_product_dir / "images").glob("*"))
    reference_images = [path for path in reference_images if path.is_file()]
    product_meta = json.loads((raw_product_dir / "product_meta.json").read_text(encoding="utf-8"))

    model_manifests = _load_generation_manifests(
        product_slug=product_slug,
        generated_root=resolved_generated_root,
    )
    panel_manifest = _build_comparison_panel_manifest(
        product_slug=product_slug,
        reference_images=reference_images,
        model_manifests=model_manifests,
    )
    comparison_panels_manifest_path = evaluation_dir / "comparison_panels_manifest.json"
    comparison_panels_manifest_path.write_text(
        json.dumps(panel_manifest, indent=2),
        encoding="utf-8",
    )

    human_score_sheet_path = evaluation_dir / "human_score_sheet.csv"
    _write_human_score_sheet(
        output_path=human_score_sheet_path,
        product_slug=product_slug,
        panel_manifest=panel_manifest,
    )

    vision_assisted_eval_path = evaluation_dir / "vision_assisted_eval.json"
    vision_payload: dict[str, Any]
    if vision_assisted and panel_manifest["panels"]:
        vision_payload = _run_vision_assisted_evaluation(
            product_slug=product_slug,
            panel_manifest=panel_manifest,
            settings=settings,
            llm_client=llm_client,
        )
    else:
        reason = "vision_assisted_disabled"
        if not panel_manifest["panels"]:
            reason = "no_generated_images_available"
        vision_payload = {
            "status": "not_run",
            "reason": reason,
            "evaluations": [],
            "aggregate_scores": {},
        }
    vision_assisted_eval_path.write_text(
        json.dumps(vision_payload, indent=2),
        encoding="utf-8",
    )

    summary = _build_evaluation_summary(
        product_slug=product_slug,
        product_meta=product_meta,
        panel_manifest=panel_manifest,
        vision_payload=vision_payload,
    )
    summary_path = evaluation_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return EvaluateImagesResult(
        product_slug=product_slug,
        evaluation_dir=evaluation_dir,
        human_score_sheet_path=human_score_sheet_path,
        vision_assisted_eval_path=vision_assisted_eval_path,
        summary_path=summary_path,
        comparison_panels_manifest_path=comparison_panels_manifest_path,
        summary=summary,
    )


def list_evaluation_ready_products(
    *,
    raw_root: Path | None = None,
) -> list[str]:
    """Return product slugs that have raw artifacts available."""
    resolved_raw_root = raw_root or RAW_DIR
    if not resolved_raw_root.exists():
        return []
    return sorted(
        child.name
        for child in resolved_raw_root.iterdir()
        if child.is_dir() and (child / "product_meta.json").exists()
    )


def _load_generation_manifests(
    *,
    product_slug: str,
    generated_root: Path,
) -> dict[str, GenerationManifest]:
    """Load available generation manifests for openai and stability."""
    manifests: dict[str, GenerationManifest] = {}
    for provider in ("openai", "stability"):
        manifest_path = generated_root / product_slug / provider / "generation_manifest.json"
        if manifest_path.exists():
            manifests[provider] = GenerationManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
    return manifests


def _build_comparison_panel_manifest(
    *,
    product_slug: str,
    reference_images: list[Path],
    model_manifests: dict[str, GenerationManifest],
) -> dict[str, Any]:
    """Create side-by-side comparison metadata for reference and generated images."""
    panels: list[dict[str, Any]] = []
    available_models: list[str] = []
    missing_models = [
        provider for provider in ("openai", "stability") if provider not in model_manifests
    ]
    for provider, manifest in model_manifests.items():
        available_models.append(provider)
        generated_images = manifest.final_generation.images
        for index, generated_image in enumerate(generated_images, start=1):
            if not reference_images:
                continue
            reference_image = reference_images[(index - 1) % len(reference_images)]
            panels.append(
                {
                    "panel_id": f"{product_slug}-{provider}-{index:02d}",
                    "provider": provider,
                    "model_name": manifest.model_name,
                    "reference_image_path": str(reference_image),
                    "generated_image_path": generated_image.local_path,
                    "generated_image_sha256": generated_image.sha256,
                    "prompt_source_mode": manifest.final_generation.prompt_source_mode,
                    "stage": "final",
                }
            )
    return {
        "product_slug": product_slug,
        "reference_image_count": len(reference_images),
        "available_models": available_models,
        "missing_models": missing_models,
        "panels": panels,
    }


def _write_human_score_sheet(
    *,
    output_path: Path,
    product_slug: str,
    panel_manifest: dict[str, Any],
) -> None:
    """Write a human-scoring CSV template for manual evaluation."""
    fieldnames = [
        "product_slug",
        "panel_id",
        "provider",
        "reference_image_path",
        "generated_image_path",
        *RUBRIC_DIMENSIONS,
        "worked",
        "failed",
        "notes",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for panel in panel_manifest["panels"]:
            writer.writerow(
                {
                    "product_slug": product_slug,
                    "panel_id": panel["panel_id"],
                    "provider": panel["provider"],
                    "reference_image_path": panel["reference_image_path"],
                    "generated_image_path": panel["generated_image_path"],
                    "worked": "",
                    "failed": "",
                    "notes": "",
                }
            )


def _run_vision_assisted_evaluation(
    *,
    product_slug: str,
    panel_manifest: dict[str, Any],
    settings: Settings,
    llm_client: OpenAITextAnalysisClient | None,
) -> dict[str, Any]:
    """Run optional vision-assisted scoring through the OpenAI API."""
    prompt_path = OUTPUTS_DIR.parent / "prompts" / "evaluation" / "vision_assisted_eval.md"
    prompt_template = prompt_path.read_text(encoding="utf-8")
    owns_client = llm_client is None
    client = llm_client or OpenAITextAnalysisClient(settings=settings)
    try:
        evaluations: list[VisionPanelEvaluation] = []
        for panel in panel_manifest["panels"]:
            panel_id = str(panel["panel_id"])
            provider = str(panel["provider"])
            user_prompt = (
                f"{prompt_template}\n\n"
                f"panel_id: {panel_id}\n"
                f"provider: {provider}\n"
                "The first image is the real product reference. "
                "The second image is the generated candidate."
            )
            completion = client.complete_json_with_images(
                system_prompt=Q2_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                image_paths=[
                    Path(str(panel["reference_image_path"])),
                    Path(str(panel["generated_image_path"])),
                ],
            )
            payload = json.loads(completion.text)
            evaluations.append(VisionPanelEvaluation.model_validate(payload))
            time.sleep(0.75)
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
        ImageGenerationError,
        LLMClientError,
        httpx.HTTPError,
    ) as exc:
        return {
            "status": "failed",
            "reason": str(exc),
            "evaluations": [],
            "aggregate_scores": {},
        }
    finally:
        if owns_client:
            client.close()

    aggregate_scores: dict[str, dict[str, float]] = {}
    for provider in ("openai", "stability"):
        provider_evals = [item for item in evaluations if item.provider == provider]
        if not provider_evals:
            continue
        aggregate_scores[provider] = {
            dimension: round(
                mean(getattr(item.scores, dimension) for item in provider_evals),
                2,
            )
            for dimension in RUBRIC_DIMENSIONS
        }

    return {
        "status": "completed",
        "product_slug": product_slug,
        "evaluations": [item.model_dump(mode="json") for item in evaluations],
        "aggregate_scores": aggregate_scores,
    }


def _build_evaluation_summary(
    *,
    product_slug: str,
    product_meta: dict[str, Any],
    panel_manifest: dict[str, Any],
    vision_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build a UI-friendly evaluation summary."""
    missing_models = panel_manifest["missing_models"]
    available_models = panel_manifest["available_models"]
    panel_count = len(panel_manifest["panels"])
    if panel_count == 0:
        status = "missing_generated_images"
        summary_text = (
            "Reference product images are available, but no generated image manifests were found "
            "for comparison yet."
        )
    elif vision_payload["status"] == "completed":
        status = "vision_assisted_complete"
        summary_text = (
            "Vision-assisted evaluation completed. Review per-dimension provider averages "
            "and panel-level strengths versus failures."
        )
    else:
        status = "human_scoring_ready"
        summary_text = (
            "Comparison panels and the human scoring sheet were generated. "
            "Vision-assisted scoring was not run."
        )

    return {
        "status": status,
        "product_slug": product_slug,
        "product_name": product_meta.get("title", product_slug),
        "category": product_meta.get("category", "unknown"),
        "reference_image_count": panel_manifest["reference_image_count"],
        "comparison_panel_count": panel_count,
        "available_models": available_models,
        "missing_models": missing_models,
        "vision_assisted_status": vision_payload["status"],
        "aggregate_scores": vision_payload.get("aggregate_scores", {}),
        "summary_text": summary_text,
    }
