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


class ReviewChunk(BaseModel):
    """Primary text-analysis chunk derived from one review or review split."""

    chunk_id: str
    product_slug: str
    product_id: str
    source_review_id: str
    chunk_index: int = 0
    text: str
    token_estimate: int
    source: Literal["review", "review_split"] = "review"


class RetrievedEvidence(BaseModel):
    """Retrieved evidence snippet for one aspect query."""

    aspect_key: str
    query: str
    chunk_id: str
    source_review_id: str
    score: float
    snippet: str


class VisualAttributeEvidence(BaseModel):
    """One visual attribute plus supporting evidence."""

    attribute: str
    rationale: str
    evidence_snippets: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_review_ids: list[str] = Field(default_factory=list)


class VisualMismatchEvidence(BaseModel):
    """Expectation-versus-reality mismatch grounded in review evidence."""

    mismatch: str
    evidence_snippets: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_review_ids: list[str] = Field(default_factory=list)


class VisualProfile(BaseModel):
    """Structured visual profile optimized for downstream image generation."""

    product_name: str
    category: str
    high_confidence_visual_attributes: list[VisualAttributeEvidence] = Field(default_factory=list)
    low_confidence_or_conflicting_attributes: list[VisualAttributeEvidence] = Field(
        default_factory=list
    )
    common_mismatches_between_expectation_and_reality: list[VisualMismatchEvidence] = Field(
        default_factory=list
    )
    prompt_ready_description: str
    negative_constraints: list[str] = Field(default_factory=list)


class AspectEvidenceResult(BaseModel):
    """LLM-extracted aspect-specific evidence candidates."""

    aspect_key: str
    supported_attributes: list[VisualAttributeEvidence] = Field(default_factory=list)
    conflicting_or_uncertain_attributes: list[VisualAttributeEvidence] = Field(default_factory=list)
    expectation_reality_mismatches: list[VisualMismatchEvidence] = Field(default_factory=list)


class ConflictResolutionResult(BaseModel):
    """Cross-aspect conflict resolution result before final synthesis."""

    resolved_high_confidence_attributes: list[VisualAttributeEvidence] = Field(default_factory=list)
    low_confidence_or_conflicting_attributes: list[VisualAttributeEvidence] = Field(
        default_factory=list
    )
    common_mismatches_between_expectation_and_reality: list[VisualMismatchEvidence] = Field(
        default_factory=list
    )
    negative_constraints: list[str] = Field(default_factory=list)
    resolution_notes: list[str] = Field(default_factory=list)


class LLMTraceStep(BaseModel):
    """One prompt/response step in the Q2 analysis chain."""

    step_name: str
    mode: Literal["baseline_description_only", "review_informed_rag"]
    prompt_path: str
    system_prompt: str
    user_prompt: str
    raw_response_text: str
    parsed_output: dict[str, object]
    attempt_count: int = 1


class PromptVersion(BaseModel):
    """Prompt revision used for an image generation attempt."""

    prompt_version_id: str
    product_id: str
    provider: str
    model_name: str
    strategy: Literal["pilot", "final"]
    prompt_source_mode: Literal["baseline_description_only", "review_informed_rag"]
    prompt_text: str
    negative_prompt: str | None = None
    negative_constraints: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedImageFile(BaseModel):
    """One generated image plus durable file metadata."""

    filename: str
    local_path: str
    sha256: str
    width: int
    height: int
    byte_size: int
    content_type: str
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class GenerationRecord(BaseModel):
    """One image generation attempt."""

    generation_id: str
    product_id: str
    provider: str
    model_name: str
    stage: Literal["pilot", "final"]
    prompt_version_id: str
    prompt_source_mode: Literal["baseline_description_only", "review_informed_rag"]
    output_paths: list[str]
    images: list[GeneratedImageFile] = Field(default_factory=list)
    status: Literal["pending", "completed", "failed"]
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationManifest(BaseModel):
    """Top-level manifest for one product/model generation run."""

    stage: str = "generate-images"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    product_slug: str
    product_id: str
    product_name: str
    provider: str
    model_name: str
    output_dir: str
    prompt_versions_path: str
    pilot_generation: GenerationRecord
    final_generation: GenerationRecord
    status: Literal["completed", "partial_success", "failed"]
    reused_existing: bool = False
    notes: list[str] = Field(default_factory=list)


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


class AgentExecutionInput(BaseModel):
    """Shared execution input used by workflow agents."""

    product_slug: str
    reuse_existing: bool = True
    refresh: bool = False


class DataCurationAgentInput(AgentExecutionInput):
    """Typed input contract for the data-curation agent."""

    selected_products_path: str
    raw_root: str
    processed_root: str


class DataCurationAgentOutput(BaseModel):
    """Typed output contract for the data-curation agent."""

    product_slug: str
    selected_category: str
    raw_product_dir: str
    processed_product_dir: str
    q1_validation_passed: bool
    review_count: int
    image_count: int
    artifact_links: dict[str, str] = Field(default_factory=dict)
    reused_existing: bool = True


class RetrievalAgentInput(AgentExecutionInput):
    """Typed input contract for the retrieval agent."""

    processed_product_dir: str
    output_dir: str


class RetrievalAgentOutput(BaseModel):
    """Typed output contract for the retrieval agent."""

    product_slug: str
    retrieval_evidence_path: str
    llm_trace_path: str
    aspect_count: int
    reused_existing: bool = True
    artifact_links: dict[str, str] = Field(default_factory=dict)


class VisualUnderstandingAgentInput(AgentExecutionInput):
    """Typed input contract for the visual-understanding agent."""

    processed_product_dir: str
    output_dir: str


class VisualUnderstandingAgentOutput(BaseModel):
    """Typed output contract for the visual-understanding agent."""

    product_slug: str
    baseline_profile_path: str
    review_profile_path: str
    prompt_ready_description: str
    negative_constraints: list[str] = Field(default_factory=list)
    reused_existing: bool = True
    artifact_links: dict[str, str] = Field(default_factory=dict)


class PromptComposerAgentInput(AgentExecutionInput):
    """Typed input contract for the prompt-composer agent."""

    visual_profile_dir: str
    generation_root: str
    providers: list[str] = Field(default_factory=list)


class PromptComposerAgentOutput(BaseModel):
    """Typed output contract for the prompt-composer agent."""

    product_slug: str
    prompt_sources: dict[str, str] = Field(default_factory=dict)
    prompt_previews: dict[str, dict[str, str]] = Field(default_factory=dict)
    reused_existing: bool = True
    artifact_links: dict[str, str] = Field(default_factory=dict)


class ImageGenerationAgentInput(AgentExecutionInput):
    """Typed input contract for the image-generation agent."""

    providers: list[str] = Field(default_factory=list)
    count: int = 4


class ImageGenerationAgentOutput(BaseModel):
    """Typed output contract for the image-generation agent."""

    product_slug: str
    generated_models: list[str] = Field(default_factory=list)
    generation_manifest_paths: dict[str, str] = Field(default_factory=dict)
    reused_existing: bool = True
    artifact_links: dict[str, str] = Field(default_factory=dict)


class EvaluationAgentInput(AgentExecutionInput):
    """Typed input contract for the evaluation agent."""

    vision_assisted: bool = False


class EvaluationAgentOutput(BaseModel):
    """Typed output contract for the evaluation agent."""

    product_slug: str
    summary_path: str
    comparison_panels_manifest_path: str
    human_score_sheet_path: str
    vision_assisted_eval_path: str
    evaluation_status: str
    reused_existing: bool = True
    artifact_links: dict[str, str] = Field(default_factory=dict)


class WorkflowStageStatus(BaseModel):
    """Aggregate status for one workflow stage in a run."""

    stage_key: str
    label: str
    agent_name: str
    status: Literal["pending", "running", "completed", "failed"]
    completed_count: int
    total_count: int
    products: list[str] = Field(default_factory=list)
    detail: str


class WorkflowArtifactHandoff(BaseModel):
    """Artifact handoff between two workflow stages."""

    from_stage: str
    to_stage: str
    label: str
    artifact_paths: list[str] = Field(default_factory=list)
    product_slug: str | None = None


class WorkflowRunSummary(BaseModel):
    """Top-level summary for one workflow run."""

    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scope: Literal["single", "all"]
    products: list[str] = Field(default_factory=list)
    status: Literal["completed", "partial_success", "failed"]
    stages: list[WorkflowStageStatus] = Field(default_factory=list)
    traces: list[WorkflowTrace] = Field(default_factory=list)
    artifact_handoffs: list[WorkflowArtifactHandoff] = Field(default_factory=list)
