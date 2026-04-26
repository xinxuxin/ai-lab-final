"""Typer CLI for stage-by-stage workflow execution."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.collectors.discovery import run_discovery
from app.collectors.product_pages import run_scrape_all, run_scrape_product
from app.config.settings import get_settings
from app.services import (
    build_processed_corpus,
    build_submission_package,
    evaluate_images_for_product,
    extract_visual_profile,
    generate_images_for_product,
    list_evaluation_ready_products,
    list_generation_ready_products,
    verify_repository,
)
from app.utils.artifacts import DOCS_DIR
from app.utils.logging import configure_logging
from app.workflow.orchestrator import run_workflow as run_agentic_workflow

app = typer.Typer(help="CLI for the CMU product image generation project.")


def _print_placeholder(stage: str, refresh: bool = False) -> None:
    typer.echo(
        json.dumps(
            {
                "stage": stage,
                "status": "placeholder",
                "refresh": refresh,
                "message": f"{stage} scaffold is ready for implementation.",
            },
            indent=2,
        )
    )


@app.command("discover-products")
def discover_products(
    config: str = typer.Option(
        "../configs/product_queries.yaml",
        help="Path to the discovery query config YAML.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Re-run discovery instead of using cached artifacts.",
    ),
    reuse_existing: bool = typer.Option(
        True,
        "--reuse-existing/--no-reuse-existing",
        help="Reuse on-disk discovery artifacts if they already exist.",
    ),
) -> None:
    """Discover candidate product links and save durable artifacts."""
    configure_logging()
    result = run_discovery(
        config_path=Path(config).resolve(),
        refresh=refresh,
        reuse_existing=reuse_existing,
    )
    summary = {
        "stage": "discover-products",
        "reused_existing": result.manifest.reused_existing,
        "total_queries": result.manifest.total_queries,
        "total_candidates_raw": result.manifest.total_candidates_raw,
        "total_candidates_saved": result.manifest.total_candidates_saved,
        "failure_counts": result.manifest.failure_counts,
    }
    typer.echo("Discovery summary:")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.manifest.output_dir}")
    typer.echo(f"- {result.candidate_queries_path}")
    typer.echo(f"- {result.candidates_path}")
    typer.echo(f"- {result.raw_html_dir}")
    typer.echo("")
    typer.echo("Manual review for final 3 products:")
    typer.echo("1. Open data/discovery/candidates.jsonl and sort candidates by ranking_score.")
    typer.echo(
        "2. Visit top canonical_url entries and verify category diversity "
        "and public review quality."
    )
    typer.echo(
        "3. Record the final three selected products and rationale in your report artifacts."
    )


@app.command("scrape-product")
def scrape_product(
    url: str = typer.Option(..., "--url", help="Public product page URL to scrape."),
    max_reviews: int = typer.Option(
        100,
        help="Maximum number of public reviews to retain.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Re-scrape the product page and reviews.",
    ),
    reuse_existing: bool = typer.Option(
        True,
        "--reuse-existing/--no-reuse-existing",
        help="Reuse existing raw artifacts when they are already complete.",
    ),
) -> None:
    """Scrape one public product page and its reviews."""
    configure_logging()
    result = run_scrape_product(
        url=url,
        max_reviews=max_reviews,
        refresh=refresh,
        reuse_existing=reuse_existing,
    )
    summary = {
        "stage": "scrape-product",
        "product_slug": result.report.product_slug,
        "title": result.report.title,
        "status": result.report.status,
        "reused_existing": result.report.reused_existing,
        "pages_fetched": result.report.pages_fetched,
        "collected_review_count": result.report.collected_review_count,
        "visible_review_count": result.report.visible_review_count,
        "image_count": result.report.image_count,
        "failure_counts": result.report.failure_counts,
    }
    typer.echo("Scrape summary:")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.output_dir}")
    typer.echo(f"- {result.output_dir / 'product_meta.json'}")
    typer.echo(f"- {result.output_dir / 'description.json'}")
    typer.echo(f"- {result.output_dir / 'reviews.jsonl'}")
    typer.echo(f"- {result.output_dir / 'images'}")
    typer.echo(f"- {result.output_dir / 'raw_html'}")
    typer.echo(f"- {result.output_dir / 'scrape_report.json'}")


@app.command("scrape-all")
def scrape_all(
    input: str = typer.Option(
        "../data/selected_products.jsonl",
        help="Path to the selected products JSONL file.",
    ),
    max_reviews: int = typer.Option(
        100,
        help="Maximum number of public reviews to retain per product.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Re-scrape all previously selected products.",
    ),
    reuse_existing: bool = typer.Option(
        True,
        "--reuse-existing/--no-reuse-existing",
        help="Reuse existing raw artifacts when they are already complete.",
    ),
) -> None:
    """Scrape all selected products and reviews."""
    configure_logging()
    result = run_scrape_all(
        input_path=Path(input).resolve(),
        max_reviews=max_reviews,
        refresh=refresh,
        reuse_existing=reuse_existing,
    )
    summary = {
        "stage": "scrape-all",
        "product_count": result.manifest.product_count,
        "reused_existing": result.manifest.reused_existing,
        "statuses": {
            entry.product_slug: {
                "status": entry.status,
                "review_count": entry.review_count,
                "image_count": entry.image_count,
            }
            for entry in result.manifest.entries
        },
    }
    typer.echo("Scrape summary:")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.manifest.output_dir}")
    typer.echo(f"- {result.manifest_path}")
    typer.echo("")
    typer.echo("Manual review for final 3 products:")
    typer.echo(
        "1. Open data/raw/raw_manifest.json to compare completeness, review counts, "
        "and image counts."
    )
    typer.echo(
        "2. Inspect each product folder under data/raw/<product_slug>/ for raw HTML, "
        "images, and scrape reports."
    )
    typer.echo(
        "3. Use product_meta.json and reviews.jsonl as the default downstream inputs "
        "unless you pass --refresh."
    )


@app.command("build-corpus")
def build_corpus(
    raw_dir: str = typer.Option(
        "../data/raw",
        help="Directory containing durable raw scrape artifacts.",
    ),
    output_dir: str = typer.Option(
        "../data/processed",
        help="Directory where cleaned reusable corpora should be written.",
    ),
    input: str = typer.Option(
        "../data/selected_products.jsonl",
        help="Path to the selected products JSONL file.",
    ),
    min_review_count: int | None = typer.Option(
        None,
        help="Minimum cleaned review count required per product for Q1.",
    ),
) -> None:
    """Build the durable textual corpus used by downstream stages."""
    configure_logging()
    result = build_processed_corpus(
        raw_dir=Path(raw_dir).resolve(),
        output_dir=Path(output_dir).resolve(),
        selected_products_path=Path(input).resolve(),
        min_review_count=min_review_count,
    )
    summary = {
        "stage": "build-corpus",
        "processed_products": result.manifest.product_count,
        "min_review_count_threshold": result.manifest.min_review_count_threshold,
        "q1_passed": result.q1_validation.passed,
        "entries": {
            entry.product_slug: {
                "cleaned_review_count": entry.cleaned_review_count,
                "valid_image_count": entry.valid_image_count,
                "description_char_count": entry.description_char_count,
                "passes_q1": entry.passes_q1,
            }
            for entry in result.manifest.entries
        },
    }
    typer.echo("Processed corpus summary:")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.manifest.output_dir}")
    typer.echo(f"- {result.manifest_path}")
    typer.echo(f"- {result.q1_summary_path}")
    typer.echo(f"- {DOCS_DIR / 'q1_selection_rationale_template.md'}")
    if not result.q1_validation.passed:
        typer.echo("")
        typer.echo("Q1 validation issues:")
        for issue in result.q1_validation.issues:
            typer.echo(f"- {issue}")
        raise typer.Exit(code=1)


@app.command("extract-visual-profile")
def extract_visual_profile_command(
    product: str = typer.Option(..., "--product", help="Processed product slug to analyze."),
    mode: str = typer.Option(
        ...,
        "--mode",
        help="Analysis mode: baseline_description_only or review_informed_rag.",
    ),
) -> None:
    """Extract visual profiles from saved descriptions and reviews."""
    configure_logging()
    result = extract_visual_profile(
        product_slug=product,
        mode=mode,
    )
    summary = {
        "stage": "extract-visual-profile",
        "product_slug": result.product_slug,
        "mode": result.mode,
        "high_confidence_count": len(result.profile.high_confidence_visual_attributes),
        "low_confidence_count": len(result.profile.low_confidence_or_conflicting_attributes),
        "mismatch_count": len(result.profile.common_mismatches_between_expectation_and_reality),
        "negative_constraint_count": len(result.profile.negative_constraints),
    }
    typer.echo("Visual profile summary:")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.profile_path}")
    typer.echo(f"- {result.retrieval_evidence_path}")
    typer.echo(f"- {result.llm_trace_path}")


@app.command("generate-images")
def generate_images(
    product: str | None = typer.Option(
        None,
        "--product",
        help="Processed product slug to generate images for.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Image model to use: openai or stability. Defaults to both.",
    ),
    all_products: bool = typer.Option(
        False,
        "--all",
        help="Generate images for every product that has both required visual profiles.",
    ),
    count: int = typer.Option(
        4,
        "--count",
        help="Number of final images to generate per product/model.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Re-generate images even if a complete manifest already exists.",
    ),
    reuse_existing: bool = typer.Option(
        True,
        "--reuse-existing/--no-reuse-existing",
        help="Reuse complete on-disk generation artifacts by default.",
    ),
) -> None:
    """Generate comparison-ready images with API-only models."""
    configure_logging()
    if bool(product) == bool(all_products):
        raise typer.BadParameter("Choose exactly one of --product or --all.")

    products = [product] if product else list_generation_ready_products()
    if not products:
        raise typer.BadParameter(
            "No generation-ready products were found under outputs/visual_profiles."
        )

    models = [model] if model else ["openai", "stability"]
    summaries: list[dict[str, object]] = []
    saved_paths: list[str] = []
    for product_slug in products:
        for model_name in models:
            result = generate_images_for_product(
                product_slug=product_slug,
                model_name=model_name,
                count=count,
                refresh=refresh,
                reuse_existing=reuse_existing,
            )
            summaries.append(
                {
                    "product_slug": product_slug,
                    "model_name": model_name,
                    "status": result.manifest.status,
                    "reused_existing": result.manifest.reused_existing,
                    "pilot_count": len(result.manifest.pilot_generation.images),
                    "final_count": len(result.manifest.final_generation.images),
                }
            )
            saved_paths.extend(
                [
                    str(result.manifest_path),
                    str(result.prompt_versions_path),
                ]
            )

    typer.echo("Image generation summary:")
    typer.echo(json.dumps({"runs": summaries}, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    for path in saved_paths:
        typer.echo(f"- {path}")


@app.command("evaluate-images")
def evaluate_images(
    product: str | None = typer.Option(
        None,
        "--product",
        help="Product slug to evaluate.",
    ),
    all_products: bool = typer.Option(
        False,
        "--all",
        help="Evaluate all products with raw artifacts.",
    ),
    vision_assisted: bool = typer.Option(
        False,
        "--vision-assisted",
        help="Run optional vision-assisted evaluation via API.",
    ),
) -> None:
    """Evaluate generated images against reference product images."""
    configure_logging()
    if bool(product) == bool(all_products):
        raise typer.BadParameter("Choose exactly one of --product or --all.")

    products = [product] if product else list_evaluation_ready_products()
    if not products:
        raise typer.BadParameter("No evaluation-ready products were found under data/raw.")

    summaries: list[dict[str, object]] = []
    saved_paths: list[str] = []
    for product_slug in products:
        result = evaluate_images_for_product(
            product_slug=product_slug,
            vision_assisted=vision_assisted,
        )
        summaries.append(
            {
                "product_slug": product_slug,
                "status": result.summary["status"],
                "comparison_panel_count": result.summary["comparison_panel_count"],
                "available_models": result.summary["available_models"],
                "missing_models": result.summary["missing_models"],
                "vision_assisted_status": result.summary["vision_assisted_status"],
            }
        )
        saved_paths.extend(
            [
                str(result.human_score_sheet_path),
                str(result.vision_assisted_eval_path),
                str(result.summary_path),
                str(result.comparison_panels_manifest_path),
            ]
        )

    typer.echo("Evaluation summary:")
    typer.echo(json.dumps({"runs": summaries}, indent=2))
    typer.echo("")
    typer.echo("Artifacts saved to:")
    for path in saved_paths:
        typer.echo(f"- {path}")


@app.command("run-workflow")
def run_workflow(
    product: str | None = typer.Option(
        None,
        "--product",
        help="Run the full agentic workflow for one product slug.",
    ),
    all_products: bool = typer.Option(
        False,
        "--all",
        help="Run the full agentic workflow for every artifact-backed product.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Recompute stages instead of reusing saved downstream artifacts.",
    ),
    reuse_existing: bool = typer.Option(
        True,
        "--reuse-existing/--no-reuse-existing",
        help="Reuse existing downstream artifacts whenever possible.",
    ),
    vision_assisted: bool = typer.Option(
        False,
        "--vision-assisted",
        help="Enable optional vision-assisted evaluation during the evaluation stage.",
    ),
) -> None:
    """Run the Q4 multi-agent workflow and save an inspectable trace."""
    configure_logging()
    if bool(product) == bool(all_products):
        raise typer.BadParameter("Choose exactly one of --product or --all.")

    result = run_agentic_workflow(
        product_slug=product,
        run_all=all_products,
        refresh=refresh,
        reuse_existing=reuse_existing,
        vision_assisted=vision_assisted,
    )
    typer.echo("Workflow summary:")
    typer.echo(
        json.dumps(
            {
                "run_id": result.summary.run_id,
                "scope": result.summary.scope,
                "status": result.summary.status,
                "products": result.summary.products,
                "stages": [
                    {
                        "stage": stage.stage_key,
                        "agent": stage.agent_name,
                        "status": stage.status,
                        "completed_count": stage.completed_count,
                        "total_count": stage.total_count,
                    }
                    for stage in result.summary.stages
                ],
            },
            indent=2,
        )
    )
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.trace_path}")
    typer.echo(f"- {result.stage_status_path}")
    typer.echo(f"- {result.artifact_links_path}")


@app.command("verify-artifacts")
def verify_artifacts(
    stage: str = typer.Option(
        "full",
        help="Validation stage to run: q1, q2, q3, q4, or full.",
    ),
    processed_dir: str = typer.Option(
        "../data/processed",
        help="Processed artifact root used for Q1 validation.",
    ),
    input: str = typer.Option(
        "../data/selected_products.jsonl",
        help="Selected products JSONL path used for Q1 validation.",
    ),
    min_review_count: int | None = typer.Option(
        None,
        help="Minimum cleaned review count required per product for Q1.",
    ),
    frontend_dir: str = typer.Option(
        "../frontend",
        help="Frontend root used for build verification during full checks.",
    ),
    skip_frontend_build: bool = typer.Option(
        False,
        help="Skip `npm run build` during full verification.",
    ),
) -> None:
    """Verify repository artifacts against Q1 through Q4 requirements."""
    configure_logging()
    result = verify_repository(
        stage=stage,  # type: ignore[arg-type]
        processed_dir=Path(processed_dir).resolve(),
        selected_products_path=Path(input).resolve(),
        min_review_count=min_review_count,
        frontend_root=Path(frontend_dir).resolve(),
        run_frontend_build=not skip_frontend_build,
    )
    typer.echo(f"{stage.upper()} verification summary:")
    typer.echo(f"- Status: {'PASS' if result.passed else 'FAIL'}")
    for check_name, check in result.summary["checks"].items():
        typer.echo(f"- {check_name}: {'PASS' if check.get('passed') else 'FAIL'}")
        for issue in check.get("issues", []):
            typer.echo(f"  - {issue}")
    typer.echo("")
    typer.echo("Machine-readable JSON:")
    typer.echo(json.dumps(result.summary, indent=2))
    if not result.passed:
        raise typer.Exit(code=1)


@app.command("build-submission-package")
def build_submission_package_command(
    output_dir: str = typer.Option(
        "../submission_package",
        help="Directory where the submission package should be assembled.",
    ),
) -> None:
    """Build a submission-ready package with the required code and artifacts."""
    configure_logging()
    result = build_submission_package(output_dir=Path(output_dir).resolve())
    typer.echo("Submission package summary:")
    typer.echo(
        json.dumps(
            {
                "output_dir": str(result.output_dir),
                "file_count": len(result.copied_paths),
                "manifest_path": str(result.manifest_path),
            },
            indent=2,
        )
    )
    typer.echo("")
    typer.echo("Artifacts saved to:")
    typer.echo(f"- {result.output_dir}")
    typer.echo(f"- {result.manifest_path}")


@app.command("serve-api")
def serve_api() -> None:
    """Run the FastAPI server with current settings."""
    settings = get_settings()
    typer.echo(
        json.dumps(
            {
                "stage": "serve-api",
                "api_base_url": settings.frontend_api_base_url,
                "message": (
                    "Run `uvicorn app.main:app --reload --port 8000` to start the API server."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
