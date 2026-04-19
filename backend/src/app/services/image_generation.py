"""Q3 image-generation pipeline for API-only product rendering."""

from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.config.settings import Settings, get_settings
from app.imagegen import (
    GeneratedImageBinary,
    ImageGenerationAdapter,
    OpenAIImageAdapter,
    StabilityImageAdapter,
    load_prompt_template,
)
from app.models.schemas import (
    GeneratedImageFile,
    GenerationManifest,
    GenerationRecord,
    ProcessedProductRecord,
    PromptVersion,
    VisualAttributeEvidence,
    VisualProfile,
)
from app.utils.artifacts import DATA_DIR, OUTPUTS_DIR, ensure_project_dirs

GENERATED_IMAGES_DIR = OUTPUTS_DIR / "generated_images"
VISUAL_PROFILES_DIR = OUTPUTS_DIR / "visual_profiles"
PROCESSED_DIR = DATA_DIR / "processed"
SUPPORTED_MODELS = {"openai", "stability"}


class ImageGenerationPipelineError(RuntimeError):
    """Raised when the Q3 image-generation pipeline cannot complete."""


@dataclass(slots=True)
class GenerateImagesResult:
    """Return value for one product/model image-generation run."""

    product_slug: str
    model_name: str
    manifest: GenerationManifest
    manifest_path: Path
    prompt_versions_path: Path


def generate_images_for_product(
    *,
    product_slug: str,
    model_name: str,
    count: int = 4,
    processed_root: Path | None = None,
    profiles_root: Path | None = None,
    outputs_root: Path | None = None,
    settings: Settings | None = None,
    adapter: ImageGenerationAdapter | None = None,
    refresh: bool = False,
    reuse_existing: bool = True,
) -> GenerateImagesResult:
    """Generate pilot and final product images for one model."""
    if model_name not in SUPPORTED_MODELS:
        available = ", ".join(sorted(SUPPORTED_MODELS))
        raise ImageGenerationPipelineError(f"Unknown model '{model_name}'. Available: {available}")
    if count < 1 or count > 5:
        raise ImageGenerationPipelineError("Final image count must be between 1 and 5.")

    settings = settings or get_settings()
    ensure_project_dirs()

    resolved_processed_root = processed_root or PROCESSED_DIR
    resolved_profiles_root = profiles_root or VISUAL_PROFILES_DIR
    resolved_outputs_root = outputs_root or GENERATED_IMAGES_DIR

    product_dir = resolved_processed_root / product_slug
    profile_dir = resolved_profiles_root / product_slug
    if not product_dir.exists():
        raise ImageGenerationPipelineError(f"Processed product directory is missing: {product_dir}")
    if not profile_dir.exists():
        raise ImageGenerationPipelineError(f"Visual profile directory is missing: {profile_dir}")

    product = ProcessedProductRecord.model_validate_json(
        (product_dir / "product.json").read_text(encoding="utf-8")
    )
    baseline_profile = _load_visual_profile(profile_dir / "baseline_description_only.json")
    review_profile = _load_visual_profile(profile_dir / "review_informed_rag.json")

    output_dir = resolved_outputs_root / product_slug / model_name
    prompt_versions_path = output_dir / "prompt_versions.json"
    manifest_path = output_dir / "generation_manifest.json"

    if reuse_existing and not refresh and manifest_path.exists():
        manifest = GenerationManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        if _manifest_is_complete(manifest):
            manifest.reused_existing = True
            return GenerateImagesResult(
                product_slug=product_slug,
                model_name=model_name,
                manifest=manifest,
                manifest_path=manifest_path,
                prompt_versions_path=prompt_versions_path,
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pilot").mkdir(parents=True, exist_ok=True)
    (output_dir / "final").mkdir(parents=True, exist_ok=True)

    prompt_versions = _build_prompt_versions(
        product=product,
        model_name=model_name,
        baseline_profile=baseline_profile,
        review_profile=review_profile,
    )
    _write_prompt_payload(output_dir / "pilot" / "prompt.json", prompt_versions[0])
    _write_prompt_payload(output_dir / "final" / "prompt.json", prompt_versions[1])
    prompt_versions_payload = {
        "versions": [version.model_dump(mode="json") for version in prompt_versions]
    }
    prompt_versions_path.write_text(
        json.dumps(prompt_versions_payload, indent=2),
        encoding="utf-8",
    )

    owns_adapter = adapter is None
    active_adapter = adapter or _build_adapter(model_name=model_name, settings=settings)
    try:
        pilot_images = active_adapter.generate(
            prompt=prompt_versions[0].prompt_text,
            count=1,
            negative_prompt=prompt_versions[0].negative_prompt,
        )
        final_images = active_adapter.generate(
            prompt=prompt_versions[1].prompt_text,
            count=count,
            negative_prompt=prompt_versions[1].negative_prompt,
        )
    finally:
        close_method = getattr(active_adapter, "close", None)
        if owns_adapter and callable(close_method):
            close_method()

    pilot_record = _write_generation_record(
        generated_images=pilot_images,
        output_dir=output_dir / "pilot",
        product=product,
        model_name=model_name,
        provider=active_adapter.provider,
        prompt_version=prompt_versions[0],
        stage="pilot",
    )
    final_record = _write_generation_record(
        generated_images=final_images,
        output_dir=output_dir / "final",
        product=product,
        model_name=model_name,
        provider=active_adapter.provider,
        prompt_version=prompt_versions[1],
        stage="final",
    )

    manifest = GenerationManifest(
        product_slug=product_slug,
        product_id=product.product_id,
        product_name=product.title,
        provider=active_adapter.provider,
        model_name=model_name,
        output_dir=str(output_dir),
        prompt_versions_path=str(prompt_versions_path),
        pilot_generation=pilot_record,
        final_generation=final_record,
        status="completed",
        reused_existing=False,
        notes=[
            "Pilot prompt is sourced from baseline_description_only.",
            "Final prompt is sourced from review_informed_rag and carries refined constraints.",
        ],
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return GenerateImagesResult(
        product_slug=product_slug,
        model_name=model_name,
        manifest=manifest,
        manifest_path=manifest_path,
        prompt_versions_path=prompt_versions_path,
    )


def list_generation_ready_products(profiles_root: Path | None = None) -> list[str]:
    """Return product slugs that have both required visual-profile inputs."""
    root = profiles_root or VISUAL_PROFILES_DIR
    if not root.exists():
        return []
    result: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if (child / "baseline_description_only.json").exists() and (
            child / "review_informed_rag.json"
        ).exists():
            result.append(child.name)
    return result


def _build_prompt_versions(
    *,
    product: ProcessedProductRecord,
    model_name: str,
    baseline_profile: VisualProfile,
    review_profile: VisualProfile,
) -> list[PromptVersion]:
    """Build one pilot prompt and one refined final prompt."""
    pilot_path, pilot_template = load_prompt_template("pilot")
    final_path, final_template = load_prompt_template("final")
    common_constraints = [
        "single product only",
        "centered composition",
        "neutral or studio background",
        "realistic product photography",
        "no extra accessories unless explicitly supported",
    ]

    pilot_context = {
        "product_name": product.title,
        "category": product.category,
        "prompt_ready_description": baseline_profile.prompt_ready_description,
        "top_attributes": _join_attributes(baseline_profile.high_confidence_visual_attributes[:3]),
        "negative_constraints": _join_constraints(
            baseline_profile.negative_constraints,
            common_constraints,
        ),
    }
    final_context = {
        "product_name": product.title,
        "category": product.category,
        "prompt_ready_description": review_profile.prompt_ready_description,
        "top_attributes": _join_attributes(review_profile.high_confidence_visual_attributes[:5]),
        "negative_constraints": _join_constraints(
            review_profile.negative_constraints,
            common_constraints,
        ),
        "mismatch_avoidance": _join_mismatch_avoidance(review_profile),
    }

    pilot_negative = _join_constraints(baseline_profile.negative_constraints, common_constraints)
    final_negative = _join_constraints(review_profile.negative_constraints, common_constraints)

    return [
        PromptVersion(
            prompt_version_id=f"{product.product_id}-{model_name}-pilot",
            product_id=product.product_id,
            provider=model_name,
            model_name=model_name,
            strategy="pilot",
            prompt_source_mode="baseline_description_only",
            prompt_text=pilot_template.format_map(pilot_context).strip(),
            negative_prompt=pilot_negative if model_name == "stability" else None,
            negative_constraints=sorted(
                set(common_constraints + baseline_profile.negative_constraints)
            ),
            notes=f"Template: {pilot_path}",
        ),
        PromptVersion(
            prompt_version_id=f"{product.product_id}-{model_name}-final",
            product_id=product.product_id,
            provider=model_name,
            model_name=model_name,
            strategy="final",
            prompt_source_mode="review_informed_rag",
            prompt_text=final_template.format_map(final_context).strip(),
            negative_prompt=final_negative if model_name == "stability" else None,
            negative_constraints=sorted(
                set(common_constraints + review_profile.negative_constraints)
            ),
            notes=f"Template: {final_path}",
        ),
    ]


def _build_adapter(*, model_name: str, settings: Settings) -> ImageGenerationAdapter:
    """Instantiate the provider adapter requested by the CLI."""
    if model_name == "openai":
        return OpenAIImageAdapter(settings=settings)
    if model_name == "stability":
        return StabilityImageAdapter(settings=settings)
    raise ImageGenerationPipelineError(f"Unsupported image model: {model_name}")


def _write_prompt_payload(path: Path, prompt_version: PromptVersion) -> None:
    """Write a prompt payload for human inspection."""
    payload = {
        "prompt_version_id": prompt_version.prompt_version_id,
        "strategy": prompt_version.strategy,
        "prompt_source_mode": prompt_version.prompt_source_mode,
        "prompt_text": prompt_version.prompt_text,
        "negative_prompt": prompt_version.negative_prompt,
        "negative_constraints": prompt_version.negative_constraints,
        "created_at": prompt_version.created_at.isoformat(),
        "notes": prompt_version.notes,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_generation_record(
    *,
    generated_images: list[GeneratedImageBinary],
    output_dir: Path,
    product: ProcessedProductRecord,
    model_name: str,
    provider: str,
    prompt_version: PromptVersion,
    stage: Literal["pilot", "final"],
) -> GenerationRecord:
    """Persist generated images and return a durable generation record."""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_files: list[GeneratedImageFile] = []
    output_paths: list[str] = []
    for index, generated in enumerate(generated_images, start=1):
        image_filename = f"image_{index:02d}.png"
        image_path = output_dir / image_filename
        image_path.write_bytes(generated.image_bytes)
        image_files.append(
            _validate_and_hash_image(
                image_path=image_path,
                content_type=generated.content_type,
                metadata=generated.metadata,
            )
        )
        output_paths.append(str(image_path))

    return GenerationRecord(
        generation_id=str(uuid4()),
        product_id=product.product_id,
        provider=provider,
        model_name=model_name,
        stage=stage,
        prompt_version_id=prompt_version.prompt_version_id,
        prompt_source_mode=prompt_version.prompt_source_mode,
        output_paths=output_paths,
        images=image_files,
        status="completed",
        metadata={
            "image_count": len(output_paths),
            "generated_at": datetime.utcnow().isoformat(),
        },
    )


def _validate_and_hash_image(
    *,
    image_path: Path,
    content_type: str,
    metadata: dict[str, str | int | float | bool],
) -> GeneratedImageFile:
    """Verify image integrity with Pillow and return file metadata."""
    try:
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageGenerationPipelineError(f"Generated image is invalid: {image_path}") from exc

    image_bytes = image_path.read_bytes()
    guessed_type = content_type or mimetypes.guess_type(image_path.name)[0] or "image/png"
    return GeneratedImageFile(
        filename=image_path.name,
        local_path=str(image_path),
        sha256=sha256(image_bytes).hexdigest(),
        width=width,
        height=height,
        byte_size=len(image_bytes),
        content_type=guessed_type,
        metadata=metadata,
    )


def _join_attributes(attributes: list[VisualAttributeEvidence]) -> str:
    """Flatten attributes into a prompt-friendly line."""
    if not attributes:
        return "Use only strongly supported product details from the listing."
    return "; ".join(attribute.attribute for attribute in attributes)


def _join_constraints(primary: list[str], fallback: list[str]) -> str:
    """Combine and flatten negative constraints."""
    values = sorted(set(primary + fallback))
    return "; ".join(values)


def _join_mismatch_avoidance(profile: VisualProfile) -> str:
    """Summarize expectation-vs-reality mismatches as prompt guardrails."""
    if not profile.common_mismatches_between_expectation_and_reality:
        return "Do not add unsupported embellishments or misleading scale cues."
    return "; ".join(
        mismatch.mismatch for mismatch in profile.common_mismatches_between_expectation_and_reality
    )


def _load_visual_profile(path: Path) -> VisualProfile:
    """Load one saved visual profile."""
    if not path.exists():
        raise ImageGenerationPipelineError(f"Visual profile is missing: {path}")
    return VisualProfile.model_validate_json(path.read_text(encoding="utf-8"))


def _manifest_is_complete(manifest: GenerationManifest) -> bool:
    """Check whether a saved manifest still points to valid on-disk image files."""
    image_paths = manifest.pilot_generation.images + manifest.final_generation.images
    for image in image_paths:
        path = Path(image.local_path)
        if not path.exists():
            return False
        try:
            with Image.open(path) as loaded_image:
                loaded_image.verify()
        except (UnidentifiedImageError, OSError):
            return False
    return True
