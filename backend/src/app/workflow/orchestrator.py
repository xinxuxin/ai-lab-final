"""Agentic workflow scaffolding."""

from app.models.schemas import WorkflowTrace


def plan_workflow() -> list[WorkflowTrace]:
    """Return placeholder workflow traces for the demo UI."""
    stages = [
        "discover-products",
        "scrape-all",
        "build-corpus",
        "extract-visual-profile",
        "generate-images",
        "evaluate-images",
    ]
    return [
        WorkflowTrace(trace_id=f"trace-{idx}", stage=stage, status="pending")
        for idx, stage in enumerate(stages, start=1)
    ]
