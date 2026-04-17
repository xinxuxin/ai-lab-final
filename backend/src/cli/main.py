"""Typer CLI for stage-by-stage workflow execution."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.collectors.discovery import run_discovery
from app.collectors.product_pages import run_scrape_all, run_scrape_product
from app.config.settings import get_settings
from app.utils.logging import configure_logging
from app.workflow.orchestrator import plan_workflow

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
def build_corpus() -> None:
    """Build the durable textual corpus used by downstream stages."""
    _print_placeholder("build-corpus")


@app.command("extract-visual-profile")
def extract_visual_profile() -> None:
    """Extract visual profiles from saved descriptions and reviews."""
    _print_placeholder("extract-visual-profile")


@app.command("generate-images")
def generate_images() -> None:
    """Generate comparison-ready images with API-only models."""
    _print_placeholder("generate-images")


@app.command("evaluate-images")
def evaluate_images() -> None:
    """Evaluate generated images against reference product images."""
    _print_placeholder("evaluate-images")


@app.command("run-workflow")
def run_workflow() -> None:
    """Run the staged agentic workflow end-to-end."""
    traces = [trace.model_dump(mode="json") for trace in plan_workflow()]
    typer.echo(json.dumps({"workflow": traces}, indent=2))


@app.command("verify-artifacts")
def verify_artifacts(
    path: str = typer.Option(
        "../artifacts",
        help="Artifacts root to validate.",
    )
) -> None:
    """Verify that expected artifact directories exist."""
    artifact_root = Path(path).resolve()
    typer.echo(
        json.dumps(
            {
                "stage": "verify-artifacts",
                "exists": artifact_root.exists(),
                "path": str(artifact_root),
            },
            indent=2,
        )
    )


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
                    "Run `uvicorn app.main:app --reload --port 8000` " "to start the API server."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
