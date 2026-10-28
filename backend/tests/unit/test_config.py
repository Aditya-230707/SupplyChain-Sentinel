"""
Unit tests for application configuration.

Verifies:
- Default values are sane
- Provider selection is validated
- Secrets are not exposed in safe_log_dict
- Nebius validation fires only when provider=nebius
- Generic invalid provider names are rejected
"""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError


def _make_settings(**kwargs: str) -> object:
    """Create Settings with explicit values, bypassing .env files."""
    # Clear the lru_cache so each test gets a fresh instance
    from app.core import config as config_module

    config_module.get_settings.cache_clear()

    # Set env vars for this test
    for key, value in kwargs.items():
        os.environ[key] = value

    from app.core.config import Settings

    return Settings(**{k.lower(): v for k, v in kwargs.items()})


def teardown_function() -> None:
    """Clear settings cache after each test."""
    from app.core import config as config_module

    config_module.get_settings.cache_clear()


def test_default_provider_is_fake_in_test_env() -> None:
    """LLM_PROVIDER defaults to fake; no network needed."""
    s = _make_settings(LLM_PROVIDER="fake", APP_ENV="test")
    assert s.llm_provider == "fake"  # type: ignore[attr-defined]


def test_nebius_provider_requires_api_key() -> None:
    """Setting LLM_PROVIDER=nebius without NEBIUS_API_KEY must raise."""
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="NEBIUS_API_KEY"):
        Settings(
            llm_provider="nebius",
            nebius_api_key="",
            nebius_model="some-model",
        )


def test_nebius_provider_requires_model_id() -> None:
    """Setting LLM_PROVIDER=nebius without NEBIUS_MODEL must raise."""
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="NEBIUS_MODEL"):
        Settings(
            llm_provider="nebius",
            nebius_api_key="valid-looking-key",
            nebius_model="",
        )


def test_nebius_provider_valid_when_both_set() -> None:
    """Both key and model set: no validation error."""
    from app.core.config import Settings

    s = Settings(
        llm_provider="nebius",
        nebius_api_key="sk-test-key",
        nebius_model="nvidia/nemotron-test",
    )
    assert s.llm_provider == "nebius"


def test_fake_provider_requires_no_keys() -> None:
    """fake provider: no API keys needed — startup must succeed."""
    from app.core.config import Settings

    s = Settings(llm_provider="fake")
    assert s.llm_provider == "fake"


def test_safe_log_dict_does_not_contain_secrets() -> None:
    """safe_log_dict must not include nebius_api_key or tavily_api_key."""
    from app.core.config import Settings

    s = Settings(
        llm_provider="nebius",
        nebius_api_key="super-secret-key",
        nebius_model="nvidia/test-model",
        tavily_api_key="tavily-secret",
    )
    safe = s.safe_log_dict()
    safe_str = str(safe)
    assert "super-secret-key" not in safe_str
    assert "tavily-secret" not in safe_str
    assert "nebius_api_key" not in safe_str
    assert "tavily_api_key" not in safe_str


def test_max_retries_default() -> None:
    from app.core.config import Settings

    s = Settings(llm_provider="fake")
    assert s.max_model_retries == 1


def test_invalid_provider_name_raises() -> None:
    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(llm_provider="anthropic")  # not in Literal


def test_production_accepts_nebius_with_required_settings() -> None:
    """APP_ENV=production accepts LLM_PROVIDER=nebius when key and model are set."""
    from app.core.config import Settings

    s = Settings(
        app_env="production",
        app_secret_key="a" * 32,
        llm_provider="nebius",
        nebius_api_key="sk-live-nebius-key",
        nebius_model="nvidia/Nemotron-3_5-Lightning",
    )
    assert s.app_env == "production"
    assert s.llm_provider == "nebius"


def test_production_rejects_fake_provider() -> None:
    """APP_ENV=production explicitly rejects LLM_PROVIDER=fake."""
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="LLM_PROVIDER must be 'nebius' in production"):
        Settings(
            app_env="production",
            app_secret_key="a" * 32,
            llm_provider="fake",
        )


def test_production_rejects_omitted_provider_defaulting_to_fake() -> None:
    """APP_ENV=production rejects omitted LLM_PROVIDER because it defaults to fake."""
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="LLM_PROVIDER must be 'nebius' in production"):
        Settings(
            app_env="production",
            app_secret_key="a" * 32,
        )


def test_development_and_test_environments_allow_fake() -> None:
    """Development and test environments can safely default to or use fake provider."""
    from app.core.config import Settings

    dev_settings = Settings(app_env="development", llm_provider="fake")
    assert dev_settings.llm_provider == "fake"

    test_settings = Settings(app_env="test", llm_provider="fake")
    assert test_settings.llm_provider == "fake"


def test_validation_errors_never_expose_api_key() -> None:
    """Validation errors must never expose secret API key values in the exception message."""
    from app.core.config import Settings

    secret_key = "super-secret-raw-token-12345"
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="production",
            app_secret_key="a" * 32,
            llm_provider="nebius",
            nebius_api_key=secret_key,
            nebius_model="",  # triggers NEBIUS_MODEL error
        )
    assert secret_key not in str(exc_info.value)
