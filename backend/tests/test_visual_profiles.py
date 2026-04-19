"""Q2 visual-profile pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import HttpUrl, TypeAdapter, ValidationError

from app.config.settings import Settings
from app.llm import JSONCompletionResult
from app.llm.prompts import PROMPT_PATHS, load_prompt_template
from app.models.schemas import ReviewChunk, ReviewRecord, VisualProfile
from app.retrieval import LocalEmbeddingRetriever, RetrievalQuery
from app.services.visual_profiles import extract_visual_profile

HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def test_visual_profile_schema_validation() -> None:
    """VisualProfile should reject outputs missing required keys."""
    with pytest.raises(ValidationError):
        VisualProfile.model_validate(
            {
                "product_name": "Example Product",
                "category": "Example Category",
                "high_confidence_visual_attributes": [],
                "low_confidence_or_conflicting_attributes": [],
                "common_mismatches_between_expectation_and_reality": [],
                "negative_constraints": [],
            }
        )


def test_prompt_templates_load() -> None:
    """All Q2 prompt templates should exist and be loadable."""
    for name, expected_path in PROMPT_PATHS.items():
        path, content = load_prompt_template(name)
        assert path == expected_path
        assert content.strip()


def test_local_retriever_ranks_and_caches(tmp_path: Path) -> None:
    """Local retriever should rank by cosine similarity and write a cache file."""

    class FakeEmbedder:
        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            vectors = {
                "black matte finish and soft texture": [1.0, 0.0],
                "large bulky footprint and wide base": [0.0, 1.0],
                "matte black finish": [1.0, 0.0],
            }
            return [vectors[text] for text in texts]

    chunks = [
        ReviewChunk(
            chunk_id="a",
            product_slug="sample",
            product_id="1",
            source_review_id="review-a",
            text="black matte finish and soft texture",
            token_estimate=6,
        ),
        ReviewChunk(
            chunk_id="b",
            product_slug="sample",
            product_id="1",
            source_review_id="review-b",
            text="large bulky footprint and wide base",
            token_estimate=6,
        ),
    ]
    cache_path = tmp_path / "embedding_cache.json"
    retriever = LocalEmbeddingRetriever(
        product_slug="sample",
        chunks=chunks,
        embedding_client=FakeEmbedder(),
        cache_path=cache_path,
    )

    result = retriever.search(
        RetrievalQuery(aspect_key="color_and_finish", query="matte black finish"),
        top_k=1,
    )

    assert result[0].chunk_id == "a"
    assert cache_path.exists()


def test_extract_visual_profile_with_mocked_llm(tmp_path: Path) -> None:
    """Full Q2 pipeline should run end-to-end with a mocked LLM client."""
    product_slug = "sample-headphones-1"
    processed_dir = tmp_path / "processed" / product_slug
    processed_dir.mkdir(parents=True, exist_ok=True)
    _write_processed_fixture(processed_dir=processed_dir, product_slug=product_slug)

    class FakeLLMClient:
        def __init__(self) -> None:
            self._completion_index = 0

        def complete_json(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            model: str | None = None,
        ) -> JSONCompletionResult:
            del system_prompt, model
            self._completion_index += 1
            if self._completion_index == 1:
                return JSONCompletionResult(text="{bad json", usage={})
            if "aspect_evidence_extraction:appearance_and_shape" in user_prompt:
                raise AssertionError("step name should not be embedded in prompt")

            payloads = [
                {
                    "aspect_key": "appearance_and_shape",
                    "supported_attributes": [
                        {
                            "attribute": "over-ear silhouette",
                            "rationale": "Multiple reviews describe an over-ear form factor.",
                            "evidence_snippets": ["comfortable over-ear fit"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        }
                    ],
                    "conflicting_or_uncertain_attributes": [],
                    "expectation_reality_mismatches": [],
                },
                {
                    "aspect_key": "color_and_finish",
                    "supported_attributes": [
                        {
                            "attribute": "matte black finish",
                            "rationale": "Reviews and listing align on a matte black look.",
                            "evidence_snippets": ["matte black earcups"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        }
                    ],
                    "conflicting_or_uncertain_attributes": [],
                    "expectation_reality_mismatches": [],
                },
                {
                    "aspect_key": "material_and_texture",
                    "supported_attributes": [
                        {
                            "attribute": "soft leatherette ear cushions",
                            "rationale": "Material is named in specs and confirmed in reviews.",
                            "evidence_snippets": ["soft leatherette pads"],
                            "source_chunk_ids": ["review-2__0"],
                            "source_review_ids": ["review-2"],
                        }
                    ],
                    "conflicting_or_uncertain_attributes": [],
                    "expectation_reality_mismatches": [],
                },
                {
                    "aspect_key": "size_and_scale",
                    "supported_attributes": [
                        {
                            "attribute": "full-size headphones",
                            "rationale": "Evidence describes a large over-ear fit.",
                            "evidence_snippets": ["covers the whole ear"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        }
                    ],
                    "conflicting_or_uncertain_attributes": [],
                    "expectation_reality_mismatches": [],
                },
                {
                    "aspect_key": "expectation_vs_reality",
                    "supported_attributes": [],
                    "conflicting_or_uncertain_attributes": [],
                    "expectation_reality_mismatches": [
                        {
                            "mismatch": "noise cancellation weaker than expected in windy settings",
                            "evidence_snippets": ["ANC is weaker outdoors in wind"],
                            "source_chunk_ids": ["review-2__0"],
                            "source_review_ids": ["review-2"],
                        }
                    ],
                },
                {
                    "resolved_high_confidence_attributes": [
                        {
                            "attribute": "over-ear silhouette",
                            "rationale": "Repeatedly supported across evidence.",
                            "evidence_snippets": ["comfortable over-ear fit"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        },
                        {
                            "attribute": "matte black finish",
                            "rationale": "Listing and reviews align.",
                            "evidence_snippets": ["matte black earcups"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        },
                    ],
                    "low_confidence_or_conflicting_attributes": [],
                    "common_mismatches_between_expectation_and_reality": [
                        {
                            "mismatch": "noise cancellation weaker than expected in windy settings",
                            "evidence_snippets": ["ANC is weaker outdoors in wind"],
                            "source_chunk_ids": ["review-2__0"],
                            "source_review_ids": ["review-2"],
                        }
                    ],
                    "negative_constraints": ["avoid glossy finish", "avoid bright accent colors"],
                    "resolution_notes": ["Material details are moderately supported."],
                },
                {
                    "product_name": "Sample Headphones",
                    "category": "Wireless Headphones",
                    "high_confidence_visual_attributes": [
                        {
                            "attribute": "over-ear silhouette",
                            "rationale": "Repeated support in description and reviews.",
                            "evidence_snippets": ["comfortable over-ear fit"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        },
                        {
                            "attribute": "matte black finish",
                            "rationale": "Consistent listing and review evidence.",
                            "evidence_snippets": ["matte black earcups"],
                            "source_chunk_ids": ["review-1__0"],
                            "source_review_ids": ["review-1"],
                        },
                    ],
                    "low_confidence_or_conflicting_attributes": [],
                    "common_mismatches_between_expectation_and_reality": [
                        {
                            "mismatch": "noise cancellation weaker than expected in windy settings",
                            "evidence_snippets": ["ANC is weaker outdoors in wind"],
                            "source_chunk_ids": ["review-2__0"],
                            "source_review_ids": ["review-2"],
                        }
                    ],
                    "prompt_ready_description": (
                        "Matte black over-ear wireless headphones with a full-size "
                        "silhouette and soft padded ear cushions."
                    ),
                    "negative_constraints": ["avoid glossy finish", "avoid bright accent colors"],
                },
            ]
            payload = payloads[self._completion_index - 2]
            return JSONCompletionResult(text=json.dumps(payload), usage={})

        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in texts]

    result = extract_visual_profile(
        product_slug=product_slug,
        mode="review_informed_rag",
        processed_root=tmp_path / "processed",
        outputs_root=tmp_path / "outputs",
        llm_client=FakeLLMClient(),  # type: ignore[arg-type]
        settings=Settings(LLM_MAX_RETRIES=2, RETRIEVAL_TOP_K=2, REVIEW_CHUNK_MAX_CHARS=1200),
    )

    assert result.profile.product_name == "Sample Headphones"
    assert result.profile.high_confidence_visual_attributes
    assert result.profile_path.exists()
    retrieval_payload = json.loads(result.retrieval_evidence_path.read_text(encoding="utf-8"))
    assert "review_informed_rag" in retrieval_payload
    trace_payload = json.loads(result.llm_trace_path.read_text(encoding="utf-8"))
    assert len(trace_payload["review_informed_rag"]) == 7


def _write_processed_fixture(*, processed_dir: Path, product_slug: str) -> None:
    """Write a minimal processed product fixture."""
    (processed_dir / "product.json").write_text(
        json.dumps(
            {
                "product_slug": product_slug,
                "product_id": "1",
                "title": "Sample Headphones",
                "category": "Wireless Headphones",
                "selected_category": "audio",
                "marketplace": "target",
                "source_url": "https://www.target.com/p/sample-headphones/-/A-1",
                "description_char_count": 120,
                "spec_bullets": [
                    "Color: Black",
                    "Ear Cushion Material: Leatherette",
                    "Wireless Technology: Bluetooth",
                ],
                "visible_review_count": 2,
                "cleaned_review_count": 2,
                "valid_image_count": 2,
                "stats_path": str(processed_dir / "review_stats.json"),
                "image_manifest_path": str(processed_dir / "image_manifest.json"),
                "reviews_path": str(processed_dir / "reviews_clean.jsonl"),
                "description_path": str(processed_dir / "description_clean.txt"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (processed_dir / "description_clean.txt").write_text(
        "Black over-ear wireless headphones with soft padded ear cushions.",
        encoding="utf-8",
    )
    reviews = [
        ReviewRecord(
            review_id="review-1",
            product_id="1",
            title="Comfortable fit",
            body="comfortable over-ear fit with matte black earcups and a full-size look",
            source_url=HTTP_URL_ADAPTER.validate_python("https://www.target.com/p/sample-headphones/-/A-1"),
        ),
        ReviewRecord(
            review_id="review-2",
            product_id="1",
            title="Good indoors",
            body="soft leatherette pads are nice, but ANC is weaker outdoors in wind",
            source_url=HTTP_URL_ADAPTER.validate_python("https://www.target.com/p/sample-headphones/-/A-1"),
        ),
    ]
    (processed_dir / "reviews_clean.jsonl").write_text(
        "\n".join(review.model_dump_json() for review in reviews) + "\n",
        encoding="utf-8",
    )
