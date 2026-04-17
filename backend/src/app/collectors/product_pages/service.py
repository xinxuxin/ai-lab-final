"""One-time product scraping orchestration with durable artifact storage."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

import httpx
import structlog
from PIL import Image, UnidentifiedImageError
from pydantic import HttpUrl, TypeAdapter
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.collectors.product_pages.base import (
    FAILURE_BLOCKED,
    FAILURE_IMAGE_DOWNLOAD_FAILED,
    FAILURE_NO_REVIEWS_ACCESSIBLE,
    FAILURE_PARSE_FAILED,
    FAILURE_PARTIAL_SUCCESS,
    ParsedProduct,
    ProductPageAdapter,
    ProductScrapeSnapshot,
)
from app.collectors.product_pages.target import TargetProductPageAdapter
from app.config.settings import Settings, get_settings
from app.models.schemas import (
    ArtifactCompleteness,
    ProductSeed,
    RawManifest,
    RawManifestEntry,
    ReviewRecord,
    ScrapeReport,
)
from app.utils.artifacts import DATA_DIR, ensure_project_dirs

logger = structlog.get_logger(__name__)

RAW_DATA_DIR = DATA_DIR / "raw"
HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)

ADAPTERS: dict[str, type[ProductPageAdapter]] = {
    "target": TargetProductPageAdapter,
}


class ProductScrapeError(RuntimeError):
    """Raised when the product scraping stage cannot complete."""


@dataclass(slots=True)
class ProductScrapeRunResult:
    """Return value for one product scrape."""

    manifest_entry: RawManifestEntry
    report: ScrapeReport
    output_dir: Path


@dataclass(slots=True)
class ScrapeAllRunResult:
    """Return value for the full selected-product scrape run."""

    manifest: RawManifest
    manifest_path: Path
    product_results: list[ProductScrapeRunResult]


def required_artifact_paths(product_dir: Path) -> dict[str, Path]:
    """Return the required artifact paths for one product scrape."""
    return {
        "product_meta": product_dir / "product_meta.json",
        "description": product_dir / "description.json",
        "reviews": product_dir / "reviews.jsonl",
        "images_dir": product_dir / "images",
        "raw_html_dir": product_dir / "raw_html",
        "scrape_report": product_dir / "scrape_report.json",
    }


def artifacts_complete(product_dir: Path) -> bool:
    """Check whether the durable raw product artifacts exist on disk."""
    paths = required_artifact_paths(product_dir)
    images_dir = paths["images_dir"]
    raw_html_dir = paths["raw_html_dir"]
    return (
        paths["product_meta"].exists()
        and paths["description"].exists()
        and paths["reviews"].exists()
        and paths["scrape_report"].exists()
        and images_dir.exists()
        and any(images_dir.iterdir())
        and raw_html_dir.exists()
        and any(raw_html_dir.iterdir())
    )


def load_selected_products(input_path: Path) -> list[ProductSeed]:
    """Load and validate the final selected product file."""
    seeds = [
        ProductSeed.model_validate_json(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(seeds) != 3:
        raise ProductScrapeError(
            f"selected_products.jsonl must contain exactly 3 products, found {len(seeds)}."
        )
    categories = {seed.category for seed in seeds}
    if len(categories) != 3:
        raise ProductScrapeError("Selected products must belong to 3 distinct categories.")
    return seeds


def run_scrape_all(
    *,
    input_path: Path,
    max_reviews: int = 100,
    refresh: bool = False,
    reuse_existing: bool = True,
    output_dir: Path | None = None,
    settings: Settings | None = None,
) -> ScrapeAllRunResult:
    """Scrape all selected products and write a durable raw manifest."""
    settings = settings or get_settings()
    ensure_project_dirs()
    selected_products = load_selected_products(input_path)
    resolved_output_dir = output_dir or RAW_DATA_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    product_results = [
        run_scrape_product(
            url=str(seed.product_url),
            category_hint=seed.category,
            max_reviews=max_reviews,
            refresh=refresh,
            reuse_existing=reuse_existing,
            output_dir=resolved_output_dir,
            settings=settings,
        )
        for seed in selected_products
    ]

    manifest = RawManifest(
        input_path=str(input_path.resolve()),
        output_dir=str(resolved_output_dir.resolve()),
        product_count=len(product_results),
        reused_existing=all(result.report.reused_existing for result in product_results),
        entries=[result.manifest_entry for result in product_results],
    )
    manifest_path = resolved_output_dir / "raw_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    if not manifest_path.exists():
        raise ProductScrapeError("raw_manifest.json was not written to disk.")

    return ScrapeAllRunResult(
        manifest=manifest,
        manifest_path=manifest_path,
        product_results=product_results,
    )


def run_scrape_product(
    *,
    url: str,
    max_reviews: int = 100,
    refresh: bool = False,
    reuse_existing: bool = True,
    output_dir: Path | None = None,
    settings: Settings | None = None,
    category_hint: str | None = None,
) -> ProductScrapeRunResult:
    """Scrape one public product page and persist durable raw artifacts."""
    settings = settings or get_settings()
    ensure_project_dirs()
    resolved_output_dir = output_dir or RAW_DATA_DIR
    adapter = _resolve_adapter(url)
    product_slug = adapter.product_slug(url)
    product_dir = resolved_output_dir / product_slug
    paths = required_artifact_paths(product_dir)

    if reuse_existing and not refresh and artifacts_complete(product_dir):
        report = ScrapeReport.model_validate_json(
            paths["scrape_report"].read_text(encoding="utf-8")
        )
        report.reused_existing = True
        manifest_entry = RawManifestEntry(
            product_slug=report.product_slug,
            product_id=report.product_id,
            source_url=report.source_url,
            category=report.category,
            scrape_timestamp=report.scrape_timestamp,
            artifact_completeness=report.artifact_completeness,
            pages_fetched=report.pages_fetched,
            review_count=report.collected_review_count,
            image_count=report.image_count,
            status=report.status,
            reused_existing=True,
            notes=report.notes,
        )
        logger.info("scrape_cache_reused", product_slug=product_slug, output_dir=str(product_dir))
        return ProductScrapeRunResult(
            manifest_entry=manifest_entry,
            report=report,
            output_dir=product_dir,
        )

    product_dir.mkdir(parents=True, exist_ok=True)
    paths["images_dir"].mkdir(parents=True, exist_ok=True)
    paths["raw_html_dir"].mkdir(parents=True, exist_ok=True)

    failure_counts: Counter[str] = Counter(
        {
            FAILURE_BLOCKED: 0,
            FAILURE_PARSE_FAILED: 0,
            FAILURE_NO_REVIEWS_ACCESSIBLE: 0,
            FAILURE_IMAGE_DOWNLOAD_FAILED: 0,
            FAILURE_PARTIAL_SUCCESS: 0,
        }
    )

    try:
        with httpx.Client(
            timeout=settings.scraping_timeout_seconds,
            follow_redirects=True,
            headers={"user-agent": settings.scraping_user_agent},
        ) as client:
            snapshot = _fetch_snapshot_with_retry(
                adapter=adapter,
                client=client,
                url=url,
                settings=settings,
            )
            parsed = adapter.parse_snapshot(
                snapshot=snapshot,
                max_reviews=max_reviews,
                min_review_chars=settings.scraping_min_review_chars,
            )
            time.sleep(settings.scraping_request_delay_seconds)

            _write_raw_fetches(
                raw_html_dir=paths["raw_html_dir"],
                page_html=snapshot.page_html,
                pdp_payload=snapshot.pdp_payload,
            )
            image_count = _download_images(
                client=client,
                image_urls=[candidate.url for candidate in parsed.image_candidates],
                images_dir=paths["images_dir"],
                settings=settings,
                failure_counts=failure_counts,
            )
    except httpx.HTTPStatusError as error:
        failure_counts[FAILURE_BLOCKED] += 1
        raise ProductScrapeError(f"Blocked or failed while scraping {url}: {error}") from error
    except httpx.HTTPError as error:
        failure_counts[FAILURE_BLOCKED] += 1
        raise ProductScrapeError(f"Network error while scraping {url}: {error}") from error
    except Exception as error:
        failure_counts[FAILURE_PARSE_FAILED] += 1
        raise ProductScrapeError(f"Parse failure while scraping {url}: {error}") from error

    if not parsed.reviews:
        failure_counts[FAILURE_NO_REVIEWS_ACCESSIBLE] += 1

    notes = list(parsed.notes)
    status: Literal["completed", "partial_success", "failed"] = "completed"
    if failure_counts[FAILURE_NO_REVIEWS_ACCESSIBLE] > 0:
        status = "partial_success"
        notes.append("No public review pagination was accessible; saved metadata and images only.")
    if image_count == 0:
        status = "failed"
        notes.append("No valid product images were downloaded.")
    elif failure_counts[FAILURE_IMAGE_DOWNLOAD_FAILED] > 0:
        status = "partial_success"
        notes.append("Some product images failed validation or download.")
    if parsed.visible_review_count is not None and len(parsed.reviews) < min(
        parsed.visible_review_count,
        max_reviews,
    ):
        status = "partial_success" if status != "failed" else status
        notes.append(
            "Collected fewer reviews than the visible public count because only "
            "the exposed most_recent block was available."
        )

    if status == "partial_success":
        failure_counts[FAILURE_PARTIAL_SUCCESS] += 1

    _write_product_meta(
        path=paths["product_meta"],
        parsed=parsed,
        category_hint=category_hint,
    )
    _write_description(path=paths["description"], parsed=parsed)
    _write_reviews(path=paths["reviews"], reviews=parsed.reviews)

    completeness = _compute_artifact_completeness(product_dir)
    report = ScrapeReport(
        product_slug=product_slug,
        product_id=parsed.product_id,
        source_url=HTTP_URL_ADAPTER.validate_python(parsed.source_url),
        category=category_hint or parsed.category,
        marketplace=parsed.marketplace,
        title=parsed.title,
        status=status,
        reused_existing=False,
        pages_fetched=len(snapshot.request_log),
        visible_review_count=parsed.visible_review_count,
        collected_review_count=len(parsed.reviews),
        image_count=image_count,
        failure_counts=dict(failure_counts),
        artifact_completeness=completeness,
        notes=notes,
    )
    paths["scrape_report"].write_text(report.model_dump_json(indent=2), encoding="utf-8")
    report.artifact_completeness = _compute_artifact_completeness(product_dir)
    paths["scrape_report"].write_text(report.model_dump_json(indent=2), encoding="utf-8")

    if not artifacts_complete(product_dir):
        raise ProductScrapeError(
            f"Scrape artifacts for {product_slug} are incomplete; refusing to report success."
        )

    manifest_entry = RawManifestEntry(
        product_slug=product_slug,
        product_id=parsed.product_id,
        source_url=HTTP_URL_ADAPTER.validate_python(parsed.source_url),
        category=category_hint or parsed.category,
        scrape_timestamp=report.scrape_timestamp,
        artifact_completeness=_compute_artifact_completeness(product_dir),
        pages_fetched=report.pages_fetched,
        review_count=report.collected_review_count,
        image_count=report.image_count,
        status=report.status,
        reused_existing=False,
        notes=notes,
    )
    logger.info(
        "scrape_product_completed",
        product_slug=product_slug,
        status=status,
        reviews=report.collected_review_count,
        images=image_count,
    )
    return ProductScrapeRunResult(
        manifest_entry=manifest_entry,
        report=report,
        output_dir=product_dir,
    )


def _resolve_adapter(url: str) -> ProductPageAdapter:
    """Select the correct marketplace adapter for a product URL."""
    for adapter_cls in ADAPTERS.values():
        adapter = adapter_cls()
        if adapter.matches_url(url):
            return adapter
    raise ProductScrapeError(f"No product-page adapter is configured for URL: {url}")


def _fetch_snapshot_with_retry(
    *,
    adapter: ProductPageAdapter,
    client: httpx.Client,
    url: str,
    settings: Settings,
) -> ProductScrapeSnapshot:
    """Fetch a product snapshot with retries and backoff."""
    retrying = Retrying(
        stop=stop_after_attempt(settings.scraping_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    for attempt in retrying:
        with attempt:
            return adapter.fetch_snapshot(
                client=client,
                url=url,
                user_agent=settings.scraping_user_agent,
                pricing_store_id=settings.target_pricing_store_id,
                api_key=settings.target_api_key,
            )
    raise ProductScrapeError(f"Unable to fetch product snapshot for {url}")


def _download_images(
    *,
    client: httpx.Client,
    image_urls: list[str],
    images_dir: Path,
    settings: Settings,
    failure_counts: Counter[str],
) -> int:
    """Download and validate product images."""
    saved_count = 0
    for index, image_url in enumerate(image_urls, start=1):
        try:
            content, image_suffix = _download_image_with_retry(
                client=client,
                image_url=image_url,
                settings=settings,
            )
        except (httpx.HTTPError, UnidentifiedImageError, OSError) as error:
            failure_counts[FAILURE_IMAGE_DOWNLOAD_FAILED] += 1
            logger.warning(
                "image_download_failed",
                category=FAILURE_IMAGE_DOWNLOAD_FAILED,
                image_url=image_url,
                error=str(error),
            )
            continue

        output_path = images_dir / f"reference_{index:02d}{image_suffix}"
        output_path.write_bytes(content)
        saved_count += 1
        time.sleep(settings.scraping_request_delay_seconds)
    return saved_count


def _download_image_with_retry(
    *,
    client: httpx.Client,
    image_url: str,
    settings: Settings,
) -> tuple[bytes, str]:
    """Download one image and verify it opens successfully with PIL."""
    retrying = Retrying(
        stop=stop_after_attempt(settings.scraping_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.HTTPError, UnidentifiedImageError, OSError)),
        reraise=True,
    )
    for attempt in retrying:
        with attempt:
            response = client.get(
                image_url,
                headers={
                    "user-agent": settings.scraping_user_agent,
                    "accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
            response.raise_for_status()
            content = response.content
            with Image.open(BytesIO(content)) as image:
                image.verify()
                image_format = (image.format or "JPEG").lower()
            suffix = ".jpg" if image_format in {"jpeg", "jpg"} else f".{image_format}"
            return content, suffix
    raise ProductScrapeError(f"Unable to download image: {image_url}")


def _write_product_meta(
    *,
    path: Path,
    parsed: ParsedProduct,
    category_hint: str | None,
) -> None:
    """Persist the top-level product metadata artifact."""
    payload = {
        "product_id": parsed.product_id,
        "title": parsed.title,
        "category": category_hint or parsed.category,
        "marketplace": parsed.marketplace,
        "source_url": parsed.source_url,
        "rating": parsed.rating,
        "visible_review_count": parsed.visible_review_count,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_description(*, path: Path, parsed: ParsedProduct) -> None:
    """Persist product description and spec bullets."""
    payload = {
        "product_id": parsed.product_id,
        "title": parsed.title,
        "category": parsed.category,
        "description_text": parsed.description,
        "bullet_text": parsed.bullet_text,
        "prompt_ready_source": "\n".join(
            part
            for part in [
                parsed.title,
                parsed.description,
                *parsed.bullet_text,
            ]
            if part
        ),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_reviews(*, path: Path, reviews: list[ReviewRecord]) -> None:
    """Persist normalized reviews as JSON Lines."""
    payload = "\n".join(review.model_dump_json() for review in reviews)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _write_raw_fetches(
    *,
    raw_html_dir: Path,
    page_html: str,
    pdp_payload: dict[str, Any],
) -> None:
    """Persist raw fetched page and API payloads for reproducibility."""
    (raw_html_dir / "product_page.html").write_text(page_html, encoding="utf-8")
    (raw_html_dir / "pdp_client_v1.json").write_text(
        json.dumps(pdp_payload, indent=2),
        encoding="utf-8",
    )


def _compute_artifact_completeness(product_dir: Path) -> ArtifactCompleteness:
    """Compute completeness flags from the on-disk artifact set."""
    paths = required_artifact_paths(product_dir)
    images_dir = paths["images_dir"]
    raw_html_dir = paths["raw_html_dir"]
    return ArtifactCompleteness(
        product_meta=paths["product_meta"].exists(),
        description=paths["description"].exists(),
        reviews=paths["reviews"].exists(),
        images=images_dir.exists() and any(images_dir.iterdir()),
        raw_html=raw_html_dir.exists() and any(raw_html_dir.iterdir()),
        scrape_report=paths["scrape_report"].exists(),
    )
