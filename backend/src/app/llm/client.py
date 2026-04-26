"""OpenAI API-only clients for chat-completion JSON and embeddings."""

from __future__ import annotations

import base64
import json
import mimetypes
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

from app.config.settings import Settings, get_settings


class LLMClientError(RuntimeError):
    """Raised when an LLM API call fails."""


@dataclass(slots=True)
class JSONCompletionResult:
    """Raw JSON-mode completion response."""

    text: str
    usage: dict[str, int | float | str]


class OpenAITextAnalysisClient:
    """Minimal OpenAI API-only client for JSON completions and embeddings."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = http_client or httpx.Client(
            timeout=60,
            headers={
                "Authorization": f"Bearer {self._settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> JSONCompletionResult:
        """Request a JSON-only chat completion."""
        payload: dict[str, object] = {
            "model": model or self._settings.llm_analysis_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._post_with_retries(
            endpoint=f"{self._settings.openai_base_url}/chat/completions",
            payload=payload,
        )
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMClientError("OpenAI completion returned no choices.")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("OpenAI completion returned empty content.")
        usage = data.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        return JSONCompletionResult(text=content, usage=usage)

    def complete_json_with_images(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path],
        model: str | None = None,
    ) -> JSONCompletionResult:
        """Request a JSON-only multimodal chat completion."""
        content: list[dict[str, object]] = [{"type": "text", "text": user_prompt}]
        for image_path in image_paths:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._build_image_data_url(image_path)},
                }
            )
        payload: dict[str, object] = {
            "model": model or self._settings.llm_analysis_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._post_with_retries(
            endpoint=f"{self._settings.openai_base_url}/chat/completions",
            payload=payload,
        )
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMClientError("OpenAI multimodal completion returned no choices.")
        message = choices[0].get("message", {})
        content_value = message.get("content")
        if not isinstance(content_value, str) or not content_value.strip():
            raise LLMClientError("OpenAI multimodal completion returned empty content.")
        usage = data.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        return JSONCompletionResult(text=content_value, usage=usage)

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        """Create embedding vectors for the supplied texts."""
        payload: dict[str, object] = {
            "model": model or self._settings.embedding_model,
            "input": texts,
        }
        response = self._post_with_retries(
            endpoint=f"{self._settings.openai_base_url}/embeddings",
            payload=payload,
        )
        data = response.json()
        embeddings = data.get("data", [])
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise LLMClientError("Embedding response shape did not match the input list.")
        result: list[list[float]] = []
        for item in embeddings:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise LLMClientError("Embedding response item is missing an embedding vector.")
            result.append([float(value) for value in item["embedding"]])
        return result

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _post_with_retries(self, *, endpoint: str, payload: dict[str, object]) -> httpx.Response:
        """POST JSON with retry handling for transient OpenAI API failures."""
        last_error: Exception | None = None
        for attempt in range(1, self._settings.llm_max_retries + 1):
            try:
                response = self._client.post(endpoint, content=json.dumps(payload))
                response.raise_for_status()
                return response
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError) as exc:
                last_error = exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in {429, 500, 502, 503, 504}:
                    raise

            if attempt == self._settings.llm_max_retries:
                break
            time.sleep(min(2**attempt, 8))

        raise LLMClientError("OpenAI request failed after multiple attempts.") from last_error

    def _build_image_data_url(self, image_path: Path) -> str:
        """Return a model-compatible data URL for a local image path."""
        media_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
        image_bytes = image_path.read_bytes()
        supported_media_types = {"image/png", "image/jpeg", "image/webp", "image/gif"}

        if media_type not in supported_media_types:
            image_bytes, media_type = self._convert_image_bytes_to_png(
                image_bytes=image_bytes,
                image_path=image_path,
            )

        return f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"

    def _convert_image_bytes_to_png(
        self,
        *,
        image_bytes: bytes,
        image_path: Path,
    ) -> tuple[bytes, str]:
        """Convert unsupported local image bytes to PNG for multimodal requests."""
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                normalized = image.convert("RGBA") if image.mode not in {"RGB", "RGBA"} else image
                buffer = BytesIO()
                normalized.save(buffer, format="PNG")
        except (UnidentifiedImageError, OSError) as exc:
            raise LLMClientError(
                f"Unsupported image format for multimodal completion: {image_path}"
            ) from exc
        return buffer.getvalue(), "image/png"
