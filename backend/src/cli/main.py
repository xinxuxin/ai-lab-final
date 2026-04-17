"""Typer CLI for stage-by-stage workflow execution."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.config.settings import get_settings
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
    refresh: bool = typer.Option(
        False,
        help="Re-run discovery instead of using cached artifacts.",
    )
) -> None:
    """Discover candidate product links and save durable artifacts."""
    _print_placeholder("discover-products", refresh=refresh)


@app.command("scrape-product")
def scrape_product(
    product_url: str,
    refresh: bool = typer.Option(
        False,
        help="Re-scrape the product page and reviews.",
    ),
) -> None:
    """Scrape one public product page and its reviews."""
    typer.echo(
        json.dumps(
            {
                "stage": "scrape-product",
                "product_url": product_url,
                "refresh": refresh,
            },
            indent=2,
        )
    )


@app.command("scrape-all")
def scrape_all(
    refresh: bool = typer.Option(
        False,
        help="Re-scrape all previously selected products.",
    )
) -> None:
    """Scrape all selected products and reviews."""
    _print_placeholder("scrape-all", refresh=refresh)


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
        "../../artifacts",
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
                    "Run `uvicorn app.main:app --reload --port 8000` "
                    "to start the API server."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
