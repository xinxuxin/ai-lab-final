"""Editable prompt-template loading helpers for Q3 image generation."""

from __future__ import annotations

from pathlib import Path

from app.utils.artifacts import PROMPTS_DIR

Q3_PROMPTS_DIR = PROMPTS_DIR / "q3"
PROMPT_PATHS = {
    "pilot": Q3_PROMPTS_DIR / "pilot_prompt.md",
    "final": Q3_PROMPTS_DIR / "final_prompt.md",
}


def load_prompt_template(name: str) -> tuple[Path, str]:
    """Load one editable Q3 prompt template."""
    path = PROMPT_PATHS.get(name)
    if path is None:
        available = ", ".join(sorted(PROMPT_PATHS))
        raise KeyError(f"Unknown prompt template '{name}'. Available: {available}")
    if not path.exists():
        raise FileNotFoundError(f"Prompt template is missing: {path}")
    return path, path.read_text(encoding="utf-8")
