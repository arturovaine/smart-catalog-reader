"""Application settings using Pydantic Settings for configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini API
    gemini_api_key: str = Field(..., description="Gemini API key")
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use for extraction",
    )

    # Processing tiers
    is_paid_tier: bool = Field(
        default=False,
        description="Whether using paid API tier (affects rate limiting)",
    )
    max_workers_free: int = Field(default=2, description="Max parallel workers for free tier")
    max_workers_paid: int = Field(default=10, description="Max parallel workers for paid tier")

    # DPI settings
    dpi_default: int = Field(default=200, description="Default DPI for PDF conversion")
    dpi_high: int = Field(default=300, description="High DPI for retry on failed extraction")

    # Fuzzy matching
    fuzzy_match_threshold: int = Field(
        default=75,
        ge=0,
        le=100,
        description="Minimum score for fuzzy category matching",
    )

    # Paths
    catalogs_dir: Path = Field(default=Path("data/catalogs"))
    output_dir: Path = Field(default=Path("data/output"))

    # Retry settings
    max_retries: int = Field(default=10, description="Maximum retry attempts for API calls")
    retry_base_delay: float = Field(default=1.0, description="Base delay for exponential backoff")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    @property
    def max_workers(self) -> int:
        """Get max workers based on tier."""
        return self.max_workers_paid if self.is_paid_tier else self.max_workers_free


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
