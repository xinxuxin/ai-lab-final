"""CLI smoke tests."""

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


def test_cli_discover_products_smoke() -> None:
    """Discover command should run successfully."""
    result = runner.invoke(app, ["discover-products"])
    assert result.exit_code == 0
    assert "discover-products" in result.stdout
