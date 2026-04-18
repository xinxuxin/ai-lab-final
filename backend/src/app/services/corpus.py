"""Processed corpus building and strict Q1 validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import cast

from PIL import Image, UnidentifiedImageError

from app.config.settings import Settings, get_settings
from app.models.schemas import (
    ImageManifestEntry,
    ProcessedManifest,
    ProcessedManifestEntry,
    ProcessedProductRecord,
    Q1ValidationResult,
    RawManifest,
    ReviewCleaningStats,
    ReviewRecord,
)
from app.utils.artifacts import DATA_DIR, DOCS_DIR, ensure_project_dirs

PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
SELECTED_PRODUCTS_PATH = DATA_DIR / "selected_products.jsonl"
RAW_MANIFEST_PATH = RAW_DIR / "raw_manifest.json"
WHITESPACE_PATTERN = re.compile(r"\s+")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WORD_PATTERN = re.compile(r"[a-z0-9']+")


class CorpusBuildError(RuntimeError):
    """Raised when the processed corpus or Q1 validation fails."""


@dataclass(slots=True)
class BuildCorpusResult:
    """Return value for the processed corpus build stage."""

    manifest: ProcessedManifest
    manifest_path: Path
    q1_validation: Q1ValidationResult
    q1_summary_path: Path


def build_processed_corpus(
    *,
    raw_dir: Path | None = None,
    output_dir: Path | None = None,
    selected_products_path: Path | None = None,
    min_review_count: int | None = None,
    settings: Settings | None = None,
) -> BuildCorpusResult:
    """Build cleaned reusable corpora from raw scrape artifacts and validate Q1."""
    settings = settings or get_settings()
    ensure_project_dirs()
    resolved_raw_dir = raw_dir or RAW_DIR
    resolved_output_dir = output_dir or PROCESSED_DIR
    resolved_selected_products = selected_products_path or SELECTED_PRODUCTS_PATH
    review_threshold = min_review_count or settings.q1_min_review_count

    raw_manifest = _load_raw_manifest(resolved_raw_dir / "raw_manifest.json")
    selected_products = _load_selected_products(resolved_selected_products)
    selected_by_slug = {entry["product_slug"]: entry for entry in selected_products}

    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: list[ProcessedManifestEntry] = []
    for raw_entry in raw_manifest.entries:
        product_slug = raw_entry.product_slug
        product_dir = resolved_raw_dir / product_slug
        if not product_dir.exists():
            raise CorpusBuildError(f"Missing raw product directory: {product_dir}")
        if product_slug not in selected_by_slug:
            raise CorpusBuildError(
                f"Raw artifact {product_slug} is not present in selected_products.jsonl."
            )

        processed_entry = _process_product_dir(
            product_slug=product_slug,
            raw_product_dir=product_dir,
            processed_root=resolved_output_dir,
            selected_category=selected_by_slug[product_slug]["category"],
            min_review_chars=settings.corpus_min_review_chars,
            min_review_count=review_threshold,
        )
        manifest_entries.append(processed_entry)

    manifest = ProcessedManifest(
        raw_manifest_path=str((resolved_raw_dir / "raw_manifest.json").resolve()),
        selected_products_path=str(resolved_selected_products.resolve()),
        output_dir=str(resolved_output_dir.resolve()),
        product_count=len(manifest_entries),
        min_review_count_threshold=review_threshold,
        entries=manifest_entries,
    )
    manifest_path = resolved_output_dir / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    q1_validation = validate_q1_artifacts(
        processed_manifest=manifest,
        selected_products_path=resolved_selected_products,
        min_review_count=review_threshold,
    )
    q1_summary_path = write_q1_docs(
        processed_manifest=manifest,
        q1_validation=q1_validation,
    )

    return BuildCorpusResult(
        manifest=manifest,
        manifest_path=manifest_path,
        q1_validation=q1_validation,
        q1_summary_path=q1_summary_path,
    )


def validate_q1_from_disk(
    *,
    processed_dir: Path | None = None,
    selected_products_path: Path | None = None,
    min_review_count: int | None = None,
    settings: Settings | None = None,
) -> Q1ValidationResult:
    """Load processed artifacts from disk and validate Q1 constraints."""
    settings = settings or get_settings()
    resolved_processed_dir = processed_dir or PROCESSED_DIR
    resolved_selected_products = selected_products_path or SELECTED_PRODUCTS_PATH
    manifest_path = resolved_processed_dir / "manifest.json"
    if not manifest_path.exists():
        raise CorpusBuildError(f"Processed manifest is missing: {manifest_path}")
    manifest = ProcessedManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    return validate_q1_artifacts(
        processed_manifest=manifest,
        selected_products_path=resolved_selected_products,
        min_review_count=min_review_count or settings.q1_min_review_count,
    )


def validate_q1_artifacts(
    *,
    processed_manifest: ProcessedManifest,
    selected_products_path: Path,
    min_review_count: int,
) -> Q1ValidationResult:
    """Apply strict Q1 checks to the processed corpus layer."""
    selected_products = _load_selected_products(selected_products_path)
    issues: list[str] = []
    notes: list[str] = []

    if len(selected_products) != 3:
        issues.append(
            f"Expected exactly 3 selected products, found {len(selected_products)}."
        )

    distinct_categories = {
        entry["category"].strip().lower()
        for entry in selected_products
        if entry["category"].strip()
    }
    if len(distinct_categories) != 3:
        issues.append(
            f"Expected 3 distinct categories, found {len(distinct_categories)}: "
            f"{sorted(distinct_categories)}."
        )

    if len(processed_manifest.entries) != 3:
        issues.append(
            f"Processed manifest should contain 3 entries, found {len(processed_manifest.entries)}."
        )

    per_product_review_counts: dict[str, int] = {}
    per_product_image_counts: dict[str, int] = {}
    for entry in processed_manifest.entries:
        per_product_review_counts[entry.product_slug] = entry.cleaned_review_count
        per_product_image_counts[entry.product_slug] = entry.valid_image_count
        if entry.description_char_count <= 0:
            issues.append(f"{entry.product_slug} has an empty cleaned description.")
        if entry.cleaned_review_count < min_review_count:
            issues.append(
                f"{entry.product_slug} has {entry.cleaned_review_count} cleaned reviews, "
                f"below threshold {min_review_count}."
            )
        if entry.valid_image_count < 1:
            issues.append(f"{entry.product_slug} does not have a valid real image.")

    if not issues:
        notes.append(
            "Q1 selection satisfies category diversity, descriptions, reviews, and images."
        )

    return Q1ValidationResult(
        passed=not issues,
        selected_products_count=len(selected_products),
        distinct_categories_count=len(distinct_categories),
        min_review_count_threshold=min_review_count,
        per_product_review_counts=per_product_review_counts,
        per_product_image_counts=per_product_image_counts,
        issues=issues,
        notes=notes,
    )


def write_q1_docs(
    *,
    processed_manifest: ProcessedManifest,
    q1_validation: Q1ValidationResult,
) -> Path:
    """Write human-readable Q1 reporting support documents."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    summary_lines = [
        "# Q1 Summary",
        "",
        f"- Status: {'PASS' if q1_validation.passed else 'FAIL'}",
        f"- Checked at: {q1_validation.checked_at.isoformat()}",
        f"- Selected products: {q1_validation.selected_products_count}",
        f"- Distinct categories: {q1_validation.distinct_categories_count}",
        f"- Minimum review threshold: {q1_validation.min_review_count_threshold}",
        "",
        "## Per Product",
        "",
    ]
    for entry in processed_manifest.entries:
        summary_lines.extend(
            [
                f"### {entry.title}",
                f"- Product slug: `{entry.product_slug}`",
                f"- Category: `{entry.category}`",
                f"- Cleaned review count: `{entry.cleaned_review_count}`",
                f"- Valid image count: `{entry.valid_image_count}`",
                f"- Description char count: `{entry.description_char_count}`",
                f"- Passes Q1 per-product checks: `{entry.passes_q1}`",
                "",
            ]
        )
        if entry.issues:
            summary_lines.append("Issues:")
            for issue in entry.issues:
                summary_lines.append(f"- {issue}")
            summary_lines.append("")

    summary_lines.append("## Validation Notes")
    summary_lines.append("")
    if q1_validation.issues:
        for issue in q1_validation.issues:
            summary_lines.append(f"- {issue}")
    else:
        summary_lines.append("- All strict Q1 checks passed.")
    for note in q1_validation.notes:
        summary_lines.append(f"- {note}")

    summary_path = DOCS_DIR / "q1_summary.md"
    summary_path.write_text("\n".join(summary_lines).rstrip() + "\n", encoding="utf-8")

    rationale_template = "\n".join(
        [
            "# Q1 Selection Rationale Template",
            "",
            "Use this template to justify the final three products in the report.",
            "",
            "## Product 1",
            "- Product name:",
            "- Marketplace URL:",
            "- Category:",
            "- Popularity level:",
            "- Why this category was chosen:",
            "- Why this specific product was chosen:",
            "- What review evidence makes it useful for downstream image generation:",
            "",
            "## Product 2",
            "- Product name:",
            "- Marketplace URL:",
            "- Category:",
            "- Popularity level:",
            "- Why this category was chosen:",
            "- Why this specific product was chosen:",
            "- What review evidence makes it useful for downstream image generation:",
            "",
            "## Product 3",
            "- Product name:",
            "- Marketplace URL:",
            "- Category:",
            "- Popularity level:",
            "- Why this category was chosen:",
            "- Why this specific product was chosen:",
            "- What review evidence makes it useful for downstream image generation:",
            "",
            "## Cross-Product Rationale",
            "- How the three products satisfy category diversity:",
            "- How the three products compare in popularity/review volume:",
            "- Why the set is suitable for Q2-Q4:",
            "",
        ]
    )
    (DOCS_DIR / "q1_selection_rationale_template.md").write_text(
        rationale_template,
        encoding="utf-8",
    )
    return summary_path


def _process_product_dir(
    *,
    product_slug: str,
    raw_product_dir: Path,
    processed_root: Path,
    selected_category: str,
    min_review_chars: int,
    min_review_count: int,
) -> ProcessedManifestEntry:
    """Process one raw product directory into durable cleaned artifacts."""
    processed_dir = processed_root / product_slug
    processed_dir.mkdir(parents=True, exist_ok=True)

    product_meta = json.loads((raw_product_dir / "product_meta.json").read_text(encoding="utf-8"))
    description_payload = json.loads(
        (raw_product_dir / "description.json").read_text(encoding="utf-8")
    )
    raw_reviews = _load_reviews(raw_product_dir / "reviews.jsonl")
    cleaned_reviews, cleaning_stats = clean_reviews(
        raw_reviews=raw_reviews,
        min_review_chars=min_review_chars,
    )
    cleaned_description, cleaned_bullets = clean_description_payload(description_payload)
    image_entries = build_image_manifest(raw_product_dir / "images")

    description_path = processed_dir / "description_clean.txt"
    reviews_path = processed_dir / "reviews_clean.jsonl"
    stats_path = processed_dir / "review_stats.json"
    image_manifest_path = processed_dir / "image_manifest.json"
    product_path = processed_dir / "product.json"

    description_path.write_text(cleaned_description, encoding="utf-8")
    _write_reviews(reviews_path, cleaned_reviews)

    stats_payload = {
        **cleaning_stats.model_dump(mode="json"),
        "visible_review_count": product_meta.get("visible_review_count"),
        "rating": product_meta.get("rating"),
    }
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")
    image_manifest_path.write_text(
        json.dumps([entry.model_dump(mode="json") for entry in image_entries], indent=2),
        encoding="utf-8",
    )

    product_record = ProcessedProductRecord(
        product_slug=product_slug,
        product_id=str(product_meta["product_id"]),
        title=normalize_text(str(product_meta["title"])),
        category=normalize_text(
            str(description_payload.get("category") or product_meta["category"])
        ),
        selected_category=normalize_text(selected_category),
        marketplace=normalize_text(str(product_meta["marketplace"])),
        source_url=product_meta["source_url"],
        description_char_count=len(cleaned_description),
        spec_bullets=cleaned_bullets,
        visible_review_count=product_meta.get("visible_review_count"),
        cleaned_review_count=len(cleaned_reviews),
        valid_image_count=sum(1 for entry in image_entries if entry.valid),
        stats_path=str(stats_path.resolve()),
        image_manifest_path=str(image_manifest_path.resolve()),
        reviews_path=str(reviews_path.resolve()),
        description_path=str(description_path.resolve()),
    )
    product_path.write_text(product_record.model_dump_json(indent=2), encoding="utf-8")

    issues: list[str] = []
    if product_record.description_char_count <= 0:
        issues.append("cleaned description is empty")
    if product_record.cleaned_review_count < min_review_count:
        issues.append(
            "cleaned review count "
            f"{product_record.cleaned_review_count} is below threshold {min_review_count}"
        )
    if product_record.valid_image_count < 1:
        issues.append("no valid real images found")

    return ProcessedManifestEntry(
        product_slug=product_slug,
        product_id=product_record.product_id,
        title=product_record.title,
        category=product_record.selected_category,
        source_url=product_record.source_url,
        processed_dir=str(processed_dir.resolve()),
        cleaned_review_count=product_record.cleaned_review_count,
        valid_image_count=product_record.valid_image_count,
        description_char_count=product_record.description_char_count,
        passes_q1=not issues,
        issues=issues,
    )


def clean_description_payload(payload: dict[str, object]) -> tuple[str, list[str]]:
    """Normalize description text and preserve cleaned spec bullets separately."""
    description_text = normalize_text(str(payload.get("description_text", "")))
    bullet_entries = cast(list[object], payload.get("bullet_text", []))
    bullet_text = [
        normalize_text(str(entry))
        for entry in bullet_entries
        if normalize_text(str(entry))
    ]
    return description_text.strip(), bullet_text


def clean_reviews(
    *,
    raw_reviews: list[ReviewRecord],
    min_review_chars: int,
) -> tuple[list[ReviewRecord], ReviewCleaningStats]:
    """Normalize, deduplicate, and filter low-information reviews."""
    stats = ReviewCleaningStats(raw_review_count=len(raw_reviews))
    cleaned_reviews: list[ReviewRecord] = []
    seen_keys: set[str] = set()

    for review in raw_reviews:
        cleaned_title = normalize_text(review.title or "") or None
        cleaned_body = normalize_text(review.body)
        combined_text = " ".join(
            part for part in [cleaned_title or "", cleaned_body] if part
        ).strip()

        if len(combined_text) < min_review_chars:
            stats.short_reviews_removed += 1
            continue

        if is_low_information_review(combined_text):
            stats.low_information_removed += 1
            continue

        dedupe_key = f"{review.review_id}:{combined_text.lower()}"
        if dedupe_key in seen_keys:
            stats.duplicates_removed += 1
            continue
        seen_keys.add(dedupe_key)

        cleaned_reviews.append(
            review.model_copy(
                update={
                    "title": cleaned_title,
                    "body": cleaned_body,
                }
            )
        )

    stats.cleaned_review_count = len(cleaned_reviews)
    return cleaned_reviews, stats


def build_image_manifest(images_dir: Path) -> list[ImageManifestEntry]:
    """Build a processed image manifest from saved real product images."""
    image_entries: list[ImageManifestEntry] = []
    for image_path in sorted(images_dir.iterdir()):
        if not image_path.is_file():
            continue
        valid = _validate_image(image_path)
        image_entries.append(
            ImageManifestEntry(
                filename=image_path.name,
                local_path=str(image_path.resolve()),
                valid=valid,
            )
        )
    return image_entries


def normalize_text(value: str) -> str:
    """Decode HTML entities, remove tags, and normalize whitespace."""
    text = unescape(value)
    text = HTML_TAG_PATTERN.sub(" ", text)
    text = text.replace("•", " ")
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    return text


def is_low_information_review(text: str) -> bool:
    """Heuristically identify low-information reviews."""
    tokens = WORD_PATTERN.findall(text.lower())
    unique_tokens = {token for token in tokens if len(token) > 1}
    return len(tokens) < 4 or len(unique_tokens) < 3


def _validate_image(path: Path) -> bool:
    """Confirm that a saved image can still be opened locally."""
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, UnidentifiedImageError):
        return False


def _load_raw_manifest(path: Path) -> RawManifest:
    """Load the raw scrape manifest from disk."""
    if not path.exists():
        raise CorpusBuildError(f"Missing raw manifest: {path}")
    return RawManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _load_selected_products(path: Path) -> list[dict[str, str]]:
    """Load selected products together with a derived product slug."""
    if not path.exists():
        raise CorpusBuildError(f"Missing selected products file: {path}")
    entries: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        payload["product_slug"] = _selected_product_slug(str(payload["product_url"]))
        entries.append(payload)
    return entries


def _load_reviews(path: Path) -> list[ReviewRecord]:
    """Load review JSONL records from disk."""
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [ReviewRecord.model_validate_json(line) for line in lines]


def _write_reviews(path: Path, reviews: list[ReviewRecord]) -> None:
    """Persist cleaned reviews as JSON Lines."""
    payload = "\n".join(review.model_dump_json() for review in reviews)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _selected_product_slug(product_url: str) -> str:
    """Derive the on-disk product slug from a selected product URL."""
    normalized_url = product_url.rstrip("/")
    slug = normalized_url.split("/p/")[-1].split("/-/A-")[0]
    product_id = normalized_url.split("/A-")[-1]
    if slug.endswith(f"-{product_id}"):
        return slug
    return f"{slug}-{product_id}"
