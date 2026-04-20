"""HTTP routes for the backend API."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config.settings import get_settings
from app.services.dashboard_data import (
    evaluation_payload,
    generation_payload,
    list_products_payload,
    product_detail_payload,
    profile_payload,
    review_stats_payload,
    workflow_latest_payload,
)
from app.utils.artifacts import REPO_ROOT, is_repo_artifact_path

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


@router.get("/products", tags=["products"])
def products() -> dict[str, object]:
    """Return selected products and artifact status."""
    return list_products_payload()


@router.get("/products/{slug}", tags=["products"])
def product_detail(slug: str) -> dict[str, object]:
    """Return one product detail payload."""
    try:
        return product_detail_payload(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reviews/{slug}/stats", tags=["reviews"])
def review_stats(slug: str) -> dict[str, object]:
    """Return one product's review stats and retrieval evidence."""
    try:
        return review_stats_payload(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/profiles/{slug}", tags=["profiles"])
def profiles(slug: str) -> dict[str, object]:
    """Return saved visual-profile outputs for one product."""
    try:
        return profile_payload(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/generation/{slug}", tags=["generation"])
def generation(slug: str) -> dict[str, object]:
    """Return generation artifacts for one product."""
    try:
        return generation_payload(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/evaluation/{slug}", tags=["evaluation"])
def evaluation(slug: str) -> dict[str, object]:
    """Return evaluation artifacts for one product."""
    try:
        return evaluation_payload(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflow/latest", tags=["workflow"])
def workflow_latest() -> dict[str, object]:
    """Return the latest artifact-backed workflow snapshot."""
    return workflow_latest_payload()


@router.get("/assets/{artifact_path:path}", tags=["assets"])
def assets(artifact_path: str) -> FileResponse:
    """Serve an artifact file from the repository's data or output roots."""
    candidate = (REPO_ROOT / artifact_path).resolve()
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_path}")
    if not is_repo_artifact_path(candidate):
        raise HTTPException(status_code=403, detail="Artifact path is outside allowed roots.")
    media_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    return FileResponse(path=candidate, media_type=media_type, filename=Path(artifact_path).name)
