"""Application services for corpus building and manifests."""

from app.services.corpus import (
    BuildCorpusResult,
    CorpusBuildError,
    build_processed_corpus,
    validate_q1_artifacts,
    validate_q1_from_disk,
)
from app.services.evaluation import (
    EvaluateImagesResult,
    EvaluationError,
    evaluate_images_for_product,
    list_evaluation_ready_products,
)
from app.services.image_generation import (
    GenerateImagesResult,
    ImageGenerationPipelineError,
    generate_images_for_product,
    list_generation_ready_products,
)
from app.services.verification import (
    SubmissionPackageResult,
    VerificationResult,
    build_submission_package,
    verify_repository,
)
from app.services.visual_profiles import (
    ExtractVisualProfileResult,
    VisualProfileError,
    chunk_reviews,
    extract_visual_profile,
)

__all__ = [
    "BuildCorpusResult",
    "CorpusBuildError",
    "EvaluateImagesResult",
    "EvaluationError",
    "ExtractVisualProfileResult",
    "GenerateImagesResult",
    "ImageGenerationPipelineError",
    "SubmissionPackageResult",
    "VerificationResult",
    "VisualProfileError",
    "build_processed_corpus",
    "build_submission_package",
    "chunk_reviews",
    "evaluate_images_for_product",
    "extract_visual_profile",
    "generate_images_for_product",
    "list_evaluation_ready_products",
    "list_generation_ready_products",
    "validate_q1_artifacts",
    "validate_q1_from_disk",
    "verify_repository",
]
