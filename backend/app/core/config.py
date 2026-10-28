"""
Application configuration via pydantic-settings.

All settings read from environment variables or .env file.
Secrets (APP_SECRET_KEY, NEBIUS_API_KEY, TAVILY_API_KEY) are never given
unsafe defaults in production.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application -----------------------------------------
    app_name: str = "SupplyChain Sentinel"
    app_env: Literal["development", "test", "production"] = "development"
    app_secret_key: str = "change-me-to-a-random-32-char-string"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    request_id_header: str = "X-Request-ID"

    # ---- Database --------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"

    # ---- LLM Provider ----------------------------------------
    llm_provider: Literal["nebius", "fake"] = "fake"

    # Nebius Token Factory (optional until actually used)
    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    nebius_model: str = ""

    # ---- Search / Content ------------------------------------
    tavily_api_key: str = ""
    tavily_max_results: int = 8
    tavily_search_depth: Literal["basic", "advanced"] = "advanced"

    # ---- Pipeline caps ---------------------------------------
    max_searches_per_run: int = 6
    max_results_per_search: int = 8
    max_content_chars: int = 12_000
    max_model_retries: int = 1
    max_concurrent_investigations: int = 3
    investigation_timeout_seconds: int = 300

    # ---- CORS ------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ---- Dev gates -------------------------------------------
    allow_live_smoke_tests: bool = False

    # ---- Validators ------------------------------------------
    @field_validator("app_secret_key")
    @classmethod
    def secret_key_not_default_in_production(cls, v: str, info: object) -> str:
        # info is a FieldValidationInfo; access data dict if available
        data = getattr(info, "data", {})
        if data.get("app_env") == "production" and v == "change-me-to-a-random-32-char-string":
            msg = "APP_SECRET_KEY must be changed from the default in production"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def production_requires_nebius_provider(self) -> Settings:
        if self.app_env == "production" and self.llm_provider != "nebius":
            msg = (
                f"LLM_PROVIDER must be 'nebius' in production; got {self.llm_provider!r}. "
                "FakeLLMProvider is strictly restricted to development and offline tests."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def nebius_model_required_when_provider_is_nebius(self) -> Settings:
        if self.llm_provider == "nebius":
            if not self.nebius_api_key:
                msg = "NEBIUS_API_KEY is required when LLM_PROVIDER=nebius"
                raise ValueError(msg)
            if not self.nebius_model:
                msg = (
                    "NEBIUS_MODEL is required when LLM_PROVIDER=nebius. "
                    "Verify the exact model ID from your Token Factory console."
                )
                raise ValueError(msg)
        return self

    def safe_log_dict(self) -> dict[str, object]:
        """Return a settings dict safe for structured logging (no secrets)."""
        return {
            "app_env": self.app_env,
            "llm_provider": self.llm_provider,
            "nebius_model": self.nebius_model if self.llm_provider == "nebius" else None,
            "database_url_scheme": self.database_url.split("://")[0],
            "tavily_configured": bool(self.tavily_api_key),
            "nebius_configured": bool(self.nebius_api_key),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
