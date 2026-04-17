"""Public product-page scraper adapters and orchestration."""

from app.collectors.product_pages.service import (
    ProductScrapeError,
    ProductScrapeRunResult,
    ScrapeAllRunResult,
    load_selected_products,
    run_scrape_all,
    run_scrape_product,
)

__all__ = [
    "ProductScrapeError",
    "ProductScrapeRunResult",
    "ScrapeAllRunResult",
    "load_selected_products",
    "run_scrape_all",
    "run_scrape_product",
]
