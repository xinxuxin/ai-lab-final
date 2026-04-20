"""Artifact-backed API payload builders for the demo frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.schemas import (
    GenerationManifest,
    ProcessedManifest,
    ProcessedProductRecord,
    VisualProfile,
)
from app.utils.artifacts import (
    DATA_DIR,
    OUTPUTS_DIR,
    artifact_api_url,
    artifact_updated_at,
)

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SELECTED_PRODUCTS_PATH = DATA_DIR / "selected_products.jsonl"
VISUAL_PROFILES_DIR = OUTPUTS_DIR / "visual_profiles"
GENERATED_IMAGES_DIR = OUTPUTS_DIR / "generated_images"
EVALUATIONS_DIR = OUTPUTS_DIR / "evaluations"


def list_products_payload() -> dict[str, Any]:
    """Return the products index used by the frontend."""
    manifest_path = PROCESSED_DIR / "manifest.json"
    if not manifest_path.exists():
        return {
            "status": "missing_artifact",
            "message": "Processed manifest is missing. Run build-corpus first.",
            "items": [],
        }

    processed_manifest = ProcessedManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    selected_records = _load_selected_records()
    items: list[dict[str, Any]] = []
    for entry in processed_manifest.entries:
        product_dir = Path(entry.processed_dir)
        product = ProcessedProductRecord.model_validate_json(
            (product_dir / "product.json").read_text(encoding="utf-8")
        )
        selected_record = selected_records.get(str(product.source_url), {})
        image_manifest = _read_json(Path(product.image_manifest_path), default=[])
        openai_generation_path = (
            GENERATED_IMAGES_DIR / product.product_slug / "openai" / "generation_manifest.json"
        )
        stability_generation_path = (
            GENERATED_IMAGES_DIR / product.product_slug / "stability" / "generation_manifest.json"
        )
        evaluation_path = EVALUATIONS_DIR / product.product_slug / "summary.json"
        reference_images = [
            {
                "filename": image["filename"],
                "url": artifact_api_url(Path(image["local_path"])),
            }
            for image in image_manifest
            if isinstance(image, dict) and image.get("valid")
        ]
        profile_dir = VISUAL_PROFILES_DIR / product.product_slug
        items.append(
            {
                "slug": product.product_slug,
                "title": product.title,
                "category": product.category,
                "selectedCategory": product.selected_category,
                "marketplace": product.marketplace,
                "sourceUrl": str(product.source_url),
                "reviewCount": product.cleaned_review_count,
                "visibleReviewCount": product.visible_review_count,
                "imageCount": product.valid_image_count,
                "descriptionCharCount": product.description_char_count,
                "rationale": selected_record.get("rationale"),
                "popularityHint": selected_record.get("popularity_hint"),
                "primaryImageUrl": reference_images[0]["url"] if reference_images else None,
                "freshness": {
                    "processed": artifact_updated_at(product_dir / "product.json"),
                    "profiles": artifact_updated_at(profile_dir / "review_informed_rag.json"),
                    "generation": artifact_updated_at(openai_generation_path)
                    or artifact_updated_at(stability_generation_path),
                    "evaluation": artifact_updated_at(evaluation_path),
                },
                "artifacts": {
                    "processed": True,
                    "profiles": {
                        "baseline": (profile_dir / "baseline_description_only.json").exists(),
                        "reviewInformed": (profile_dir / "review_informed_rag.json").exists(),
                    },
                    "generation": {
                        "openai": openai_generation_path.exists(),
                        "stability": stability_generation_path.exists(),
                    },
                    "evaluation": evaluation_path.exists(),
                },
            }
        )

    return {
        "status": "ok",
        "generatedAt": artifact_updated_at(manifest_path),
        "items": items,
    }


def product_detail_payload(slug: str) -> dict[str, Any]:
    """Return detail payload for one selected product."""
    product = _load_product(slug)
    raw_meta_path = RAW_DIR / slug / "product_meta.json"
    description_path = PROCESSED_DIR / slug / "description_clean.txt"
    image_manifest_path = PROCESSED_DIR / slug / "image_manifest.json"
    selected_records = _load_selected_records()
    selected_record = selected_records.get(str(product.source_url), {})
    raw_meta = _read_json(raw_meta_path, default={})
    image_manifest = _read_json(image_manifest_path, default=[])

    reference_images = [
        {
            "filename": image["filename"],
            "url": artifact_api_url(Path(image["local_path"])),
        }
        for image in image_manifest
        if isinstance(image, dict) and image.get("valid")
    ]
    return {
        "status": "ok",
        "product": {
            "slug": product.product_slug,
            "title": product.title,
            "category": product.category,
            "selectedCategory": product.selected_category,
            "marketplace": product.marketplace,
            "sourceUrl": str(product.source_url),
            "reviewCount": product.cleaned_review_count,
            "visibleReviewCount": product.visible_review_count,
            "imageCount": product.valid_image_count,
            "rating": raw_meta.get("rating"),
            "popularityHint": selected_record.get("popularity_hint"),
            "rationale": selected_record.get("rationale"),
            "descriptionText": description_path.read_text(encoding="utf-8").strip(),
            "specBullets": product.spec_bullets,
            "referenceImages": reference_images,
            "freshness": artifact_updated_at(product_dir(slug) / "product.json"),
        },
    }


def review_stats_payload(slug: str) -> dict[str, Any]:
    """Return review stats, sample reviews, and retrieval evidence."""
    _load_product(slug)
    stats_path = PROCESSED_DIR / slug / "review_stats.json"
    reviews_path = PROCESSED_DIR / slug / "reviews_clean.jsonl"
    retrieval_path = VISUAL_PROFILES_DIR / slug / "retrieval_evidence.json"
    if not stats_path.exists() or not reviews_path.exists():
        return {
            "status": "missing_artifact",
            "message": "Processed review artifacts are missing. Run build-corpus first.",
            "productSlug": slug,
        }

    stats = _read_json(stats_path, default={})
    reviews = _read_jsonl(reviews_path)[:6]
    retrieval = _read_json(retrieval_path, default={})
    evidence_snippets: list[dict[str, Any]] = []
    if isinstance(retrieval, dict):
        for mode, aspects in retrieval.items():
            if not isinstance(aspects, dict):
                continue
            for aspect_key, entries in aspects.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries[:2]:
                    if isinstance(entry, dict):
                        evidence_snippets.append(
                            {
                                "mode": mode,
                                "aspect": aspect_key,
                                "snippet": entry.get("snippet"),
                                "score": entry.get("score"),
                            }
                        )

    return {
        "status": "ok",
        "productSlug": slug,
        "stats": stats,
        "samples": reviews,
        "evidenceSnippets": evidence_snippets[:8],
        "freshness": {
            "stats": artifact_updated_at(stats_path),
            "retrieval": artifact_updated_at(retrieval_path),
        },
    }


def profile_payload(slug: str) -> dict[str, Any]:
    """Return baseline and review-informed visual profile payloads."""
    _load_product(slug)
    profile_dir = VISUAL_PROFILES_DIR / slug
    baseline_path = profile_dir / "baseline_description_only.json"
    review_path = profile_dir / "review_informed_rag.json"
    retrieval_path = profile_dir / "retrieval_evidence.json"
    trace_path = profile_dir / "llm_trace.json"

    modes: dict[str, Any] = {}
    missing: list[str] = []
    for mode_name, path in (
        ("baseline_description_only", baseline_path),
        ("review_informed_rag", review_path),
    ):
        if path.exists():
            profile = VisualProfile.model_validate_json(path.read_text(encoding="utf-8"))
            modes[mode_name] = {
                "status": "available",
                "profile": profile.model_dump(mode="json"),
                "updatedAt": artifact_updated_at(path),
            }
        else:
            modes[mode_name] = {
                "status": "missing_artifact",
                "message": f"{mode_name} is missing. Run extract-visual-profile for this product.",
            }
            missing.append(mode_name)

    return {
        "status": "ok" if not missing else "partial",
        "productSlug": slug,
        "modes": modes,
        "retrievalEvidence": _read_json(retrieval_path, default={}),
        "llmTrace": _read_json(trace_path, default={}),
        "missingArtifacts": missing,
        "freshness": {
            "baseline": artifact_updated_at(baseline_path),
            "reviewInformed": artifact_updated_at(review_path),
        },
    }


def generation_payload(slug: str) -> dict[str, Any]:
    """Return generation artifacts for one product slug."""
    _load_product(slug)
    reference_images = _reference_images(slug)
    models: dict[str, Any] = {}
    missing: list[str] = []
    for provider in ("openai", "stability"):
        manifest_path = GENERATED_IMAGES_DIR / slug / provider / "generation_manifest.json"
        prompt_versions_path = GENERATED_IMAGES_DIR / slug / provider / "prompt_versions.json"
        if not manifest_path.exists():
            models[provider] = {
                "status": "missing_artifact",
                "message": (
                    f"{provider} generation artifacts are missing. " "Run generate-images first."
                ),
            }
            missing.append(provider)
            continue
        manifest = GenerationManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        prompt_versions = _read_json(prompt_versions_path, default={"versions": []})
        models[provider] = {
            "status": "available",
            "manifest": manifest.model_dump(mode="json"),
            "promptVersions": prompt_versions,
            "pilotImages": [
                _generated_image_item(image) for image in manifest.pilot_generation.images
            ],
            "finalImages": [
                _generated_image_item(image) for image in manifest.final_generation.images
            ],
            "updatedAt": artifact_updated_at(manifest_path),
        }

    return {
        "status": "ok" if not missing else "partial",
        "productSlug": slug,
        "referenceImages": reference_images,
        "models": models,
        "missingArtifacts": missing,
        "freshness": {
            provider: model.get("updatedAt")
            for provider, model in models.items()
            if isinstance(model, dict)
        },
    }


def evaluation_payload(slug: str) -> dict[str, Any]:
    """Return evaluation artifacts or a clear missing-artifact state."""
    _load_product(slug)
    evaluation_dir = EVALUATIONS_DIR / slug
    summary_path = evaluation_dir / "summary.json"
    if not summary_path.exists():
        return {
            "status": "missing_artifact",
            "productSlug": slug,
            "message": "Evaluation artifacts are missing. Run evaluate-images first.",
        }

    panels = _read_json(evaluation_dir / "comparison_panels_manifest.json", default={})
    summary = _read_json(summary_path, default={})
    vision_eval = _read_json(evaluation_dir / "vision_assisted_eval.json", default={})
    return {
        "status": "ok",
        "productSlug": slug,
        "summary": summary,
        "comparisonPanels": _panel_items_from_manifest(panels),
        "visionAssisted": vision_eval,
        "humanScoreSheetUrl": artifact_api_url(evaluation_dir / "human_score_sheet.csv"),
        "freshness": artifact_updated_at(summary_path),
    }


def workflow_latest_payload() -> dict[str, Any]:
    """Return current stage progress derived from on-disk artifacts."""
    products = list_products_payload().get("items", [])
    total_products = len(products)
    profile_complete = sum(
        1
        for item in products
        if item["artifacts"]["profiles"]["baseline"]
        and item["artifacts"]["profiles"]["reviewInformed"]
    )
    generation_complete = sum(
        1
        for item in products
        if item["artifacts"]["generation"]["openai"] or item["artifacts"]["generation"]["stability"]
    )
    evaluation_complete = sum(1 for item in products if item["artifacts"]["evaluation"])

    stages = [
        _workflow_stage(
            stage="discover-products",
            completed=(DATA_DIR / "discovery" / "discovery_manifest.json").exists(),
            total=1,
            current=1 if (DATA_DIR / "discovery" / "discovery_manifest.json").exists() else 0,
            artifact="data/discovery/discovery_manifest.json",
        ),
        _workflow_stage(
            stage="scrape-all",
            completed=(RAW_DIR / "raw_manifest.json").exists(),
            total=total_products or 3,
            current=total_products,
            artifact="data/raw/raw_manifest.json",
        ),
        _workflow_stage(
            stage="build-corpus",
            completed=(PROCESSED_DIR / "manifest.json").exists(),
            total=total_products or 3,
            current=total_products,
            artifact="data/processed/manifest.json",
        ),
        _workflow_stage(
            stage="extract-visual-profile",
            completed=profile_complete == total_products and total_products > 0,
            total=total_products or 3,
            current=profile_complete,
            artifact="outputs/visual_profiles/<product_slug>/review_informed_rag.json",
        ),
        _workflow_stage(
            stage="generate-images",
            completed=generation_complete == total_products and total_products > 0,
            total=total_products or 3,
            current=generation_complete,
            artifact="outputs/generated_images/<product_slug>/<model>/generation_manifest.json",
        ),
        _workflow_stage(
            stage="evaluate-images",
            completed=evaluation_complete == total_products and total_products > 0,
            total=total_products or 3,
            current=evaluation_complete,
            artifact="outputs/evaluations/<product_slug>/summary.json",
        ),
    ]

    return {
        "status": "ok",
        "stages": stages,
        "traces": [
            {
                "stage": stage["stage"],
                "artifact": stage["artifact"],
                "owner": "Artifact-backed workflow",
                "note": stage["detail"],
            }
            for stage in stages
        ],
    }


def _workflow_stage(
    *,
    stage: str,
    completed: bool,
    total: int,
    current: int,
    artifact: str,
) -> dict[str, Any]:
    """Build one workflow stage status object."""
    if completed:
        status = "Ready"
        timeline_status = "done"
        detail = f"{current}/{total} artifact targets are available."
    elif current > 0:
        status = "Running"
        timeline_status = "active"
        detail = f"{current}/{total} artifact targets are available so far."
    else:
        status = "Pending"
        timeline_status = "pending"
        detail = "No durable artifacts are available yet."
    return {
        "stage": stage,
        "status": status,
        "timelineStatus": timeline_status,
        "artifact": artifact,
        "completedCount": current,
        "totalCount": total,
        "detail": detail,
    }


def _load_product(slug: str) -> ProcessedProductRecord:
    """Load one processed product or raise FileNotFoundError."""
    path = product_dir(slug) / "product.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown product slug: {slug}")
    return ProcessedProductRecord.model_validate_json(path.read_text(encoding="utf-8"))


def product_dir(slug: str) -> Path:
    """Return the processed product directory for one slug."""
    return PROCESSED_DIR / slug


def _load_selected_records() -> dict[str, dict[str, Any]]:
    """Load selected product rows keyed by source URL."""
    if not SELECTED_PRODUCTS_PATH.exists():
        return {}
    records = _read_jsonl(SELECTED_PRODUCTS_PATH)
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        source_url = record.get("product_url")
        if isinstance(source_url, str):
            result[source_url] = record
    return result


def _reference_images(slug: str) -> list[dict[str, str]]:
    """Return reference image descriptors for one product."""
    image_manifest_path = PROCESSED_DIR / slug / "image_manifest.json"
    image_manifest = _read_json(image_manifest_path, default=[])
    return [
        {
            "filename": image["filename"],
            "url": artifact_api_url(Path(image["local_path"])),
        }
        for image in image_manifest
        if isinstance(image, dict) and image.get("valid")
    ]


def _generated_image_item(image: Any) -> dict[str, Any]:
    """Normalize one generated image record for frontend consumption."""
    local_path = Path(image.local_path if hasattr(image, "local_path") else image["local_path"])
    return {
        "filename": image.filename if hasattr(image, "filename") else image["filename"],
        "url": artifact_api_url(local_path),
        "sha256": image.sha256 if hasattr(image, "sha256") else image["sha256"],
        "width": image.width if hasattr(image, "width") else image["width"],
        "height": image.height if hasattr(image, "height") else image["height"],
    }


def _panel_items_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Attach asset URLs to saved comparison panels."""
    panels = manifest.get("panels", [])
    if not isinstance(panels, list):
        return []
    result: list[dict[str, Any]] = []
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        result.append(
            {
                **panel,
                "referenceImageUrl": artifact_api_url(Path(str(panel["reference_image_path"]))),
                "generatedImageUrl": artifact_api_url(Path(str(panel["generated_image_path"]))),
            }
        )
    return result


def _read_json(path: Path, *, default: Any) -> Any:
    """Read one JSON file or return the supplied default."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dicts."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows
