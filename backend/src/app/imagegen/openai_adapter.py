"""OpenAI Images API adapter."""

from __future__ import annotations

import base64
import json
import time

import httpx

from app.config.settings import Settings, get_settings
from app.imagegen.base import GeneratedImageBinary, ImageGenerationAdapter, ImageGenerationError


class OpenAIImageAdapter(ImageGenerationAdapter):
    """Generate product images through the OpenAI Images API."""

    provider = "openai"
    supports_negative_prompt = False

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.model_name = self._settings.openai_image_model
        if not self._settings.openai_api_key:
            raise ImageGenerationError("OPENAI_API_KEY is required for OpenAI image generation.")
        self._client = http_client or httpx.Client(
            timeout=self._settings.image_generation_timeout_seconds,
            headers={
                "Authorization": f"Bearer {self._settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )

    def generate(
        self,
        *,
        prompt: str,
        count: int,
        negative_prompt: str | None = None,
    ) -> list[GeneratedImageBinary]:
        """Generate one or more product images with OpenAI."""
        if count < 1:
            raise ImageGenerationError("OpenAI image generation requires count >= 1.")
        composed_prompt = prompt
        if negative_prompt:
            composed_prompt = f"{prompt}\n\nAvoid: {negative_prompt}"
        payload = {
            "model": self.model_name,
            "prompt": composed_prompt,
            "size": self._settings.openai_image_size,
            "n": count,
        }
        response: httpx.Response | None = None
        last_error: Exception | None = None
        for attempt in range(1, self._settings.llm_max_retries + 1):
            try:
                response = self._client.post(
                    f"{self._settings.openai_base_url}/images/generations",
                    content=json.dumps(payload),
                )
                response.raise_for_status()
                last_error = None
                break
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError) as exc:
                last_error = exc
                if attempt == self._settings.llm_max_retries:
                    raise ImageGenerationError(
                        "OpenAI image generation timed out after multiple attempts."
                    ) from exc
                time.sleep(min(2**attempt, 5))

        if response is None:
            raise ImageGenerationError(
                "OpenAI image generation returned no response."
            ) from last_error

        data = response.json()
        raw_items = data.get("data", [])
        if not isinstance(raw_items, list) or len(raw_items) != count:
            raise ImageGenerationError("OpenAI Images API returned an unexpected payload.")

        images: list[GeneratedImageBinary] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise ImageGenerationError("OpenAI Images API item had an unexpected shape.")
            b64_json = item.get("b64_json")
            if not isinstance(b64_json, str):
                raise ImageGenerationError("OpenAI Images API item is missing image bytes.")
            images.append(
                GeneratedImageBinary(
                    image_bytes=base64.b64decode(b64_json),
                    content_type="image/png",
                    metadata={
                        "revised_prompt": str(item.get("revised_prompt") or ""),
                    },
                )
            )
        return images

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
