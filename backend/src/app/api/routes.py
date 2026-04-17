"""HTTP routes for the backend API."""

from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter(prefix="/api")


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return a simple health payload."""
    settings = get_settings()
    return {
        "status": "ok",
        "project": settings.project_name,
        "environment": settings.environment,
    }
