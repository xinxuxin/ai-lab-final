"""Q2 LLM analysis pipeline for structured visual-profile extraction."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar, cast

import httpx
from pydantic import BaseModel, ValidationError

from app.config.settings import Settings, get_settings
from app.llm import Q2_SYSTEM_PROMPT, OpenAITextAnalysisClient, load_prompt_template
from app.models.schemas import (
    AspectEvidenceResult,
    ConflictResolutionResult,
    LLMTraceStep,
    ProcessedProductRecord,
    RetrievedEvidence,
    ReviewChunk,
    ReviewRecord,
    VisualProfile,
)
from app.retrieval import (
    KeywordOverlapRetriever,
    LocalEmbeddingRetriever,
    RetrievalQuery,
    Retriever,
)
from app.utils.artifacts import DATA_DIR, OUTPUTS_DIR, ensure_project_dirs

VISUAL_PROFILES_DIR = OUTPUTS_DIR / "visual_profiles"
PROCESSED_DIR = DATA_DIR / "processed"

MODE_BASELINE = "baseline_description_only"
MODE_RAG = "review_informed_rag"
VALID_MODES = {MODE_BASELINE, MODE_RAG}
ModeLiteral = Literal["baseline_description_only", "review_informed_rag"]
T = TypeVar("T", bound=BaseModel)

ASPECT_QUERIES: tuple[RetrievalQuery, ...] = (
    RetrievalQuery(
        aspect_key="appearance_and_shape",
        query="appearance, silhouette, visible form factor, shape, design, look",
    ),
    RetrievalQuery(
        aspect_key="color_and_finish",
        query="color, finish, gloss, matte, black, white, metallic, wood tone",
    ),
    RetrievalQuery(
        aspect_key="material_and_texture",
        query="material, texture, plastic, metal, glass, fabric, leather, wood",
    ),
    RetrievalQuery(
        aspect_key="size_and_scale",
        query="size, scale, dimensions, compact, large, bulky, lightweight",
    ),
    RetrievalQuery(
        aspect_key="expectation_vs_reality",
        query="expected vs actual, looks different, misleading, mismatch, reality",
    ),
)


class VisualProfileError(RuntimeError):
    """Raised when the visual-profile pipeline cannot complete."""


@dataclass(slots=True)
class ExtractVisualProfileResult:
    """Return value for one visual-profile extraction run."""

    product_slug: str
    mode: str
    profile: VisualProfile
    profile_path: Path
    retrieval_evidence_path: Path
    llm_trace_path: Path
    trace_steps: list[LLMTraceStep]


def extract_visual_profile(
    *,
    product_slug: str,
    mode: str,
    processed_root: Path | None = None,
    outputs_root: Path | None = None,
    llm_client: OpenAITextAnalysisClient | None = None,
    settings: Settings | None = None,
) -> ExtractVisualProfileResult:
    """Run the full Q2 analysis chain for one product and one mode."""
    if mode not in VALID_MODES:
        available = ", ".join(sorted(VALID_MODES))
        raise VisualProfileError(f"Unknown mode '{mode}'. Available: {available}")
    typed_mode = cast(ModeLiteral, mode)

    settings = settings or get_settings()
    ensure_project_dirs()
    resolved_processed_root = processed_root or PROCESSED_DIR
    resolved_outputs_root = outputs_root or VISUAL_PROFILES_DIR
    product_dir = resolved_processed_root / product_slug
    if not product_dir.exists():
        raise VisualProfileError(f"Processed product directory is missing: {product_dir}")

    product = ProcessedProductRecord.model_validate_json(
        (product_dir / "product.json").read_text(encoding="utf-8")
    )
    description_text = (product_dir / "description_clean.txt").read_text(encoding="utf-8").strip()
    reviews = _load_reviews(product_dir / "reviews_clean.jsonl")

    output_dir = resolved_outputs_root / product_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    owns_client = llm_client is None
    client = llm_client or OpenAITextAnalysisClient(settings=settings)
    try:
        retrieval_map = _build_retrieval_evidence(
            mode=typed_mode,
            product_slug=product_slug,
            product_id=product.product_id,
            description_text=description_text,
            reviews=reviews,
            client=client,
            settings=settings,
        )
        trace_steps: list[LLMTraceStep] = []
        aspect_results = [
            _extract_aspect_evidence(
                query=query,
                mode=typed_mode,
                product=product,
                description_text=description_text,
                retrieved_evidence=retrieval_map[query.aspect_key],
                client=client,
                settings=settings,
                trace_steps=trace_steps,
            )
            for query in ASPECT_QUERIES
        ]
        conflict_result = _resolve_conflicts(
            mode=typed_mode,
            product=product,
            aspect_results=aspect_results,
            client=client,
            settings=settings,
            trace_steps=trace_steps,
        )
        profile = _synthesize_visual_profile(
            mode=typed_mode,
            product=product,
            description_text=description_text,
            conflict_result=conflict_result,
            client=client,
            settings=settings,
            trace_steps=trace_steps,
        )
    finally:
        if owns_client:
            client.close()

    profile_path = output_dir / f"{mode}.json"
    profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

    retrieval_evidence_path = output_dir / "retrieval_evidence.json"
    _merge_json_output(
        retrieval_evidence_path,
        mode,
        {
            aspect_key: [entry.model_dump(mode="json") for entry in entries]
            for aspect_key, entries in retrieval_map.items()
        },
    )

    llm_trace_path = output_dir / "llm_trace.json"
    _merge_json_output(
        llm_trace_path,
        mode,
        [step.model_dump(mode="json") for step in trace_steps],
    )

    return ExtractVisualProfileResult(
        product_slug=product_slug,
        mode=typed_mode,
        profile=profile,
        profile_path=profile_path,
        retrieval_evidence_path=retrieval_evidence_path,
        llm_trace_path=llm_trace_path,
        trace_steps=trace_steps,
    )


def chunk_reviews(
    *,
    product_slug: str,
    product_id: str,
    reviews: list[ReviewRecord],
    max_chars: int,
) -> list[ReviewChunk]:
    """Use one review per chunk unless a review is overly long."""
    chunks: list[ReviewChunk] = []
    for review in reviews:
        review_text = "\n".join(part for part in [review.title or "", review.body] if part).strip()
        if len(review_text) <= max_chars:
            chunks.append(
                ReviewChunk(
                    chunk_id=f"{review.review_id}__0",
                    product_slug=product_slug,
                    product_id=product_id,
                    source_review_id=review.review_id,
                    chunk_index=0,
                    text=review_text,
                    token_estimate=_token_estimate(review_text),
                    source="review",
                )
            )
            continue

        for index, piece in enumerate(_split_long_review(review_text, max_chars=max_chars)):
            chunks.append(
                ReviewChunk(
                    chunk_id=f"{review.review_id}__{index}",
                    product_slug=product_slug,
                    product_id=product_id,
                    source_review_id=review.review_id,
                    chunk_index=index,
                    text=piece,
                    token_estimate=_token_estimate(piece),
                    source="review_split",
                )
            )
    return chunks


def _build_retrieval_evidence(
    *,
    mode: ModeLiteral,
    product_slug: str,
    product_id: str,
    description_text: str,
    reviews: list[ReviewRecord],
    client: OpenAITextAnalysisClient,
    settings: Settings,
) -> dict[str, list[RetrievedEvidence]]:
    """Return per-aspect evidence lists for the selected mode."""
    if mode == MODE_BASELINE:
        return {
            query.aspect_key: [
                RetrievedEvidence(
                    aspect_key=query.aspect_key,
                    query=query.query,
                    chunk_id="description_context",
                    source_review_id="description_context",
                    score=1.0,
                    snippet=description_text,
                )
            ]
            for query in ASPECT_QUERIES
        }

    chunks = chunk_reviews(
        product_slug=product_slug,
        product_id=product_id,
        reviews=reviews,
        max_chars=settings.review_chunk_max_chars,
    )
    try:
        retriever: Retriever = LocalEmbeddingRetriever(
            product_slug=product_slug,
            chunks=chunks,
            embedding_client=client,
        )
    except httpx.HTTPError:
        retriever = KeywordOverlapRetriever(chunks=chunks)
    return {
        query.aspect_key: retriever.search(query, top_k=settings.retrieval_top_k)
        for query in ASPECT_QUERIES
    }


def _extract_aspect_evidence(
    *,
    query: RetrievalQuery,
    mode: ModeLiteral,
    product: ProcessedProductRecord,
    description_text: str,
    retrieved_evidence: list[RetrievedEvidence],
    client: OpenAITextAnalysisClient,
    settings: Settings,
    trace_steps: list[LLMTraceStep],
) -> AspectEvidenceResult:
    """Run the aspect-specific evidence extraction step."""
    prompt_path, prompt_template = load_prompt_template("aspect_evidence_extraction")
    context: dict[str, object] = {
        "mode": mode,
        "aspect_key": query.aspect_key,
        "aspect_query": query.query,
        "product_name": product.title,
        "category": product.category,
        "selected_category": product.selected_category,
        "description": description_text,
        "spec_bullets": product.spec_bullets,
        "retrieved_evidence": [entry.model_dump(mode="json") for entry in retrieved_evidence],
    }
    return _run_structured_step(
        step_name=f"aspect_evidence_extraction:{query.aspect_key}",
        mode=mode,
        prompt_path=prompt_path,
        prompt_template=prompt_template,
        context=context,
        response_model=AspectEvidenceResult,
        client=client,
        settings=settings,
        trace_steps=trace_steps,
    )


def _resolve_conflicts(
    *,
    mode: ModeLiteral,
    product: ProcessedProductRecord,
    aspect_results: list[AspectEvidenceResult],
    client: OpenAITextAnalysisClient,
    settings: Settings,
    trace_steps: list[LLMTraceStep],
) -> ConflictResolutionResult:
    """Resolve cross-aspect conflicts before final synthesis."""
    prompt_path, prompt_template = load_prompt_template("conflict_resolution")
    context: dict[str, object] = {
        "mode": mode,
        "product_name": product.title,
        "category": product.category,
        "selected_category": product.selected_category,
        "aspect_results": [result.model_dump(mode="json") for result in aspect_results],
    }
    return _run_structured_step(
        step_name="conflict_resolution",
        mode=mode,
        prompt_path=prompt_path,
        prompt_template=prompt_template,
        context=context,
        response_model=ConflictResolutionResult,
        client=client,
        settings=settings,
        trace_steps=trace_steps,
    )


def _synthesize_visual_profile(
    *,
    mode: ModeLiteral,
    product: ProcessedProductRecord,
    description_text: str,
    conflict_result: ConflictResolutionResult,
    client: OpenAITextAnalysisClient,
    settings: Settings,
    trace_steps: list[LLMTraceStep],
) -> VisualProfile:
    """Synthesize the final frontend-friendly VisualProfile JSON."""
    prompt_path, prompt_template = load_prompt_template("final_visual_profile_synthesis")
    context: dict[str, object] = {
        "mode": mode,
        "product_name": product.title,
        "category": product.category,
        "selected_category": product.selected_category,
        "description": description_text,
        "spec_bullets": product.spec_bullets,
        "conflict_resolution": conflict_result.model_dump(mode="json"),
    }
    return _run_structured_step(
        step_name="final_visual_profile_synthesis",
        mode=mode,
        prompt_path=prompt_path,
        prompt_template=prompt_template,
        context=context,
        response_model=VisualProfile,
        client=client,
        settings=settings,
        trace_steps=trace_steps,
    )


def _run_structured_step(
    *,
    step_name: str,
    mode: ModeLiteral,
    prompt_path: Path,
    prompt_template: str,
    context: Mapping[str, object],
    response_model: type[T],
    client: OpenAITextAnalysisClient,
    settings: Settings,
    trace_steps: list[LLMTraceStep],
) -> T:
    """Execute one JSON-only step with parse validation retries."""
    base_prompt = (
        f"{prompt_template}\n\nContext JSON:\n"
        f"{json.dumps(context, indent=2, ensure_ascii=False)}"
    )
    raw_response_text = ""
    last_error = "no response"

    for attempt in range(1, settings.llm_max_retries + 1):
        prompt = base_prompt
        if attempt > 1:
            prompt += (
                "\n\nYour previous response did not validate. "
                f"Return only valid JSON matching the schema. Validation error: {last_error}"
            )
        completion = client.complete_json(
            system_prompt=Q2_SYSTEM_PROMPT,
            user_prompt=prompt,
            model=settings.llm_analysis_model,
        )
        raw_response_text = completion.text
        try:
            payload = json.loads(raw_response_text)
            parsed = response_model.model_validate(payload)
            trace_steps.append(
                LLMTraceStep(
                    step_name=step_name,
                    mode=mode,
                    prompt_path=str(prompt_path.resolve()),
                    system_prompt=Q2_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    raw_response_text=raw_response_text,
                    parsed_output=parsed.model_dump(mode="json"),
                    attempt_count=attempt,
                )
            )
            return parsed
        except (json.JSONDecodeError, ValidationError) as error:
            last_error = str(error)

    raise VisualProfileError(
        f"Step '{step_name}' failed to produce valid JSON after "
        f"{settings.llm_max_retries} attempts."
    )


def _load_reviews(path: Path) -> list[ReviewRecord]:
    """Load cleaned review JSONL records from processed artifacts."""
    return [
        ReviewRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _split_long_review(text: str, *, max_chars: int) -> list[str]:
    """Split an overly long review into sentence-ish chunks."""
    sentences = text.replace("\n", " ").split(". ")
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence.strip()
        if not candidate:
            continue
        combined = candidate if not current else f"{current}. {candidate}"
        if len(combined) <= max_chars:
            current = combined
            continue
        if current:
            pieces.append(current.strip())
        current = candidate
    if current:
        pieces.append(current.strip())
    return pieces or [text[:max_chars]]


def _token_estimate(text: str) -> int:
    """Approximate token count for chunking/debug output."""
    return max(1, len(text.split()))


def _merge_json_output(path: Path, mode: str, payload: object) -> None:
    """Merge one mode's output into a shared JSON artifact."""
    existing: dict[str, object] = {}
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            existing = loaded
    existing[mode] = payload
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
