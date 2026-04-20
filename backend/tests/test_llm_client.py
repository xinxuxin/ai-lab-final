"""Tests for the OpenAI API client helpers."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.config.settings import Settings
from app.llm.client import OpenAITextAnalysisClient


def test_build_image_data_url_keeps_supported_png(tmp_path: Path) -> None:
    """Supported formats should be passed through without conversion."""
    image_path = tmp_path / "sample.png"
    _write_image(image_path, format="PNG")

    client = OpenAITextAnalysisClient(settings=Settings(OPENAI_API_KEY="test-key"))
    try:
        data_url = client._build_image_data_url(image_path)
    finally:
        client.close()

    assert data_url.startswith("data:image/png;base64,")


def test_build_image_data_url_converts_unsupported_format_to_png(tmp_path: Path) -> None:
    """Unsupported formats should be converted before being sent to the API."""
    image_path = tmp_path / "sample.bmp"
    _write_image(image_path, format="BMP")

    client = OpenAITextAnalysisClient(settings=Settings(OPENAI_API_KEY="test-key"))
    try:
        data_url = client._build_image_data_url(image_path)
    finally:
        client.close()

    assert data_url.startswith("data:image/png;base64,")
    encoded = data_url.split(",", 1)[1]
    converted = Image.open(BytesIO(base64.b64decode(encoded)))
    assert converted.format == "PNG"


def _write_image(path: Path, *, format: str) -> None:
    """Write a small image fixture for client tests."""
    image = Image.new("RGB", (4, 4), color=(255, 255, 255))
    image.save(path, format=format)
