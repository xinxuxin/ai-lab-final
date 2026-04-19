"""Adapter interfaces for API-only image generation providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class ImageGenerationError(RuntimeError):
    """Raised when an image-generation API call fails."""


@dataclass(slots=True)
class GeneratedImageBinary:
    """Raw generated image bytes returned by a provider."""

    image_bytes: bytes
    content_type: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


class ImageGenerationAdapter(Protocol):
    """Protocol for provider-specific image generation adapters."""

    provider: str
    model_name: str
    supports_negative_prompt: bool

    def generate(
        self,
        *,
        prompt: str,
        count: int,
        negative_prompt: str | None = None,
    ) -> list[GeneratedImageBinary]:
        """Generate one or more images for a prompt."""
