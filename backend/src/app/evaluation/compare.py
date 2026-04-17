"""Evaluation placeholders."""

from app.models.schemas import EvaluationRecord


def compare_generated_images(product_id: str) -> EvaluationRecord | None:
    """Placeholder comparison entrypoint."""
    del product_id
    return None
