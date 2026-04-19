"""Editable prompt-template loading helpers for Q2 analysis."""

from __future__ import annotations

from pathlib import Path

from app.utils.artifacts import PROMPTS_DIR

Q2_PROMPTS_DIR = PROMPTS_DIR / "q2"
PROMPT_PATHS = {
    "aspect_evidence_extraction": Q2_PROMPTS_DIR / "aspect_evidence_extraction.md",
    "conflict_resolution": Q2_PROMPTS_DIR / "conflict_resolution.md",
    "final_visual_profile_synthesis": Q2_PROMPTS_DIR / "final_visual_profile_synthesis.md",
}

Q2_SYSTEM_PROMPT = (
    "You are a careful product analyst. Use only the supplied product description, "
    "spec bullets, and evidence snippets. Never invent unsupported visual attributes. "
    "Prefer explicit uncertainty over speculation."
)


def load_prompt_template(name: str) -> tuple[Path, str]:
    """Load one editable prompt template by logical name."""
    path = PROMPT_PATHS.get(name)
    if path is None:
        available = ", ".join(sorted(PROMPT_PATHS))
        raise KeyError(f"Unknown prompt template '{name}'. Available: {available}")
    if not path.exists():
        raise FileNotFoundError(f"Prompt template is missing: {path}")
    return path, path.read_text(encoding="utf-8")
