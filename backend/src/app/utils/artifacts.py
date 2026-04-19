"""Helpers for filesystem artifact paths."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
DOCS_DIR = REPO_ROOT / "docs"
DATA_DIR = REPO_ROOT / "data"
OUTPUTS_DIR = REPO_ROOT / "outputs"
PROMPTS_DIR = REPO_ROOT / "prompts"


def ensure_project_dirs() -> None:
    """Ensure top-level artifact directories exist."""
    for path in [ARTIFACTS_DIR, DOCS_DIR, DATA_DIR, OUTPUTS_DIR, PROMPTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
