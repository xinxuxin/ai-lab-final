"""Backend import smoke tests."""

from app.collectors.discovery import run_discovery
from app.collectors.product_pages import run_scrape_all, run_scrape_product
from app.main import app
from cli.main import app as cli_app


def test_import_smoke() -> None:
    """Ensure key modules import successfully."""
    assert app.title == "Generating Product Image from Customer Reviews"
    assert cli_app.info.help is not None
    assert callable(run_discovery)
    assert callable(run_scrape_product)
    assert callable(run_scrape_all)
