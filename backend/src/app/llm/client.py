"""OpenAI API-only clients for chat-completion JSON and embeddings."""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

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
        payload = {
            "model": model or self._settings.llm_analysis_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._client.post(
            f"{self._settings.openai_base_url}/chat/completions",
            content=json.dumps(payload),
        )
        response.raise_for_status()
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

    def embed_texts(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        """Create embedding vectors for the supplied texts."""
        payload = {
            "model": model or self._settings.embedding_model,
            "input": texts,
        }
        response = self._client.post(
            f"{self._settings.openai_base_url}/embeddings",
            content=json.dumps(payload),
        )
        response.raise_for_status()
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
