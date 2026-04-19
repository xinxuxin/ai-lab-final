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
    scraping_timeout_seconds: int = Field(default=30, alias="SCRAPING_TIMEOUT_SECONDS")
    scraping_user_agent: str = Field(
        default="ai-lab-final-research-bot/0.1",
        alias="SCRAPING_USER_AGENT",
    )
    scraping_min_review_chars: int = Field(default=25, alias="SCRAPING_MIN_REVIEW_CHARS")
    q1_min_review_count: int = Field(default=5, alias="Q1_MIN_REVIEW_COUNT")
    corpus_min_review_chars: int = Field(default=25, alias="CORPUS_MIN_REVIEW_CHARS")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    llm_analysis_model: str = Field(default="gpt-4o-mini", alias="LLM_ANALYSIS_MODEL")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")
    review_chunk_max_chars: int = Field(default=1200, alias="REVIEW_CHUNK_MAX_CHARS")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    target_api_key: str = Field(
        default="9f36aeafbe60771e321a7cc95a78140772ab3e96",
        alias="TARGET_API_KEY",
    )
    target_pricing_store_id: str = Field(default="2077", alias="TARGET_PRICING_STORE_ID")
    frontend_api_base_url: str = Field(
        default="http://localhost:8000",
        alias="FRONTEND_API_BASE_URL",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
