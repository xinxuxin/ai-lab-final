"""Project settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Generating Product Image from Customer Reviews"
    environment: str = "development"
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    stability_api_key: str = Field(default="", alias="STABILITY_API_KEY")
    discovery_max_products: int = Field(default=25, alias="DISCOVERY_MAX_PRODUCTS")
    discovery_timeout_seconds: int = Field(default=20, alias="DISCOVERY_TIMEOUT_SECONDS")
    discovery_request_delay_seconds: float = Field(
        default=1.0,
        alias="DISCOVERY_REQUEST_DELAY_SECONDS",
    )
    discovery_user_agent: str = Field(
        default="ai-lab-final-research-bot/0.1",
        alias="DISCOVERY_USER_AGENT",
    )
    scraping_request_delay_seconds: float = Field(
        default=1.5, alias="SCRAPING_REQUEST_DELAY_SECONDS"
    )
    scraping_max_retries: int = Field(default=3, alias="SCRAPING_MAX_RETRIES")
    frontend_api_base_url: str = Field(
        default="http://localhost:8000",
        alias="FRONTEND_API_BASE_URL",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
