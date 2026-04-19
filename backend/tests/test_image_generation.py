"""Q3 image-generation pipeline tests."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.config.settings import Settings
from app.imagegen import (
    GeneratedImageBinary,
    OpenAIImageAdapter,
    StabilityImageAdapter,
    load_prompt_template,
)
from app.models.schemas import VisualAttributeEvidence, VisualMismatchEvidence, VisualProfile
from app.services.image_generation import (
    ImageGenerationPipelineError,
    generate_images_for_product,
)


def test_q3_prompt_templates_load() -> None:
    """All Q3 prompt templates should exist and be loadable."""
    for name in ("pilot", "final"):
        path, content = load_prompt_template(name)
        assert path.exists()
        assert content.strip()


def test_openai_image_adapter_decodes_b64_images() -> None:
    """OpenAI adapter should decode base64 images into byte payloads."""
    png_bytes = _sample_png_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/images/generations")
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["model"] == "gpt-image-1"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"b64_json": base64.b64encode(png_bytes).decode("utf-8")},
                    {"b64_json": base64.b64encode(png_bytes).decode("utf-8")},
                ]
            },
        )

    adapter = OpenAIImageAdapter(
        settings=Settings(OPENAI_API_KEY="test-key"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = adapter.generate(prompt="test prompt", count=2)

    assert len(result) == 2
    assert result[0].image_bytes == png_bytes
    assert result[0].content_type == "image/png"


def test_stability_image_adapter_reads_binary_images() -> None:
    """Stability adapter should return binary images from the HTTP response."""
    png_bytes = _sample_png_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/v2beta/stable-image/generate/core")
        return httpx.Response(
            200,
            content=png_bytes,
            headers={"content-type": "image/png", "seed": "1234"},
        )

    adapter = StabilityImageAdapter(
        settings=Settings(STABILITY_API_KEY="test-key"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = adapter.generate(prompt="test prompt", count=1, negative_prompt="no accessory")

    assert len(result) == 1
    assert result[0].image_bytes == png_bytes
    assert result[0].metadata["seed"] == "1234"


def test_generation_pipeline_writes_manifest_and_images(tmp_path: Path) -> None:
    """Q3 pipeline should write prompt history, images, and manifest artifacts."""
    product_slug = "sample-product"
    _write_generation_inputs(tmp_path=tmp_path, product_slug=product_slug)

    class FakeAdapter:
        provider = "openai"
        model_name = "openai"
        supports_negative_prompt = False

        def generate(
            self,
            *,
            prompt: str,
            count: int,
            negative_prompt: str | None = None,
        ) -> list[GeneratedImageBinary]:
            del prompt, negative_prompt
            return [
                GeneratedImageBinary(
                    image_bytes=_sample_png_bytes(),
                    content_type="image/png",
                    metadata={"index": index},
                )
                for index in range(count)
            ]

    result = generate_images_for_product(
        product_slug=product_slug,
        model_name="openai",
        count=4,
        processed_root=tmp_path / "processed",
        profiles_root=tmp_path / "visual_profiles",
        outputs_root=tmp_path / "generated",
        adapter=FakeAdapter(),
        settings=Settings(OPENAI_API_KEY="test-key"),
    )

    assert result.manifest.status == "completed"
    assert result.prompt_versions_path.exists()
    payload = json.loads(result.prompt_versions_path.read_text(encoding="utf-8"))
    assert len(payload["versions"]) == 2
    assert result.manifest.pilot_generation.images[0].sha256
    assert len(result.manifest.final_generation.images) == 4
    assert result.manifest_path.exists()


def test_generation_pipeline_rejects_invalid_images(tmp_path: Path) -> None:
    """Q3 pipeline should fail if the generated file is not a valid image."""
    product_slug = "sample-product"
    _write_generation_inputs(tmp_path=tmp_path, product_slug=product_slug)

    class InvalidAdapter:
        provider = "stability"
        model_name = "stability"
        supports_negative_prompt = True

        def generate(
            self,
            *,
            prompt: str,
            count: int,
            negative_prompt: str | None = None,
        ) -> list[GeneratedImageBinary]:
            del prompt, count, negative_prompt
            return [GeneratedImageBinary(image_bytes=b"not-an-image", content_type="image/png")]

    with pytest.raises(ImageGenerationPipelineError):
        generate_images_for_product(
            product_slug=product_slug,
            model_name="stability",
            count=1,
            processed_root=tmp_path / "processed",
            profiles_root=tmp_path / "visual_profiles",
            outputs_root=tmp_path / "generated",
            adapter=InvalidAdapter(),
            settings=Settings(STABILITY_API_KEY="test-key"),
        )


def _write_generation_inputs(*, tmp_path: Path, product_slug: str) -> None:
    """Create the minimal processed/product-profile inputs required by Q3."""
    processed_dir = tmp_path / "processed" / product_slug
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "product.json").write_text(
        json.dumps(
            {
                "product_slug": product_slug,
                "product_id": "sample-1",
                "title": "Sample Product",
                "category": "Air Purifier",
                "selected_category": "home",
                "marketplace": "target",
                "source_url": "https://www.target.com/p/sample-product/-/A-1",
                "description_char_count": 120,
                "spec_bullets": ["Color: White", "Finish: Matte", "Material: Plastic"],
                "visible_review_count": 10,
                "cleaned_review_count": 8,
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
    profile_dir = tmp_path / "visual_profiles" / product_slug
    profile_dir.mkdir(parents=True, exist_ok=True)
    baseline = VisualProfile(
        product_name="Sample Product",
        category="Air Purifier",
        high_confidence_visual_attributes=[],
        low_confidence_or_conflicting_attributes=[],
        common_mismatches_between_expectation_and_reality=[],
        prompt_ready_description="A white compact air purifier with a clean matte finish.",
        negative_constraints=["avoid bright accent colors"],
    )
    review_informed = VisualProfile(
        product_name="Sample Product",
        category="Air Purifier",
        high_confidence_visual_attributes=[
            VisualAttributeEvidence(
                attribute="compact rounded rectangular body",
                rationale="Supported by reviews.",
                evidence_snippets=["compact rounded body"],
                source_chunk_ids=["review-1__0"],
                source_review_ids=["review-1"],
            ),
            VisualAttributeEvidence(
                attribute="matte white finish",
                rationale="Listing and reviews align.",
                evidence_snippets=["matte white shell"],
                source_chunk_ids=["review-2__0"],
                source_review_ids=["review-2"],
            ),
        ],
        low_confidence_or_conflicting_attributes=[],
        common_mismatches_between_expectation_and_reality=[
            VisualMismatchEvidence(
                mismatch="do not exaggerate the size beyond a tabletop scale",
                evidence_snippets=["smaller than expected"],
                source_chunk_ids=["review-3__0"],
                source_review_ids=["review-3"],
            )
        ],
        prompt_ready_description=(
            "A compact matte white tabletop air purifier with a rounded rectangular body "
            "and a centered top vent."
        ),
        negative_constraints=["avoid glossy finish", "avoid colorful controls"],
    )
    (profile_dir / "baseline_description_only.json").write_text(
        baseline.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (profile_dir / "review_informed_rag.json").write_text(
        review_informed.model_dump_json(indent=2),
        encoding="utf-8",
    )


def _sample_png_bytes() -> bytes:
    """Return a tiny valid PNG image."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()
