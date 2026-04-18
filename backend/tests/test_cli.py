"""CLI smoke tests."""

from pathlib import Path

from pydantic import HttpUrl, TypeAdapter
from pytest import MonkeyPatch
from typer.testing import CliRunner

from app.collectors.product_pages.service import ProductScrapeRunResult, ScrapeAllRunResult
from app.models.schemas import (
    ArtifactCompleteness,
    DiscoveryManifest,
    ProcessedManifest,
    ProcessedManifestEntry,
    Q1ValidationResult,
    RawManifest,
    RawManifestEntry,
    ScrapeReport,
)
from app.services.corpus import BuildCorpusResult
from cli.main import app

runner = CliRunner()
HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def test_cli_discover_products_smoke(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """Discover command should run successfully."""
    config_path = tmp_path / "queries.yaml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "marketplaces:",
                "  - bestbuy",
                "queries:",
                "  - query: desk lamp",
                "    category_guess: lighting",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "data" / "discovery"
    output_dir.mkdir(parents=True)
    candidate_queries_path = output_dir / "candidate_queries.json"
    candidate_queries_path.write_text("[]", encoding="utf-8")
    candidates_path = output_dir / "candidates.jsonl"
    candidates_path.write_text("", encoding="utf-8")
    raw_html_dir = output_dir / "raw_html"
    raw_html_dir.mkdir()

    from app.collectors.discovery.service import DiscoveryRunResult

    def fake_run_discovery(
        config_path: Path,
        *,
        refresh: bool = False,
        reuse_existing: bool = True,
        output_dir: Path | None = None,
        settings: object | None = None,
    ) -> DiscoveryRunResult:
        del refresh, reuse_existing, settings
        return DiscoveryRunResult(
            manifest=DiscoveryManifest(
                config_path=str(config_path),
                output_dir=str(output_dir or tmp_path / "data" / "discovery"),
                candidate_queries_path=str(candidate_queries_path),
                candidates_path=str(candidates_path),
                raw_html_dir=str(raw_html_dir),
                total_queries=1,
                total_candidates_raw=2,
                total_candidates_saved=1,
                failure_counts={
                    "blocked": 0,
                    "parse_failed": 0,
                    "no_results": 0,
                    "duplicate_removed": 1,
                },
                marketplaces=["bestbuy"],
            ),
            candidates=[],
            candidate_queries_path=candidate_queries_path,
            candidates_path=candidates_path,
            raw_html_dir=raw_html_dir,
        )

    monkeypatch.setattr("cli.main.run_discovery", fake_run_discovery)
    result = runner.invoke(
        app,
        [
            "discover-products",
            "--config",
            str(config_path),
            "--reuse-existing",
        ],
    )
    assert result.exit_code == 0
    assert "Discovery summary:" in result.stdout


def test_cli_scrape_all_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Scrape-all command should print a durable artifact summary."""
    manifest_path = tmp_path / "data" / "raw" / "raw_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_run_scrape_all(
        *,
        input_path: Path,
        max_reviews: int = 100,
        refresh: bool = False,
        reuse_existing: bool = True,
        output_dir: Path | None = None,
        settings: object | None = None,
    ) -> ScrapeAllRunResult:
        del input_path, max_reviews, refresh, reuse_existing, output_dir, settings
        report = ScrapeReport(
            product_slug="sample-product-1",
            product_id="123",
            source_url=HTTP_URL_ADAPTER.validate_python("https://www.target.com/p/sample/-/A-123"),
            category="lighting",
            marketplace="target",
            title="Sample Product",
            status="completed",
            artifact_completeness=ArtifactCompleteness(
                product_meta=True,
                description=True,
                reviews=True,
                images=True,
                raw_html=True,
                scrape_report=True,
            ),
        )
        return ScrapeAllRunResult(
            manifest=RawManifest(
                input_path=str(tmp_path / "data" / "selected_products.jsonl"),
                output_dir=str(tmp_path / "data" / "raw"),
                product_count=1,
                reused_existing=False,
                entries=[
                    RawManifestEntry(
                        product_slug="sample-product-1",
                        product_id="123",
                        source_url=HTTP_URL_ADAPTER.validate_python(
                            "https://www.target.com/p/sample/-/A-123"
                        ),
                        category="lighting",
                        artifact_completeness=report.artifact_completeness,
                        pages_fetched=2,
                        review_count=8,
                        image_count=3,
                        status="completed",
                    )
                ],
            ),
            manifest_path=manifest_path,
            product_results=[
                ProductScrapeRunResult(
                    manifest_entry=RawManifestEntry(
                        product_slug="sample-product-1",
                        product_id="123",
                        source_url=HTTP_URL_ADAPTER.validate_python(
                            "https://www.target.com/p/sample/-/A-123"
                        ),
                        category="lighting",
                        artifact_completeness=report.artifact_completeness,
                        pages_fetched=2,
                        review_count=8,
                        image_count=3,
                        status="completed",
                    ),
                    report=report,
                    output_dir=tmp_path / "data" / "raw" / "sample-product-1",
                )
            ],
        )

    monkeypatch.setattr("cli.main.run_scrape_all", fake_run_scrape_all)
    result = runner.invoke(
        app,
        ["scrape-all", "--input", str(tmp_path / "selected_products.jsonl")],
    )
    assert result.exit_code == 0
    assert "Scrape summary:" in result.stdout


def test_cli_build_corpus_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Build-corpus command should print processed summary output."""
    manifest_path = tmp_path / "data" / "processed" / "manifest.json"
    q1_summary_path = tmp_path / "docs" / "q1_summary.md"

    def fake_build_processed_corpus(
        *,
        raw_dir: Path | None = None,
        output_dir: Path | None = None,
        selected_products_path: Path | None = None,
        min_review_count: int | None = None,
        settings: object | None = None,
    ) -> BuildCorpusResult:
        del raw_dir, output_dir, selected_products_path, min_review_count, settings
        return BuildCorpusResult(
            manifest=ProcessedManifest(
                raw_manifest_path=str(tmp_path / "data" / "raw" / "raw_manifest.json"),
                selected_products_path=str(tmp_path / "data" / "selected_products.jsonl"),
                output_dir=str(tmp_path / "data" / "processed"),
                product_count=3,
                min_review_count_threshold=5,
                entries=[
                    ProcessedManifestEntry(
                        product_slug="sample-product-1",
                        product_id="123",
                        title="Sample Product",
                        category="lighting",
                        source_url=HTTP_URL_ADAPTER.validate_python(
                            "https://www.target.com/p/sample/-/A-123"
                        ),
                        processed_dir=str(tmp_path / "data" / "processed" / "sample-product-1"),
                        cleaned_review_count=8,
                        valid_image_count=3,
                        description_char_count=120,
                        passes_q1=True,
                    )
                ],
            ),
            manifest_path=manifest_path,
            q1_validation=Q1ValidationResult(
                passed=True,
                selected_products_count=3,
                distinct_categories_count=3,
                min_review_count_threshold=5,
                per_product_review_counts={"sample-product-1": 8},
                per_product_image_counts={"sample-product-1": 3},
            ),
            q1_summary_path=q1_summary_path,
        )

    monkeypatch.setattr("cli.main.build_processed_corpus", fake_build_processed_corpus)
    result = runner.invoke(app, ["build-corpus"])
    assert result.exit_code == 0
    assert "Processed corpus summary:" in result.stdout


def test_cli_verify_artifacts_q1_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Q1 verification command should print human and machine-readable output."""

    def fake_validate_q1_from_disk(
        *,
        processed_dir: Path | None = None,
        selected_products_path: Path | None = None,
        min_review_count: int | None = None,
        settings: object | None = None,
    ) -> Q1ValidationResult:
        del processed_dir, selected_products_path, min_review_count, settings
        return Q1ValidationResult(
            passed=True,
            selected_products_count=3,
            distinct_categories_count=3,
            min_review_count_threshold=5,
            per_product_review_counts={"sample-product-1": 8},
            per_product_image_counts={"sample-product-1": 3},
            notes=["All strict Q1 checks passed."],
        )

    monkeypatch.setattr("cli.main.validate_q1_from_disk", fake_validate_q1_from_disk)
    result = runner.invoke(app, ["verify-artifacts", "--stage", "q1"])
    assert result.exit_code == 0
    assert "Q1 verification summary:" in result.stdout
    assert "Machine-readable JSON:" in result.stdout
