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
    source_url: HttpUrl


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
