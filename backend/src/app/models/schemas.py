"""Pydantic schemas used across the pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ProductSeed(BaseModel):
    """Candidate product discovered before final selection."""

    marketplace: str
    category: str
    product_url: HttpUrl
    title_hint: str
    popularity_hint: str | None = None
    rationale: str | None = None


class DiscoveryQuerySeed(BaseModel):
    """One configured product search seed."""

    query: str
    category_guess: str
    marketplaces: list[str] = Field(default_factory=list)


class DiscoveryConfig(BaseModel):
    """Discovery configuration loaded from YAML."""

    version: int = 1
    marketplaces: list[str] = Field(default_factory=lambda: ["bestbuy"])
    queries: list[DiscoveryQuerySeed]


class DiscoveryCandidate(BaseModel):
    """Candidate product discovered from a marketplace search page."""

    title: str
    canonical_url: str
    marketplace: str
    query: str
    category_guess: str
    price: float | None = None
    rating: float | None = None
    visible_review_count: int | None = None
    thumbnail_url: str | None = None
    ranking_score: float = 0.0
    is_product_page: bool = True
    raw_html_path: str | None = None
    matched_queries: list[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class DiscoveryManifest(BaseModel):
    """Summary metadata for a discovery run."""

    stage: str = "discover-products"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    config_path: str
    output_dir: str
    candidate_queries_path: str
    candidates_path: str
    raw_html_dir: str
    total_queries: int
    total_candidates_raw: int
    total_candidates_saved: int
    failure_counts: dict[str, int]
    marketplaces: list[str]
    reused_existing: bool = False
    notes: list[str] = Field(default_factory=list)


class ProductRecord(BaseModel):
    """Durable product artifact used across the workflow."""

    product_id: str
    title: str
    category: str
    marketplace: str
    source_url: HttpUrl
    description: str
    selected: bool = True
    popularity_level: Literal["low", "medium", "high"]
    rationale: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewRecord(BaseModel):
    """One public customer review."""

    review_id: str
    product_id: str
    author: str | None = None
    rating: float | None = None
    title: str | None = None
    body: str
    posted_at: datetime | None = None
    helpful_votes: int | None = None
    verified: bool | None = None
    source_url: HttpUrl


class ArtifactCompleteness(BaseModel):
    """Per-product raw artifact completeness flags."""

    product_meta: bool = False
    description: bool = False
    reviews: bool = False
    images: bool = False
    raw_html: bool = False
    scrape_report: bool = False


class RawManifestEntry(BaseModel):
    """Manifest entry for one scraped product."""

    product_slug: str
    product_id: str
    source_url: HttpUrl
    category: str
    scrape_timestamp: datetime = Field(default_factory=datetime.utcnow)
    artifact_completeness: ArtifactCompleteness
    pages_fetched: int = 0
    review_count: int = 0
    image_count: int = 0
    status: Literal["completed", "partial_success", "failed"]
    reused_existing: bool = False
    notes: list[str] = Field(default_factory=list)


class RawManifest(BaseModel):
    """Top-level manifest for all durable raw scrape artifacts."""

    stage: str = "scrape-all"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    input_path: str
    output_dir: str
    product_count: int
    reused_existing: bool = False
    entries: list[RawManifestEntry] = Field(default_factory=list)


class ReviewCleaningStats(BaseModel):
    """Review cleaning counters preserved for reporting."""

    raw_review_count: int = 0
    cleaned_review_count: int = 0
    duplicates_removed: int = 0
    short_reviews_removed: int = 0
    low_information_removed: int = 0


class ImageManifestEntry(BaseModel):
    """One reference image tracked in the processed artifact layer."""

    filename: str
    local_path: str
    source: str = "reference"
    valid: bool = True


class ProcessedProductRecord(BaseModel):
    """Cleaned product artifact ready for downstream reuse."""

    product_slug: str
    product_id: str
    title: str
    category: str
    selected_category: str
    marketplace: str
    source_url: HttpUrl
    description_char_count: int
    spec_bullets: list[str] = Field(default_factory=list)
    visible_review_count: int | None = None
    cleaned_review_count: int = 0
    valid_image_count: int = 0
    stats_path: str
    image_manifest_path: str
    reviews_path: str
    description_path: str


class ProcessedManifestEntry(BaseModel):
    """Global processed-manifest entry for one product."""

    product_slug: str
    product_id: str
    title: str
    category: str
    source_url: HttpUrl
    processed_dir: str
    cleaned_review_count: int
    valid_image_count: int
    description_char_count: int
    passes_q1: bool = False
    issues: list[str] = Field(default_factory=list)


class ProcessedManifest(BaseModel):
    """Top-level processed corpus manifest."""

    stage: str = "build-corpus"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    raw_manifest_path: str
    selected_products_path: str
    output_dir: str
    product_count: int
    min_review_count_threshold: int
    entries: list[ProcessedManifestEntry] = Field(default_factory=list)


class Q1ValidationResult(BaseModel):
    """Machine-readable Q1 verification result."""

    stage: str = "q1"
    passed: bool
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    selected_products_count: int
    distinct_categories_count: int
    min_review_count_threshold: int
    per_product_review_counts: dict[str, int] = Field(default_factory=dict)
    per_product_image_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ScrapeReport(BaseModel):
    """Detailed report for one product scrape run."""

    product_slug: str
    product_id: str
    source_url: HttpUrl
    category: str
    marketplace: str
    title: str
    status: Literal["completed", "partial_success", "failed"]
    reused_existing: bool = False
    scrape_timestamp: datetime = Field(default_factory=datetime.utcnow)
    pages_fetched: int = 0
    visible_review_count: int | None = None
    collected_review_count: int = 0
    image_count: int = 0
    failure_counts: dict[str, int] = Field(default_factory=dict)
    artifact_completeness: ArtifactCompleteness
    notes: list[str] = Field(default_factory=list)


class ImageAsset(BaseModel):
    """Image file tracked in the repository."""

    asset_id: str
    product_id: str
    source: Literal["reference", "generated", "comparison"]
    local_path: str
    provider: str | None = None
    prompt_version_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VisualProfile(BaseModel):
    """Structured visual target extracted from text evidence."""

    product_id: str
    summary: str
    visual_attributes: list[str]
    materials: list[str]
    colors: list[str]
    packaging_cues: list[str]
    evidence_review_ids: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)


class PromptVersion(BaseModel):
    """Prompt revision used for an image generation attempt."""

    prompt_version_id: str
    product_id: str
    provider: str
    strategy: str
    prompt_text: str
    negative_prompt: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationRecord(BaseModel):
    """One image generation attempt."""

    generation_id: str
    product_id: str
    provider: str
    model_name: str
    prompt_version_id: str
    output_paths: list[str]
    status: Literal["pending", "completed", "failed"]
    metadata: dict[str, str | int | float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationRecord(BaseModel):
    """Comparison and evaluation result for generated outputs."""

    evaluation_id: str
    product_id: str
    compared_asset_ids: list[str]
    rubric_scores: dict[str, float]
    summary: str
    differences: list[str]
    strengths: list[str]
    weaknesses: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowTrace(BaseModel):
    """Trace log for the agentic workflow."""

    trace_id: str
    stage: str
    status: Literal["pending", "running", "completed", "failed"]
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
