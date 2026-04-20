"""Evaluation entrypoints."""

from app.services.evaluation import EvaluateImagesResult, evaluate_images_for_product


def compare_generated_images(product_slug: str) -> EvaluateImagesResult:
    """Build evaluation artifacts for one product slug."""
    return evaluate_images_for_product(product_slug=product_slug)
