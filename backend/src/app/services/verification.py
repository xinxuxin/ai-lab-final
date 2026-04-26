"""Repository verification and submission packaging helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from app.models.schemas import (
    GenerationManifest,
    ProcessedManifest,
    Q1ValidationResult,
    VisualProfile,
)
from app.services.corpus import validate_q1_from_disk
from app.utils.artifacts import DATA_DIR, DOCS_DIR, OUTPUTS_DIR, PROMPTS_DIR, REPO_ROOT
from app.workflow.agents import (
    DataCurationAgent,
    EvaluationAgent,
    ImageGenerationAgent,
    PromptComposerAgent,
    RetrievalAgent,
    VisualUnderstandingAgent,
)
from app.workflow.orchestrator import load_latest_workflow_run

VerificationStage = Literal["q1", "q2", "q3", "q4", "full"]


@dataclass(slots=True)
class VerificationResult:
    """Human and machine-readable verification output."""

    stage: VerificationStage
    passed: bool
    summary: dict[str, Any]


@dataclass(slots=True)
class SubmissionPackageResult:
    """Result for the submission package builder."""

    output_dir: Path
    copied_paths: list[Path]
    manifest_path: Path


def verify_repository(
    *,
    stage: VerificationStage,
    processed_dir: Path | None = None,
    selected_products_path: Path | None = None,
    min_review_count: int | None = None,
    frontend_root: Path | None = None,
    run_frontend_build: bool = True,
) -> VerificationResult:
    """Verify repository artifacts against assignment-aligned requirements."""
    resolved_processed_dir = processed_dir or DATA_DIR / "processed"
    resolved_selected_path = selected_products_path or DATA_DIR / "selected_products.jsonl"
    resolved_frontend_root = frontend_root or REPO_ROOT / "frontend"

    checks: dict[str, Any] = {}
    issues: list[str] = []

    if stage in {"q1", "full"}:
        q1_result = _verify_q1(
            processed_dir=resolved_processed_dir,
            selected_products_path=resolved_selected_path,
            min_review_count=min_review_count,
        )
        checks["q1"] = q1_result
        issues.extend(q1_result["issues"])

    if stage in {"q2", "full"}:
        q2_result = _verify_q2(processed_dir=resolved_processed_dir)
        checks["q2"] = q2_result
        issues.extend(q2_result["issues"])

    if stage in {"q3", "full"}:
        q3_result = _verify_q3(processed_dir=resolved_processed_dir)
        checks["q3"] = q3_result
        issues.extend(q3_result["issues"])

    if stage in {"q4", "full"}:
        q4_result = _verify_q4()
        checks["q4"] = q4_result
        issues.extend(q4_result["issues"])

    if stage == "full":
        frontend_result = _verify_frontend(
            frontend_root=resolved_frontend_root,
            run_build=run_frontend_build,
        )
        checks["frontend"] = frontend_result
        issues.extend(frontend_result["issues"])

    return VerificationResult(
        stage=stage,
        passed=not issues,
        summary={
            "stage": stage,
            "passed": not issues,
            "checks": checks,
            "issues": issues,
        },
    )


def build_submission_package(*, output_dir: Path | None = None) -> SubmissionPackageResult:
    """Copy required repository artifacts into a submission package directory."""
    resolved_output_dir = output_dir or REPO_ROOT / "submission_package"
    if resolved_output_dir.exists():
        shutil.rmtree(resolved_output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    ignore_generated = shutil.ignore_patterns(
        ".DS_Store",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "dist",
        "node_modules",
    )

    copy_targets = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "backend",
        REPO_ROOT / "frontend",
        REPO_ROOT / "configs",
        REPO_ROOT / "data",
        REPO_ROOT / "outputs",
        REPO_ROOT / "prompts",
        REPO_ROOT / "docs",
        REPO_ROOT / "reports",
        REPO_ROOT / "scripts",
        REPO_ROOT / ".env.example",
        REPO_ROOT / "Makefile",
    ]
    copied_paths: list[Path] = []
    for source in copy_targets:
        destination = resolved_output_dir / source.name
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore_generated)
        elif source.exists():
            shutil.copy2(source, destination)
        copied_paths.append(destination)

    manifest_path = resolved_output_dir / "submission_manifest.json"
    manifest_payload = {
        "created_from": str(REPO_ROOT),
        "copied_paths": [
            str(path.relative_to(resolved_output_dir)) if path.exists() else str(path.name)
            for path in copied_paths
        ],
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    return SubmissionPackageResult(
        output_dir=resolved_output_dir,
        copied_paths=copied_paths,
        manifest_path=manifest_path,
    )


def _verify_q1(
    *,
    processed_dir: Path,
    selected_products_path: Path,
    min_review_count: int | None,
) -> dict[str, Any]:
    validation: Q1ValidationResult = validate_q1_from_disk(
        processed_dir=processed_dir,
        selected_products_path=selected_products_path,
        min_review_count=min_review_count,
    )
    return {
        "passed": validation.passed,
        "selected_products_count": validation.selected_products_count,
        "distinct_categories_count": validation.distinct_categories_count,
        "min_review_count_threshold": validation.min_review_count_threshold,
        "per_product_review_counts": validation.per_product_review_counts,
        "per_product_image_counts": validation.per_product_image_counts,
        "issues": validation.issues,
    }


def _verify_q2(*, processed_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    manifest_path = processed_dir / "manifest.json"
    if not manifest_path.exists():
        return {"passed": False, "issues": ["Processed manifest is missing for Q2 verification."]}

    manifest = ProcessedManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    products_checked: list[str] = []
    for entry in manifest.entries:
        slug = entry.product_slug
        products_checked.append(slug)
        profile_dir = OUTPUTS_DIR / "visual_profiles" / slug
        baseline_path = profile_dir / "baseline_description_only.json"
        review_path = profile_dir / "review_informed_rag.json"
        retrieval_path = profile_dir / "retrieval_evidence.json"
        if not baseline_path.exists():
            issues.append(f"Q2 baseline profile is missing for {slug}.")
        else:
            try:
                VisualProfile.model_validate_json(baseline_path.read_text(encoding="utf-8"))
            except ValidationError as exc:
                message = exc.errors()[0]["msg"]
                issues.append(f"Q2 baseline profile is invalid for {slug}: {message}")
        if not review_path.exists():
            issues.append(f"Q2 review-informed profile is missing for {slug}.")
        else:
            try:
                VisualProfile.model_validate_json(review_path.read_text(encoding="utf-8"))
            except ValidationError as exc:
                issues.append(
                    f"Q2 review-informed profile is invalid for {slug}: {exc.errors()[0]['msg']}"
                )
        if not retrieval_path.exists():
            issues.append(f"Q2 retrieval evidence is missing for {slug}.")
    for prompt_path in [
        PROMPTS_DIR / "q2" / "aspect_evidence_extraction.md",
        PROMPTS_DIR / "q2" / "conflict_resolution.md",
        PROMPTS_DIR / "q2" / "final_visual_profile_synthesis.md",
    ]:
        if not prompt_path.exists():
            issues.append(f"Q2 prompt template is missing: {prompt_path.name}.")
    return {"passed": not issues, "products_checked": products_checked, "issues": issues}


def _verify_q3(*, processed_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    manifest = ProcessedManifest.model_validate_json((processed_dir / "manifest.json").read_text())
    providers_used: set[str] = set()
    products_checked: list[str] = []
    for entry in manifest.entries:
        slug = entry.product_slug
        products_checked.append(slug)
        for provider in ("openai", "stability"):
            manifest_path = (
                OUTPUTS_DIR / "generated_images" / slug / provider / "generation_manifest.json"
            )
            if not manifest_path.exists():
                issues.append(f"Q3 generation manifest is missing for {slug}/{provider}.")
                continue
            try:
                generation_manifest = GenerationManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8")
                )
            except ValidationError as exc:
                message = exc.errors()[0]["msg"]
                issues.append(f"Q3 generation manifest is invalid for {slug}/{provider}: {message}")
                continue
            providers_used.add(provider)
            final_count = len(generation_manifest.final_generation.images)
            if final_count < 3 or final_count > 5:
                issues.append(
                    f"Q3 final image count for {slug}/{provider} must be "
                    f"between 3 and 5; got {final_count}."
                )
            for image in generation_manifest.final_generation.images:
                _verify_image(Path(image.local_path), issues, f"{slug}/{provider}/{image.filename}")
        evaluation_summary = OUTPUTS_DIR / "evaluations" / slug / "summary.json"
        if not evaluation_summary.exists():
            issues.append(f"Q3 evaluation summary is missing for {slug}.")
    if len(providers_used) < 2:
        issues.append(
            "Q3 requires at least two image-generation providers across the selected products."
        )
    return {
        "passed": not issues,
        "products_checked": products_checked,
        "providers_used": sorted(providers_used),
        "issues": issues,
    }


def _verify_q4() -> dict[str, Any]:
    issues: list[str] = []
    required_agents = [
        DataCurationAgent,
        RetrievalAgent,
        VisualUnderstandingAgent,
        PromptComposerAgent,
        ImageGenerationAgent,
        EvaluationAgent,
    ]
    agent_names = [agent.__name__ for agent in required_agents]
    latest_run = load_latest_workflow_run()
    if latest_run is None:
        issues.append("Q4 workflow trace is missing. Run run-workflow first.")
    workflow_doc = DOCS_DIR / "agentic_workflow.md"
    if not workflow_doc.exists():
        issues.append("Q4 workflow documentation is missing.")
    return {
        "passed": not issues,
        "agents": agent_names,
        "latest_run_id": latest_run.summary.run_id if latest_run else None,
        "issues": issues,
    }


def _verify_frontend(*, frontend_root: Path, run_build: bool) -> dict[str, Any]:
    issues: list[str] = []
    page_expectations = {
        "ProductsPage.tsx": "api.getProducts()",
        "ReviewsPage.tsx": "api.getReviews(",
        "ProfilesPage.tsx": "api.getProfiles(",
        "GenerationPage.tsx": "api.getGeneration(",
        "ComparisonPage.tsx": "api.getEvaluation(",
        "WorkflowPage.tsx": "api.getWorkflow()",
    }
    for filename, api_call in page_expectations.items():
        page_path = frontend_root / "src" / "pages" / filename
        if not page_path.exists():
            issues.append(f"Frontend page is missing: {filename}.")
            continue
        if api_call not in page_path.read_text(encoding="utf-8"):
            issues.append(f"Frontend page is not loading artifact-backed state: {filename}.")

    if run_build:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_root,
            capture_output=True,
            text=True,
            check=False,
        )
        build_ok = result.returncode == 0
        if not build_ok:
            issues.append(f"Frontend build failed: {result.stderr or result.stdout}")
    else:
        build_ok = None
    return {"passed": not issues, "frontend_build_passed": build_ok, "issues": issues}


def _verify_image(path: Path, issues: list[str], label: str) -> None:
    if not path.exists():
        issues.append(f"Image artifact is missing: {label}.")
        return
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        issues.append(f"Image artifact could not be opened for {label}: {exc}")
