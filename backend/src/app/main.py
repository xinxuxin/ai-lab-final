"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config.settings import get_settings


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Generating Product Image from Customer Reviews",
        version="0.1.0",
        description="API server for the CMU final project workflow.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.include_router(api_router)
    return app


app = create_app()


def run() -> None:
    """Run the API with uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
