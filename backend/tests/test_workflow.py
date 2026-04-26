"""Workflow contract and orchestration tests."""

from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch

from app.models.schemas import (
    DataCurationAgentInput,
    DataCurationAgentOutput,
    EvaluationAgentInput,
    EvaluationAgentOutput,
    ImageGenerationAgentInput,
    ImageGenerationAgentOutput,
    PromptComposerAgentInput,
    PromptComposerAgentOutput,
    RetrievalAgentInput,
    RetrievalAgentOutput,
    VisualUnderstandingAgentInput,
    VisualUnderstandingAgentOutput,
)
from app.services.dashboard_data import workflow_latest_payload
from app.workflow.orchestrator import load_latest_workflow_run, run_workflow


def test_workflow_contract_models_round_trip() -> None:
    """Workflow agent contracts should validate typed payloads."""
    data_input = DataCurationAgentInput(
        product_slug="sample-product",
        selected_products_path="data/selected_products.jsonl",
        raw_root="data/raw",
        processed_root="data/processed",
    )
    data_output = DataCurationAgentOutput(
        product_slug="sample-product",
        selected_category="lighting",
        raw_product_dir="data/raw/sample-product",
        processed_product_dir="data/processed/sample-product",
        q1_validation_passed=True,
        review_count=10,
        image_count=3,
    )
    retrieval_input = RetrievalAgentInput(
        product_slug="sample-product",
        processed_product_dir="data/processed/sample-product",
        output_dir="outputs/visual_profiles/sample-product",
    )
    retrieval_output = RetrievalAgentOutput(
        product_slug="sample-product",
        retrieval_evidence_path="outputs/visual_profiles/sample-product/retrieval_evidence.json",
        llm_trace_path="outputs/visual_profiles/sample-product/llm_trace.json",
        aspect_count=5,
    )
    visual_input = VisualUnderstandingAgentInput(
        product_slug="sample-product",
        processed_product_dir="data/processed/sample-product",
        output_dir="outputs/visual_profiles/sample-product",
    )
    visual_output = VisualUnderstandingAgentOutput(
        product_slug="sample-product",
        baseline_profile_path="outputs/visual_profiles/sample-product/baseline_description_only.json",
        review_profile_path="outputs/visual_profiles/sample-product/review_informed_rag.json",
        prompt_ready_description="A white matte product.",
    )
    prompt_input = PromptComposerAgentInput(
        product_slug="sample-product",
        visual_profile_dir="outputs/visual_profiles/sample-product",
        generation_root="outputs/generated_images",
        providers=["openai", "stability"],
    )
    prompt_output = PromptComposerAgentOutput(
        product_slug="sample-product",
        prompt_sources={"openai": "saved_prompt_versions"},
        prompt_previews={"openai": {"pilot": "Pilot prompt", "final": "Final prompt"}},
    )
    image_input = ImageGenerationAgentInput(
        product_slug="sample-product",
        providers=["openai", "stability"],
    )
    image_output = ImageGenerationAgentOutput(
        product_slug="sample-product",
        generated_models=["openai", "stability"],
        generation_manifest_paths={
            "openai": "outputs/generated_images/sample-product/openai/generation_manifest.json"
        },
    )
    evaluation_input = EvaluationAgentInput(product_slug="sample-product", vision_assisted=False)
    evaluation_output = EvaluationAgentOutput(
        product_slug="sample-product",
        summary_path="outputs/evaluations/sample-product/summary.json",
        comparison_panels_manifest_path="outputs/evaluations/sample-product/comparison_panels_manifest.json",
        human_score_sheet_path="outputs/evaluations/sample-product/human_score_sheet.csv",
        vision_assisted_eval_path="outputs/evaluations/sample-product/vision_assisted_eval.json",
        evaluation_status="human_scoring_ready",
    )

    assert data_input.product_slug == data_output.product_slug
    assert retrieval_input.product_slug == retrieval_output.product_slug
    assert visual_input.product_slug == visual_output.product_slug
    assert prompt_input.providers == ["openai", "stability"]
    assert prompt_output.prompt_sources["openai"] == "saved_prompt_versions"
    assert image_input.providers == image_output.generated_models
    assert evaluation_input.product_slug == evaluation_output.product_slug


def test_run_workflow_smoke_with_mocked_agents(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The orchestrator should write trace, stage status, and handoff artifacts."""

    class FakeDataCurationAgent:
        def run(self, payload: DataCurationAgentInput) -> DataCurationAgentOutput:
            return DataCurationAgentOutput(
                product_slug=payload.product_slug,
                selected_category="lighting",
                raw_product_dir=str(tmp_path / "data" / "raw" / payload.product_slug),
                processed_product_dir=str(tmp_path / "data" / "processed" / payload.product_slug),
                q1_validation_passed=True,
                review_count=8,
                image_count=2,
                artifact_links={"processed_product": "data/processed/sample-product/product.json"},
            )

    class FakeRetrievalAgent:
        def run(self, payload: RetrievalAgentInput) -> RetrievalAgentOutput:
            return RetrievalAgentOutput(
                product_slug=payload.product_slug,
                retrieval_evidence_path=str(
                    tmp_path
                    / "outputs"
                    / "visual_profiles"
                    / payload.product_slug
                    / "retrieval_evidence.json"
                ),
                llm_trace_path=str(
                    tmp_path
                    / "outputs"
                    / "visual_profiles"
                    / payload.product_slug
                    / "llm_trace.json"
                ),
                aspect_count=5,
                artifact_links={
                    "retrieval_evidence": (
                        "outputs/visual_profiles/sample-product/retrieval_evidence.json"
                    )
                },
            )

    class FakeVisualUnderstandingAgent:
        def run(self, payload: VisualUnderstandingAgentInput) -> VisualUnderstandingAgentOutput:
            return VisualUnderstandingAgentOutput(
                product_slug=payload.product_slug,
                baseline_profile_path=str(
                    tmp_path
                    / "outputs"
                    / "visual_profiles"
                    / payload.product_slug
                    / "baseline_description_only.json"
                ),
                review_profile_path=str(
                    tmp_path
                    / "outputs"
                    / "visual_profiles"
                    / payload.product_slug
                    / "review_informed_rag.json"
                ),
                prompt_ready_description="Prompt-ready description",
                artifact_links={
                    "review_profile": (
                        "outputs/visual_profiles/sample-product/review_informed_rag.json"
                    )
                },
            )

    class FakePromptComposerAgent:
        def run(self, payload: PromptComposerAgentInput) -> PromptComposerAgentOutput:
            return PromptComposerAgentOutput(
                product_slug=payload.product_slug,
                prompt_sources={
                    "openai": "visual_profile_templates",
                    "stability": "visual_profile_templates",
                },
                prompt_previews={"openai": {"pilot": "pilot", "final": "final"}},
            )

    class FakeImageGenerationAgent:
        def run(self, payload: ImageGenerationAgentInput) -> ImageGenerationAgentOutput:
            return ImageGenerationAgentOutput(
                product_slug=payload.product_slug,
                generated_models=payload.providers,
                generation_manifest_paths={
                    provider: (
                        f"outputs/generated_images/{payload.product_slug}/"
                        f"{provider}/generation_manifest.json"
                    )
                    for provider in payload.providers
                },
                artifact_links={
                    provider: (
                        f"outputs/generated_images/{payload.product_slug}/"
                        f"{provider}/generation_manifest.json"
                    )
                    for provider in payload.providers
                },
            )

    class FakeEvaluationAgent:
        def run(self, payload: EvaluationAgentInput) -> EvaluationAgentOutput:
            return EvaluationAgentOutput(
                product_slug=payload.product_slug,
                summary_path=f"outputs/evaluations/{payload.product_slug}/summary.json",
                comparison_panels_manifest_path=f"outputs/evaluations/{payload.product_slug}/comparison_panels_manifest.json",
                human_score_sheet_path=f"outputs/evaluations/{payload.product_slug}/human_score_sheet.csv",
                vision_assisted_eval_path=f"outputs/evaluations/{payload.product_slug}/vision_assisted_eval.json",
                evaluation_status="human_scoring_ready",
                artifact_links={
                    "summary": f"outputs/evaluations/{payload.product_slug}/summary.json"
                },
            )

    monkeypatch.setattr(
        "app.workflow.orchestrator.WORKFLOW_RUNS_DIR", tmp_path / "outputs" / "workflow_runs"
    )
    monkeypatch.setattr("app.workflow.orchestrator.PROCESSED_DIR", tmp_path / "data" / "processed")
    monkeypatch.setattr("app.workflow.orchestrator.RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(
        "app.workflow.orchestrator.SELECTED_PRODUCTS_PATH",
        tmp_path / "data" / "selected_products.jsonl",
    )
    monkeypatch.setattr(
        "app.workflow.orchestrator.VISUAL_PROFILES_DIR", tmp_path / "outputs" / "visual_profiles"
    )
    monkeypatch.setattr(
        "app.workflow.orchestrator.GENERATED_IMAGES_DIR", tmp_path / "outputs" / "generated_images"
    )
    monkeypatch.setattr("app.workflow.orchestrator.DataCurationAgent", FakeDataCurationAgent)
    monkeypatch.setattr("app.workflow.orchestrator.RetrievalAgent", FakeRetrievalAgent)
    monkeypatch.setattr(
        "app.workflow.orchestrator.VisualUnderstandingAgent", FakeVisualUnderstandingAgent
    )
    monkeypatch.setattr("app.workflow.orchestrator.PromptComposerAgent", FakePromptComposerAgent)
    monkeypatch.setattr("app.workflow.orchestrator.ImageGenerationAgent", FakeImageGenerationAgent)
    monkeypatch.setattr("app.workflow.orchestrator.EvaluationAgent", FakeEvaluationAgent)
    monkeypatch.setattr(
        "app.workflow.orchestrator._discover_products_from_artifacts",
        lambda: ["sample-product"],
    )

    result = run_workflow(run_all=True)

    assert result.trace_path.exists()
    assert result.stage_status_path.exists()
    assert result.artifact_links_path.exists()
    assert result.summary.status == "completed"
    traces = json.loads(result.trace_path.read_text(encoding="utf-8"))
    assert len(traces) == 6


def test_latest_workflow_trace_generation(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Latest workflow payload should expose saved stage and handoff data."""
    run_dir = tmp_path / "outputs" / "workflow_runs" / "20260420T120000Z-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    trace_payload = [
        {
            "trace_id": "data_curation-sample-product",
            "stage": "data_curation",
            "status": "completed",
            "started_at": "2026-04-20T12:00:00Z",
            "finished_at": "2026-04-20T12:00:01Z",
            "inputs": {"product_slug": "sample-product"},
            "outputs": {"processed_product_dir": "data/processed/sample-product"},
            "notes": ["DataCurationAgent"],
        }
    ]
    stage_payload = [
        {
            "stage_key": "data_curation",
            "label": "Q1 Data Curation",
            "agent_name": "DataCurationAgent",
            "status": "completed",
            "completed_count": 1,
            "total_count": 1,
            "products": ["sample-product"],
            "detail": "Completed for all 1 products.",
        }
    ]
    handoff_payload = [
        {
            "from_stage": "data_curation",
            "to_stage": "retrieval",
            "label": "Cleaned corpus and validated Q1 artifacts",
            "product_slug": "sample-product",
            "artifact_paths": ["data/processed/sample-product/product.json"],
        }
    ]
    (run_dir / "trace.json").write_text(json.dumps(trace_payload), encoding="utf-8")
    (run_dir / "stage_status.json").write_text(json.dumps(stage_payload), encoding="utf-8")
    (run_dir / "artifact_links.json").write_text(json.dumps(handoff_payload), encoding="utf-8")

    monkeypatch.setattr(
        "app.workflow.orchestrator.WORKFLOW_RUNS_DIR", tmp_path / "outputs" / "workflow_runs"
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.WORKFLOW_RUNS_DIR",
        tmp_path / "outputs" / "workflow_runs",
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.dashboard_data.artifact_api_url",
        lambda path: f"/api/assets/{Path(path).name}",
    )

    latest = load_latest_workflow_run()
    payload = workflow_latest_payload()

    assert latest is not None
    assert latest.summary.run_id == "20260420T120000Z-test"
    assert payload["latestRun"]["runId"] == "20260420T120000Z-test"
    assert payload["handoffs"][0]["fromStage"] == "data_curation"
