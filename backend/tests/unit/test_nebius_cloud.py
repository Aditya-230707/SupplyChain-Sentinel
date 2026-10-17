"""Tests for Nebius Token Factory Cloud adapter — NVIDIA Nemotron integration.

Includes comprehensive mocked tests for:
- 401 Unauthorized / auth failure with API key redaction verification
- 429 Quota / Rate limit error handling
- Timeout / connection failure handling
- Structured output fallback from json_schema to json_object
- Health check against /v1/models catalog
- Optional live smoke test (guarded by ALLOW_LIVE_SMOKE_TESTS and NEBIUS_API_KEY)
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.core.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderQuotaError,
)
from app.providers.nebius_provider import NebiusTokenFactoryProvider


class SimpleIncidentPayload(BaseModel):
    incident_type: str
    severity_level: str
    estimated_days: int


@pytest.mark.asyncio
async def test_nebius_401_auth_error_with_key_redaction() -> None:
    """Verify that a 401 response raises ProviderAuthError and never leaks the API key."""
    secret_key = "nebius-super-secret-production-key-998877"
    provider = NebiusTokenFactoryProvider(
        api_key=secret_key,
        model_id="nvidia/Nemotron-3_5-Lightning",
        max_retries=0,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception(f"401 Unauthorized: Invalid API key {secret_key}")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(ProviderAuthError) as exc_info:
            await provider.generate_structured(
                task_name="test_auth_redaction",
                system_prompt="system",
                user_payload={"test": "payload"},
                response_model=SimpleIncidentPayload,
            )

    err_msg = str(exc_info.value)
    assert "Nebius auth error" in err_msg
    # Crucial security assertion: the raw secret key must NEVER appear in the exception message
    assert secret_key not in err_msg


@pytest.mark.asyncio
async def test_nebius_429_quota_limit_handling() -> None:
    """Verify that 429 rate limit / quota exhaustion raises ProviderQuotaError."""
    provider = NebiusTokenFactoryProvider(
        api_key="sk-test-mock",
        model_id="nvidia/Nemotron-3_5-Lightning",
        max_retries=0,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("429 Too Many Requests: TPM quota exceeded for model")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(ProviderQuotaError) as exc_info:
            await provider.generate_structured(
                task_name="test_quota",
                system_prompt="system",
                user_payload={"test": "payload"},
                response_model=SimpleIncidentPayload,
            )

    assert "Nebius quota exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_nebius_timeout_connection_error() -> None:
    """Verify that network timeouts / connection drops raise ProviderError."""
    provider = NebiusTokenFactoryProvider(
        api_key="sk-test-mock",
        model_id="nvidia/Nemotron-3_5-Lightning",
        max_retries=0,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Connection timed out after 30000ms")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_structured(
                task_name="test_timeout",
                system_prompt="system",
                user_payload={"test": "payload"},
                response_model=SimpleIncidentPayload,
            )

    assert "Nebius provider error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_nebius_structured_fallback_to_json_object() -> None:
    """Verify fallback from strict json_schema to standard json_object mode."""
    provider = NebiusTokenFactoryProvider(
        api_key="sk-test-mock",
        model_id="nvidia/Nemotron-3_5-Lightning",
        max_retries=0,
    )

    mock_choice = MagicMock()
    mock_choice.message.content = (
        '{"incident_type": "flood", "severity_level": "high", "estimated_days": 14}'
    )
    success_completion = MagicMock()
    success_completion.choices = [mock_choice]
    success_completion.usage.prompt_tokens = 95
    success_completion.usage.completion_tokens = 22

    # First attempt (json_schema) fails; second attempt (json_object fallback) succeeds
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("json_schema format not supported by this endpoint"),
            success_completion,
        ]
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        result = await provider.generate_structured(
            task_name="test_fallback",
            system_prompt="Extract incident",
            user_payload={"source": "flood reported at factory"},
            response_model=SimpleIncidentPayload,
        )

    assert isinstance(result.parsed_output, SimpleIncidentPayload)
    assert result.parsed_output.incident_type == "flood"
    assert result.parsed_output.estimated_days == 14
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_nebius_health_check_success_and_catalog() -> None:
    """Verify health check queries /v1/models and detects model availability."""
    secret_key = "nebius-key-health-test"
    target_model = "nvidia/Nemotron-3_5-Lightning"
    provider = NebiusTokenFactoryProvider(
        api_key=secret_key,
        model_id=target_model,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "meta-llama/Llama-3-70B"},
            {"id": target_model},
            {"id": "nvidia/nemotron-3-super-120b-a12b"},
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.health_check()

    assert health["configured"] is True
    assert health["reachable"] is True
    assert health["model_available"] is True
    assert health["error"] is None


@pytest.mark.asyncio
async def test_nebius_health_check_401_redaction() -> None:
    """Verify health check handles 401 without exposing secret credentials."""
    secret_key = "nebius-super-secret-key-111"
    provider = NebiusTokenFactoryProvider(
        api_key=secret_key,
        model_id="nvidia/Nemotron-3_5-Lightning",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.health_check()

    assert health["configured"] is True
    assert health["reachable"] is False
    assert health["model_available"] is None
    assert "Authentication failed (key redacted)" in str(health["error"])
    assert secret_key not in str(health["error"])


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("ALLOW_LIVE_SMOKE_TESTS") != "true" or not os.getenv("NEBIUS_API_KEY"),
    reason=(
        "Live smoke test disabled. Set ALLOW_LIVE_SMOKE_TESTS=true and NEBIUS_API_KEY "
        "to run against Nebius Token Factory."
    ),
)
async def test_nebius_live_smoke_test() -> None:  # pragma: no cover
    """Live smoke test against real Nebius Token Factory endpoint when explicitly enabled."""
    from app.core.config import get_settings

    settings = get_settings()
    provider = NebiusTokenFactoryProvider(
        api_key=settings.nebius_api_key,
        model_id=settings.nebius_model or "nvidia/Nemotron-3_5-Lightning",
        base_url=settings.nebius_base_url,
    )

    # 1. Check health
    health = await provider.health_check()
    assert health["reachable"] is True, f"Nebius unreachable: {health.get('error')}"

    # 2. Check structured inference
    res = await provider.generate_structured(
        task_name="live_smoke_test",
        system_prompt="You are a structured extraction engine. Return valid JSON only.",
        user_payload={"report": "Fire at manufacturing line halts production for 10 days"},
        response_model=SimpleIncidentPayload,
    )
    assert isinstance(res.parsed_output, SimpleIncidentPayload)
    assert res.parsed_output.estimated_days > 0
