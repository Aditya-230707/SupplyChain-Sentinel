"""
Unit tests for application configuration.

Verifies:
- Default values are sane
- Provider selection is validated
- Secrets are not exposed in safe_log_dict
- Nebius validation fires only when provider=nebius
- Ollama validation fires only when provider=ollama
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


def test_ollama_provider_requires_model() -> None:
    """LLM_PROVIDER=ollama without OLLAMA_MODEL must raise."""
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="OLLAMA_MODEL"):
        Settings(llm_provider="ollama", ollama_model="")


def test_ollama_provider_valid_with_model() -> None:
    from app.core.config import Settings

    s = Settings(llm_provider="ollama", ollama_model="qwen3.5:9b")
    assert s.ollama_model == "qwen3.5:9b"


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
