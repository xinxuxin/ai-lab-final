"""CLI smoke tests."""

from pathlib import Path

from pydantic import HttpUrl, TypeAdapter
from pytest import MonkeyPatch
from typer.testing import CliRunner

from app.collectors.product_pages.service import ProductScrapeRunResult, ScrapeAllRunResult
from app.models.schemas import (
    ArtifactCompleteness,
    DiscoveryManifest,
    GeneratedImageFile,
    GenerationManifest,
    GenerationRecord,
    ProcessedManifest,
    ProcessedManifestEntry,
    PromptVersion,
    Q1ValidationResult,
    RawManifest,
    RawManifestEntry,
    ScrapeReport,
    VisualProfile,
)
from app.services.corpus import BuildCorpusResult
from app.services.evaluation import EvaluateImagesResult
from app.services.image_generation import GenerateImagesResult
from app.services.visual_profiles import ExtractVisualProfileResult
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
        docs_root: Path | None = None,
        min_review_count: int | None = None,
        settings: object | None = None,
    ) -> BuildCorpusResult:
        del raw_dir, output_dir, selected_products_path, docs_root, min_review_count, settings
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


def test_cli_extract_visual_profile_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Extract-visual-profile command should print saved output paths."""
    output_dir = tmp_path / "outputs" / "visual_profiles" / "sample-product"
    output_dir.mkdir(parents=True, exist_ok=True)

    def fake_extract_visual_profile(
        *,
        product_slug: str,
        mode: str,
        processed_root: Path | None = None,
        outputs_root: Path | None = None,
        llm_client: object | None = None,
        settings: object | None = None,
    ) -> ExtractVisualProfileResult:
        del processed_root, outputs_root, llm_client, settings
        return ExtractVisualProfileResult(
            product_slug=product_slug,
            mode=mode,
            profile=VisualProfile(
                product_name="Sample Product",
                category="lighting",
                high_confidence_visual_attributes=[],
                low_confidence_or_conflicting_attributes=[],
                common_mismatches_between_expectation_and_reality=[],
                prompt_ready_description="A grounded sample prompt.",
                negative_constraints=[],
            ),
            profile_path=output_dir / f"{mode}.json",
            retrieval_evidence_path=output_dir / "retrieval_evidence.json",
            llm_trace_path=output_dir / "llm_trace.json",
            trace_steps=[],
        )

    monkeypatch.setattr("cli.main.extract_visual_profile", fake_extract_visual_profile)
    result = runner.invoke(
        app,
        [
            "extract-visual-profile",
            "--product",
            "sample-product",
            "--mode",
            "baseline_description_only",
        ],
    )
    assert result.exit_code == 0
    assert "Visual profile summary:" in result.stdout


def test_cli_generate_images_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Generate-images command should print manifest and prompt-version paths."""
    output_dir = tmp_path / "outputs" / "generated_images" / "sample-product" / "openai"
    output_dir.mkdir(parents=True, exist_ok=True)

    def fake_generate_images_for_product(
        *,
        product_slug: str,
        model_name: str,
        count: int = 4,
        processed_root: Path | None = None,
        profiles_root: Path | None = None,
        outputs_root: Path | None = None,
        settings: object | None = None,
        adapter: object | None = None,
        refresh: bool = False,
        reuse_existing: bool = True,
    ) -> GenerateImagesResult:
        del (
            count,
            processed_root,
            profiles_root,
            outputs_root,
            settings,
            adapter,
            refresh,
            reuse_existing,
        )
        prompt_version = PromptVersion(
            prompt_version_id="sample-prompt",
            product_id="123",
            provider=model_name,
            model_name=model_name,
            strategy="pilot",
            prompt_source_mode="baseline_description_only",
            prompt_text="A grounded product prompt.",
        )
        pilot_generation = GenerationRecord(
            generation_id="pilot-1",
            product_id="123",
            provider=model_name,
            model_name=model_name,
            stage="pilot",
            prompt_version_id=prompt_version.prompt_version_id,
            prompt_source_mode=prompt_version.prompt_source_mode,
            output_paths=[str(output_dir / "pilot" / "image_01.png")],
            images=[
                GeneratedImageFile(
                    filename="image_01.png",
                    local_path=str(output_dir / "pilot" / "image_01.png"),
                    sha256="abc",
                    width=512,
                    height=512,
                    byte_size=128,
                    content_type="image/png",
                )
            ],
            status="completed",
        )
        final_generation = GenerationRecord(
            generation_id="final-1",
            product_id="123",
            provider=model_name,
            model_name=model_name,
            stage="final",
            prompt_version_id="sample-final",
            prompt_source_mode="review_informed_rag",
            output_paths=[str(output_dir / "final" / "image_01.png")],
            images=[
                GeneratedImageFile(
                    filename="image_01.png",
                    local_path=str(output_dir / "final" / "image_01.png"),
                    sha256="def",
                    width=512,
                    height=512,
                    byte_size=128,
                    content_type="image/png",
                )
            ],
            status="completed",
        )
        return GenerateImagesResult(
            product_slug=product_slug,
            model_name=model_name,
            manifest=GenerationManifest(
                product_slug=product_slug,
                product_id="123",
                product_name="Sample Product",
                provider=model_name,
                model_name=model_name,
                output_dir=str(output_dir),
                prompt_versions_path=str(output_dir / "prompt_versions.json"),
                pilot_generation=pilot_generation,
                final_generation=final_generation,
                status="completed",
            ),
            manifest_path=output_dir / "generation_manifest.json",
            prompt_versions_path=output_dir / "prompt_versions.json",
        )

    monkeypatch.setattr("cli.main.generate_images_for_product", fake_generate_images_for_product)
    result = runner.invoke(
        app,
        [
            "generate-images",
            "--product",
            "sample-product",
            "--model",
            "openai",
            "--count",
            "4",
        ],
    )
    assert result.exit_code == 0
    assert "Image generation summary:" in result.stdout


def test_cli_evaluate_images_smoke(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Evaluate-images command should print saved evaluation artifact paths."""
    output_dir = tmp_path / "outputs" / "evaluations" / "sample-product"
    output_dir.mkdir(parents=True, exist_ok=True)

    def fake_evaluate_images_for_product(
        *,
        product_slug: str,
        raw_root: Path | None = None,
        generated_root: Path | None = None,
        outputs_root: Path | None = None,
        settings: object | None = None,
        vision_assisted: bool = False,
        llm_client: object | None = None,
    ) -> EvaluateImagesResult:
        del raw_root, generated_root, outputs_root, settings, vision_assisted, llm_client
        return EvaluateImagesResult(
            product_slug=product_slug,
            evaluation_dir=output_dir,
            human_score_sheet_path=output_dir / "human_score_sheet.csv",
            vision_assisted_eval_path=output_dir / "vision_assisted_eval.json",
            summary_path=output_dir / "summary.json",
            comparison_panels_manifest_path=output_dir / "comparison_panels_manifest.json",
            summary={
                "status": "human_scoring_ready",
                "comparison_panel_count": 4,
                "available_models": ["openai"],
                "missing_models": ["stability"],
                "vision_assisted_status": "not_run",
            },
        )

    monkeypatch.setattr("cli.main.evaluate_images_for_product", fake_evaluate_images_for_product)
    result = runner.invoke(app, ["evaluate-images", "--product", "sample-product"])
    assert result.exit_code == 0
    assert "Evaluation summary:" in result.stdout
