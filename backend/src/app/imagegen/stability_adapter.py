"""Stability AI image-generation adapter."""

from __future__ import annotations

import json

import httpx

from app.config.settings import Settings, get_settings
from app.imagegen.base import GeneratedImageBinary, ImageGenerationAdapter, ImageGenerationError


class StabilityImageAdapter(ImageGenerationAdapter):
    """Generate product images through the Stability AI API."""

    provider = "stability"
    supports_negative_prompt = True

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.model_name = self._settings.stability_image_model
        if not self._settings.stability_api_key:
            raise ImageGenerationError(
                "STABILITY_API_KEY is required for Stability image generation."
            )
        self._client = http_client or httpx.Client(
            timeout=self._settings.image_generation_timeout_seconds,
            headers={
                "Authorization": f"Bearer {self._settings.stability_api_key}",
                "Accept": "image/*",
            },
        )

    def generate(
        self,
        *,
        prompt: str,
        count: int,
        negative_prompt: str | None = None,
    ) -> list[GeneratedImageBinary]:
        """Generate one or more product images with Stability."""
        if count < 1:
            raise ImageGenerationError("Stability image generation requires count >= 1.")

        images: list[GeneratedImageBinary] = []
        endpoint = f"{self._settings.stability_base_url}/v2beta/stable-image/generate/core"
        for _ in range(count):
            files = {
                "prompt": (None, prompt),
                "aspect_ratio": (None, self._settings.stability_aspect_ratio),
                "output_format": (None, self._settings.stability_output_format),
            }
            if negative_prompt:
                files["negative_prompt"] = (None, negative_prompt)
            response = self._client.post(endpoint, files=files)
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    payload = response.json()
                except json.JSONDecodeError as exc:
                    raise ImageGenerationError(
                        "Stability returned JSON instead of an image and it could not be decoded."
                    ) from exc
                message = payload.get("message") if isinstance(payload, dict) else None
                raise ImageGenerationError(
                    f"Stability returned JSON instead of an image: {message or payload}"
                )
            response.raise_for_status()
            images.append(
                GeneratedImageBinary(
                    image_bytes=response.content,
                    content_type=response.headers.get("content-type", "image/png"),
                    metadata={
                        "finish_reason": str(response.headers.get("finish-reason", "")),
                        "seed": str(response.headers.get("seed", "")),
                    },
                )
            )
        return images

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
