"""End-to-end Q4 agentic workflow orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import (
    DataCurationAgentInput,
    EvaluationAgentInput,
    ImageGenerationAgentInput,
    PromptComposerAgentInput,
    RetrievalAgentInput,
    VisualUnderstandingAgentInput,
    WorkflowArtifactHandoff,
    WorkflowRunSummary,
    WorkflowStageStatus,
    WorkflowTrace,
)
from app.utils.artifacts import DATA_DIR, OUTPUTS_DIR, ensure_project_dirs
from app.workflow.agents import (
    DataCurationAgent,
    EvaluationAgent,
    ImageGenerationAgent,
    PromptComposerAgent,
    RetrievalAgent,
    VisualUnderstandingAgent,
)

WORKFLOW_RUNS_DIR = OUTPUTS_DIR / "workflow_runs"
VISUAL_PROFILES_DIR = OUTPUTS_DIR / "visual_profiles"
GENERATED_IMAGES_DIR = OUTPUTS_DIR / "generated_images"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SELECTED_PRODUCTS_PATH = DATA_DIR / "selected_products.jsonl"

STAGE_DEFINITIONS = [
    ("data_curation", "DataCurationAgent", "Q1 Data Curation"),
    ("retrieval", "RetrievalAgent", "Q2 Retrieval"),
    ("visual_understanding", "VisualUnderstandingAgent", "Q2 Visual Understanding"),
    ("prompt_composition", "PromptComposerAgent", "Q3 Prompt Composition"),
    ("image_generation", "ImageGenerationAgent", "Q3 Image Generation"),
    ("evaluation", "EvaluationAgent", "Q3 Comparison and Evaluation"),
]


class WorkflowExecutionError(RuntimeError):
    """Raised when the workflow cannot complete for a requested scope."""


@dataclass(slots=True)
class WorkflowRunResult:
    """Returned after a workflow run is saved to disk."""

    summary: WorkflowRunSummary
    run_dir: Path
    trace_path: Path
    stage_status_path: Path
    artifact_links_path: Path


def run_workflow(
    *,
    product_slug: str | None = None,
    run_all: bool = False,
    refresh: bool = False,
    reuse_existing: bool = True,
    vision_assisted: bool = False,
    count: int = 4,
) -> WorkflowRunResult:
    """Run the agentic workflow for one product or every saved product."""
    if bool(product_slug) == bool(run_all):
        raise WorkflowExecutionError("Choose exactly one of product_slug or run_all.")

    ensure_project_dirs()
    WORKFLOW_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    products = [product_slug] if product_slug else _discover_products_from_artifacts()
    if not products:
        raise WorkflowExecutionError(
            "No artifact-backed products are available. Create raw/processed artifacts first."
        )

    run_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    run_dir = WORKFLOW_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    traces: list[WorkflowTrace] = []
    handoffs: list[WorkflowArtifactHandoff] = []

    data_curation_agent = DataCurationAgent()
    retrieval_agent = RetrievalAgent()
    visual_understanding_agent = VisualUnderstandingAgent()
    prompt_composer_agent = PromptComposerAgent()
    image_generation_agent = ImageGenerationAgent()
    evaluation_agent = EvaluationAgent()

    for slug in products:
        curation_output = _execute_stage(
            traces=traces,
            stage_key="data_curation",
            agent_name="DataCurationAgent",
            inputs={
                "product_slug": slug,
                "selected_products_path": str(SELECTED_PRODUCTS_PATH),
            },
            runner=lambda: data_curation_agent.run(
                DataCurationAgentInput(
                    product_slug=slug,
                    selected_products_path=str(SELECTED_PRODUCTS_PATH),
                    raw_root=str(RAW_DIR),
                    processed_root=str(PROCESSED_DIR),
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )
        _handoff(
            handoffs,
            from_stage="data_curation",
            to_stage="retrieval",
            label="Cleaned corpus and validated Q1 artifacts",
            product_slug=slug,
            artifact_links=curation_output.artifact_links,
        )

        retrieval_output = _execute_stage(
            traces=traces,
            stage_key="retrieval",
            agent_name="RetrievalAgent",
            inputs={
                "product_slug": slug,
                "processed_product_dir": curation_output.processed_product_dir,
            },
            runner=lambda: retrieval_agent.run(
                RetrievalAgentInput(
                    product_slug=slug,
                    processed_product_dir=curation_output.processed_product_dir,
                    output_dir=str(VISUAL_PROFILES_DIR / slug),
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )
        _handoff(
            handoffs,
            from_stage="retrieval",
            to_stage="visual_understanding",
            label="Aspect-specific review evidence",
            product_slug=slug,
            artifact_links=retrieval_output.artifact_links,
        )

        visual_output = _execute_stage(
            traces=traces,
            stage_key="visual_understanding",
            agent_name="VisualUnderstandingAgent",
            inputs={
                "product_slug": slug,
                "processed_product_dir": curation_output.processed_product_dir,
            },
            runner=lambda: visual_understanding_agent.run(
                VisualUnderstandingAgentInput(
                    product_slug=slug,
                    processed_product_dir=curation_output.processed_product_dir,
                    output_dir=str(VISUAL_PROFILES_DIR / slug),
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )
        _handoff(
            handoffs,
            from_stage="visual_understanding",
            to_stage="prompt_composition",
            label="Structured visual profile",
            product_slug=slug,
            artifact_links=visual_output.artifact_links,
        )

        prompt_output = _execute_stage(
            traces=traces,
            stage_key="prompt_composition",
            agent_name="PromptComposerAgent",
            inputs={
                "product_slug": slug,
                "visual_profile_dir": str(VISUAL_PROFILES_DIR / slug),
            },
            runner=lambda: prompt_composer_agent.run(
                PromptComposerAgentInput(
                    product_slug=slug,
                    visual_profile_dir=str(VISUAL_PROFILES_DIR / slug),
                    generation_root=str(GENERATED_IMAGES_DIR),
                    providers=["openai", "stability"],
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )
        _handoff(
            handoffs,
            from_stage="prompt_composition",
            to_stage="image_generation",
            label="Pilot and final prompt plans",
            product_slug=slug,
            artifact_links=prompt_output.artifact_links,
        )

        generation_output = _execute_stage(
            traces=traces,
            stage_key="image_generation",
            agent_name="ImageGenerationAgent",
            inputs={
                "product_slug": slug,
                "providers": "openai,stability",
            },
            runner=lambda: image_generation_agent.run(
                ImageGenerationAgentInput(
                    product_slug=slug,
                    providers=["openai", "stability"],
                    count=count,
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )
        _handoff(
            handoffs,
            from_stage="image_generation",
            to_stage="evaluation",
            label="Generated product image manifests",
            product_slug=slug,
            artifact_links=generation_output.artifact_links,
        )

        _execute_stage(
            traces=traces,
            stage_key="evaluation",
            agent_name="EvaluationAgent",
            inputs={
                "product_slug": slug,
                "vision_assisted": str(vision_assisted),
            },
            runner=lambda: evaluation_agent.run(
                EvaluationAgentInput(
                    product_slug=slug,
                    vision_assisted=vision_assisted,
                    refresh=refresh,
                    reuse_existing=reuse_existing,
                )
            ),
        )

    stages = _aggregate_stage_status(products=products, traces=traces)
    status = _workflow_status_from_traces(traces)
    summary = WorkflowRunSummary(
        run_id=run_id,
        created_at=datetime.now(tz=UTC),
        scope="single" if product_slug else "all",
        products=products,
        status=status,
        stages=stages,
        traces=traces,
        artifact_handoffs=handoffs,
    )

    trace_path = run_dir / "trace.json"
    stage_status_path = run_dir / "stage_status.json"
    artifact_links_path = run_dir / "artifact_links.json"
    trace_path.write_text(
        json.dumps([trace.model_dump(mode="json") for trace in traces], indent=2),
        encoding="utf-8",
    )
    stage_status_path.write_text(
        json.dumps([stage.model_dump(mode="json") for stage in stages], indent=2),
        encoding="utf-8",
    )
    artifact_links_path.write_text(
        json.dumps([handoff.model_dump(mode="json") for handoff in handoffs], indent=2),
        encoding="utf-8",
    )
    return WorkflowRunResult(
        summary=summary,
        run_dir=run_dir,
        trace_path=trace_path,
        stage_status_path=stage_status_path,
        artifact_links_path=artifact_links_path,
    )


def plan_workflow() -> list[WorkflowTrace]:
    """Return the latest saved workflow trace, if present."""
    latest = load_latest_workflow_run()
    return latest.summary.traces if latest else []


def load_latest_workflow_run() -> WorkflowRunResult | None:
    """Load the latest saved workflow run from disk."""
    if not WORKFLOW_RUNS_DIR.exists():
        return None
    candidates = [path for path in WORKFLOW_RUNS_DIR.iterdir() if path.is_dir()]
    if not candidates:
        return None
    latest_dir = max(candidates, key=lambda path: path.stat().st_mtime)
    trace_path = latest_dir / "trace.json"
    stage_status_path = latest_dir / "stage_status.json"
    artifact_links_path = latest_dir / "artifact_links.json"
    if not trace_path.exists() or not stage_status_path.exists() or not artifact_links_path.exists():
        return None

    traces = [WorkflowTrace.model_validate(item) for item in json.loads(trace_path.read_text())]
    stages = [WorkflowStageStatus.model_validate(item) for item in json.loads(stage_status_path.read_text())]
    handoffs = [
        WorkflowArtifactHandoff.model_validate(item)
        for item in json.loads(artifact_links_path.read_text())
    ]
    products = sorted(
        {
            trace.inputs.get("product_slug", "")
            for trace in traces
            if trace.inputs.get("product_slug")
        }
    )
    summary = WorkflowRunSummary(
        run_id=latest_dir.name,
        created_at=traces[0].started_at if traces else datetime.fromtimestamp(latest_dir.stat().st_mtime, tz=UTC),
        scope="single" if len(products) == 1 else "all",
        products=products,
        status=_workflow_status_from_traces(traces),
        stages=stages,
        traces=traces,
        artifact_handoffs=handoffs,
    )
    return WorkflowRunResult(
        summary=summary,
        run_dir=latest_dir,
        trace_path=trace_path,
        stage_status_path=stage_status_path,
        artifact_links_path=artifact_links_path,
    )


def _execute_stage(*, traces: list[WorkflowTrace], stage_key: str, agent_name: str, inputs: dict[str, str], runner):
    started_at = datetime.now(tz=UTC)
    try:
        output = runner()
    except Exception as exc:
        traces.append(
            WorkflowTrace(
                trace_id=f"{stage_key}-{inputs.get('product_slug', 'scope')}",
                stage=stage_key,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(tz=UTC),
                inputs=inputs,
                outputs={},
                notes=[agent_name, str(exc)],
            )
        )
        raise WorkflowExecutionError(f"{agent_name} failed for {inputs.get('product_slug')}: {exc}") from exc

    outputs = {
        key: value
        for key, value in output.model_dump(mode="json").items()
        if isinstance(value, str) and value
    }
    notes = [agent_name]
    if getattr(output, "reused_existing", False):
        notes.append("reused_existing")
    traces.append(
        WorkflowTrace(
            trace_id=f"{stage_key}-{inputs.get('product_slug', 'scope')}",
            stage=stage_key,
            status="completed",
            started_at=started_at,
            finished_at=datetime.now(tz=UTC),
            inputs=inputs,
            outputs=outputs,
            notes=notes,
        )
    )
    return output


def _handoff(
    handoffs: list[WorkflowArtifactHandoff],
    *,
    from_stage: str,
    to_stage: str,
    label: str,
    product_slug: str,
    artifact_links: dict[str, str],
) -> None:
    handoffs.append(
        WorkflowArtifactHandoff(
            from_stage=from_stage,
            to_stage=to_stage,
            label=label,
            product_slug=product_slug,
            artifact_paths=sorted(set(artifact_links.values())),
        )
    )


def _aggregate_stage_status(
    *,
    products: list[str],
    traces: list[WorkflowTrace],
) -> list[WorkflowStageStatus]:
    statuses: list[WorkflowStageStatus] = []
    total_count = len(products)
    for stage_key, agent_name, label in STAGE_DEFINITIONS:
        stage_traces = [trace for trace in traces if trace.stage == stage_key]
        completed_products = sorted(
            {
                trace.inputs.get("product_slug", "")
                for trace in stage_traces
                if trace.status == "completed" and trace.inputs.get("product_slug")
            }
        )
        failed_products = sorted(
            {
                trace.inputs.get("product_slug", "")
                for trace in stage_traces
                if trace.status == "failed" and trace.inputs.get("product_slug")
            }
        )
        if failed_products:
            status = "failed"
            detail = f"Failed for {', '.join(failed_products)}."
        elif len(completed_products) == total_count and total_count > 0:
            status = "completed"
            detail = f"Completed for all {total_count} products."
        elif completed_products:
            status = "running"
            detail = f"Completed for {len(completed_products)}/{total_count} products."
        else:
            status = "pending"
            detail = "No executions recorded yet."
        statuses.append(
            WorkflowStageStatus(
                stage_key=stage_key,
                label=label,
                agent_name=agent_name,
                status=status,
                completed_count=len(completed_products),
                total_count=total_count,
                products=completed_products,
                detail=detail,
            )
        )
    return statuses


def _workflow_status_from_traces(traces: list[WorkflowTrace]) -> str:
    if any(trace.status == "failed" for trace in traces):
        return "failed"
    if traces:
        return "completed"
    return "partial_success"


def _discover_products_from_artifacts() -> list[str]:
    if PROCESSED_DIR.exists():
        slugs = sorted(
            path.name for path in PROCESSED_DIR.iterdir() if path.is_dir() and (path / "product.json").exists()
        )
        if slugs:
            return slugs
    if RAW_DIR.exists():
        slugs = sorted(
            path.name for path in RAW_DIR.iterdir() if path.is_dir() and (path / "product_meta.json").exists()
        )
        if slugs:
            return slugs
    return []
