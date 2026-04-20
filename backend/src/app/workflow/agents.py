"""Typed workflow agents for the end-to-end Q4 orchestration layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import (
    DataCurationAgentInput,
    DataCurationAgentOutput,
    EvaluationAgentInput,
    EvaluationAgentOutput,
    ImageGenerationAgentInput,
    ImageGenerationAgentOutput,
    ProcessedProductRecord,
    PromptComposerAgentInput,
    PromptComposerAgentOutput,
    RetrievalAgentInput,
    RetrievalAgentOutput,
    VisualProfile,
    VisualUnderstandingAgentInput,
    VisualUnderstandingAgentOutput,
)
from app.services import (
    build_processed_corpus,
    evaluate_images_for_product,
    extract_visual_profile,
    generate_images_for_product,
    validate_q1_from_disk,
)
from app.utils.artifacts import DATA_DIR, OUTPUTS_DIR, PROMPTS_DIR, relative_repo_artifact_path


def _relative(path: Path) -> str:
    return relative_repo_artifact_path(path)


@dataclass(slots=True)
class DataCurationAgent:
    """Prepare the cleaned corpus and validate the Q1 base artifacts."""

    def run(self, payload: DataCurationAgentInput) -> DataCurationAgentOutput:
        raw_root = Path(payload.raw_root)
        processed_root = Path(payload.processed_root)
        raw_product_dir = raw_root / payload.product_slug
        if not raw_product_dir.exists():
            raise FileNotFoundError(
                f"Raw product artifacts are missing for {payload.product_slug}: {raw_product_dir}"
            )

        product_json_path = processed_root / payload.product_slug / "product.json"
        reused_existing = payload.reuse_existing and not payload.refresh and product_json_path.exists()
        if not reused_existing:
            build_processed_corpus(
                raw_dir=raw_root,
                output_dir=processed_root,
                selected_products_path=Path(payload.selected_products_path),
            )

        validation = validate_q1_from_disk(
            processed_dir=processed_root,
            selected_products_path=Path(payload.selected_products_path),
        )
        product = ProcessedProductRecord.model_validate_json(
            product_json_path.read_text(encoding="utf-8")
        )
        return DataCurationAgentOutput(
            product_slug=payload.product_slug,
            selected_category=product.selected_category,
            raw_product_dir=str(raw_product_dir),
            processed_product_dir=str(product_json_path.parent),
            q1_validation_passed=validation.passed,
            review_count=product.cleaned_review_count,
            image_count=product.valid_image_count,
            artifact_links={
                "raw_meta": _relative(raw_product_dir / "product_meta.json"),
                "reviews": _relative(raw_product_dir / "reviews.jsonl"),
                "processed_product": _relative(product_json_path),
                "processed_manifest": _relative(processed_root / "manifest.json"),
            },
            reused_existing=reused_existing,
        )


@dataclass(slots=True)
class RetrievalAgent:
    """Build or reuse the retrieval-evidence layer for review-informed analysis."""

    def run(self, payload: RetrievalAgentInput) -> RetrievalAgentOutput:
        output_dir = Path(payload.output_dir)
        retrieval_path = output_dir / "retrieval_evidence.json"
        trace_path = output_dir / "llm_trace.json"
        review_profile_path = output_dir / "review_informed_rag.json"
        reused_existing = (
            payload.reuse_existing
            and not payload.refresh
            and retrieval_path.exists()
            and trace_path.exists()
            and review_profile_path.exists()
        )
        if not reused_existing:
            extract_visual_profile(
                product_slug=payload.product_slug,
                mode="review_informed_rag",
                processed_root=Path(payload.processed_product_dir).parent,
                outputs_root=output_dir.parent,
            )

        retrieval_payload = json.loads(retrieval_path.read_text(encoding="utf-8"))
        aspect_entries = retrieval_payload.get("review_informed_rag", {})
        aspect_count = len(aspect_entries) if isinstance(aspect_entries, dict) else 0
        return RetrievalAgentOutput(
            product_slug=payload.product_slug,
            retrieval_evidence_path=str(retrieval_path),
            llm_trace_path=str(trace_path),
            aspect_count=aspect_count,
            reused_existing=reused_existing,
            artifact_links={
                "retrieval_evidence": _relative(retrieval_path),
                "llm_trace": _relative(trace_path),
                "review_profile": _relative(review_profile_path),
            },
        )


@dataclass(slots=True)
class VisualUnderstandingAgent:
    """Ensure both baseline and review-informed visual profiles exist."""

    def run(self, payload: VisualUnderstandingAgentInput) -> VisualUnderstandingAgentOutput:
        output_dir = Path(payload.output_dir)
        baseline_path = output_dir / "baseline_description_only.json"
        review_path = output_dir / "review_informed_rag.json"
        reused_existing = (
            payload.reuse_existing
            and not payload.refresh
            and baseline_path.exists()
            and review_path.exists()
        )
        if not baseline_path.exists() or payload.refresh:
            extract_visual_profile(
                product_slug=payload.product_slug,
                mode="baseline_description_only",
                processed_root=Path(payload.processed_product_dir).parent,
                outputs_root=output_dir.parent,
            )
            reused_existing = False

        if not review_path.exists():
            extract_visual_profile(
                product_slug=payload.product_slug,
                mode="review_informed_rag",
                processed_root=Path(payload.processed_product_dir).parent,
                outputs_root=output_dir.parent,
            )
            reused_existing = False

        review_profile = VisualProfile.model_validate_json(review_path.read_text(encoding="utf-8"))
        return VisualUnderstandingAgentOutput(
            product_slug=payload.product_slug,
            baseline_profile_path=str(baseline_path),
            review_profile_path=str(review_path),
            prompt_ready_description=review_profile.prompt_ready_description,
            negative_constraints=review_profile.negative_constraints,
            reused_existing=reused_existing,
            artifact_links={
                "baseline_profile": _relative(baseline_path),
                "review_profile": _relative(review_path),
            },
        )


@dataclass(slots=True)
class PromptComposerAgent:
    """Prepare prompt previews and record prompt-source handoffs for Q3."""

    def run(self, payload: PromptComposerAgentInput) -> PromptComposerAgentOutput:
        visual_profile_dir = Path(payload.visual_profile_dir)
        baseline_profile = VisualProfile.model_validate_json(
            (visual_profile_dir / "baseline_description_only.json").read_text(encoding="utf-8")
        )
        review_profile = VisualProfile.model_validate_json(
            (visual_profile_dir / "review_informed_rag.json").read_text(encoding="utf-8")
        )
        _, pilot_template = _load_q3_prompt("pilot")
        _, final_template = _load_q3_prompt("final")
        prompt_sources: dict[str, str] = {}
        prompt_previews: dict[str, dict[str, str]] = {}
        artifact_links: dict[str, str] = {}

        for provider in payload.providers:
            provider_dir = Path(payload.generation_root) / payload.product_slug / provider
            prompt_versions_path = provider_dir / "prompt_versions.json"
            if prompt_versions_path.exists():
                prompt_versions = json.loads(prompt_versions_path.read_text(encoding="utf-8"))
                prompt_sources[provider] = "saved_prompt_versions"
                prompt_previews[provider] = {
                    version["strategy"]: version["prompt_text"]
                    for version in prompt_versions.get("versions", [])
                    if isinstance(version, dict) and isinstance(version.get("strategy"), str)
                }
                artifact_links[f"{provider}_prompt_versions"] = _relative(prompt_versions_path)
                continue

            prompt_sources[provider] = "visual_profile_templates"
            prompt_previews[provider] = {
                "pilot": _render_prompt_preview(pilot_template, baseline_profile),
                "final": _render_prompt_preview(final_template, review_profile),
            }

        return PromptComposerAgentOutput(
            product_slug=payload.product_slug,
            prompt_sources=prompt_sources,
            prompt_previews=prompt_previews,
            reused_existing=all(source == "saved_prompt_versions" for source in prompt_sources.values()),
            artifact_links=artifact_links,
        )


@dataclass(slots=True)
class ImageGenerationAgent:
    """Generate or reuse images for all configured providers."""

    def run(self, payload: ImageGenerationAgentInput) -> ImageGenerationAgentOutput:
        generated_models: list[str] = []
        manifest_paths: dict[str, str] = {}
        reused_existing = True
        for provider in payload.providers:
            result = generate_images_for_product(
                product_slug=payload.product_slug,
                model_name=provider,
                count=payload.count,
                refresh=payload.refresh,
                reuse_existing=payload.reuse_existing,
            )
            generated_models.append(provider)
            manifest_paths[provider] = str(result.manifest_path)
            reused_existing = reused_existing and result.manifest.reused_existing

        return ImageGenerationAgentOutput(
            product_slug=payload.product_slug,
            generated_models=generated_models,
            generation_manifest_paths=manifest_paths,
            reused_existing=reused_existing,
            artifact_links={provider: _relative(Path(path)) for provider, path in manifest_paths.items()},
        )


@dataclass(slots=True)
class EvaluationAgent:
    """Build or reuse comparison analytics for generated outputs."""

    def run(self, payload: EvaluationAgentInput) -> EvaluationAgentOutput:
        evaluation_dir = OUTPUTS_DIR / "evaluations" / payload.product_slug
        summary_path = evaluation_dir / "summary.json"
        comparison_panels_path = evaluation_dir / "comparison_panels_manifest.json"
        human_score_sheet_path = evaluation_dir / "human_score_sheet.csv"
        vision_assisted_path = evaluation_dir / "vision_assisted_eval.json"
        reused_existing = (
            payload.reuse_existing
            and not payload.refresh
            and summary_path.exists()
            and comparison_panels_path.exists()
            and human_score_sheet_path.exists()
            and vision_assisted_path.exists()
        )
        if reused_existing:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            return EvaluationAgentOutput(
                product_slug=payload.product_slug,
                summary_path=str(summary_path),
                comparison_panels_manifest_path=str(comparison_panels_path),
                human_score_sheet_path=str(human_score_sheet_path),
                vision_assisted_eval_path=str(vision_assisted_path),
                evaluation_status=str(summary["status"]),
                reused_existing=True,
                artifact_links={
                    "summary": _relative(summary_path),
                    "comparison_panels": _relative(comparison_panels_path),
                    "human_score_sheet": _relative(human_score_sheet_path),
                    "vision_assisted_eval": _relative(vision_assisted_path),
                },
            )

        result = evaluate_images_for_product(
            product_slug=payload.product_slug,
            vision_assisted=payload.vision_assisted,
        )
        return EvaluationAgentOutput(
            product_slug=payload.product_slug,
            summary_path=str(result.summary_path),
            comparison_panels_manifest_path=str(result.comparison_panels_manifest_path),
            human_score_sheet_path=str(result.human_score_sheet_path),
            vision_assisted_eval_path=str(result.vision_assisted_eval_path),
            evaluation_status=str(result.summary["status"]),
            reused_existing=False,
            artifact_links={
                "summary": _relative(result.summary_path),
                "comparison_panels": _relative(result.comparison_panels_manifest_path),
                "human_score_sheet": _relative(result.human_score_sheet_path),
                "vision_assisted_eval": _relative(result.vision_assisted_eval_path),
            },
        )


def _load_q3_prompt(name: str) -> tuple[Path, str]:
    prompt_path = PROMPTS_DIR / "q3" / f"{name}_prompt.md"
    return prompt_path, prompt_path.read_text(encoding="utf-8")


def _render_prompt_preview(template: str, profile: VisualProfile) -> str:
    top_attributes = "; ".join(
        attribute.attribute for attribute in profile.high_confidence_visual_attributes[:4]
    ) or "Use only grounded product details."
    mismatch_avoidance = "; ".join(
        mismatch.mismatch for mismatch in profile.common_mismatches_between_expectation_and_reality[:3]
    ) or "Avoid unsupported mismatches."
    negative_constraints = "; ".join(profile.negative_constraints) or "Avoid unsupported extras."
    return template.format(
        product_name=profile.product_name,
        category=profile.category,
        prompt_ready_description=profile.prompt_ready_description,
        top_attributes=top_attributes,
        mismatch_avoidance=mismatch_avoidance,
        negative_constraints=negative_constraints,
    )
