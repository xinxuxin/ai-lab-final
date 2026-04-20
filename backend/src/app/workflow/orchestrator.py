"""Agentic workflow scaffolding."""

from typing import Literal

from app.models.schemas import WorkflowTrace
from app.services.dashboard_data import workflow_latest_payload


def plan_workflow() -> list[WorkflowTrace]:
    """Return workflow traces derived from real artifact status."""
    payload = workflow_latest_payload()
    traces: list[WorkflowTrace] = []
    for index, trace in enumerate(payload.get("traces", []), start=1):
        if not isinstance(trace, dict):
            continue
        status: Literal["pending", "running", "completed", "failed"] = "pending"
        note = str(trace.get("note", ""))
        if "available" in note:
            status = "running"
        if "artifact targets are available." in note and "so far" not in note:
            status = "completed"
        traces.append(
            WorkflowTrace(
                trace_id=f"trace-{index}",
                stage=str(trace.get("stage", "unknown")),
                status=status,
                outputs={"artifact": str(trace.get("artifact", ""))},
                notes=[note],
            )
        )
    return traces
