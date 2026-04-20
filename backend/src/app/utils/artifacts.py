"""Helpers for filesystem artifact paths."""

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

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


def is_repo_artifact_path(path: Path) -> bool:
    """Return whether the path is inside the supported artifact roots."""
    try:
        resolved = path.resolve()
    except FileNotFoundError:
        resolved = path
    for root in (DATA_DIR, OUTPUTS_DIR, DOCS_DIR, PROMPTS_DIR):
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def relative_repo_artifact_path(path: Path) -> str:
    """Return a repo-relative artifact path."""
    return str(path.resolve().relative_to(REPO_ROOT))


def artifact_api_url(path: Path) -> str:
    """Return the HTTP URL used by the frontend to load an artifact file."""
    relative_path = relative_repo_artifact_path(path)
    return f"/api/assets/{quote(relative_path)}"


def artifact_updated_at(path: Path) -> str | None:
    """Return the UTC mtime of an artifact path as ISO-8601."""
    if not path.exists():
        return None
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return timestamp.isoformat()
