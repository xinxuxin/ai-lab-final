"""CLI smoke tests."""

from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from app.models.schemas import DiscoveryManifest
from cli.main import app

runner = CliRunner()


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
