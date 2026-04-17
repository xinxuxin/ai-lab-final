"""Filesystem manifest helpers."""

from pathlib import Path


def list_json_manifests(root: Path) -> list[Path]:
    """List JSON manifests under the provided root."""
    return sorted(root.rglob("*.json"))
