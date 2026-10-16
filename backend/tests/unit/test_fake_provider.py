"""
Unit tests for FakeLLMProvider.

Verifies:
- Deterministic queued responses are returned in order
- Call count is tracked
- always_raise causes every call to raise
- Health check returns configured values
- No network access in any of these tests
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.providers.fake_provider import FakeLLMProvider

# ---- Test schemas (local to this module) --------------------


class SimpleOutput(BaseModel):
    label: str
    score: float = 0.0


class EmptyOutput(BaseModel):
    items: list[str] = []


# ---- Tests --------------------------------------------------


@pytest.mark.asyncio
async def test_fake_provider_returns_queued_response() -> None:
    expected = SimpleOutput(label="test_label", score=0.9)
    provider = FakeLLMProvider(responses=[expected])

    result = await provider.generate_structured(
        task_name="test",
        system_prompt="You are a test.",
        user_payload={"data": "content"},
        response_model=SimpleOutput,
    )

    assert isinstance(result.parsed_output, SimpleOutput)
    assert result.parsed_output.label == "test_label"
    assert result.parsed_output.score == 0.9


@pytest.mark.asyncio
async def test_fake_provider_returns_responses_in_order() -> None:
    r1 = SimpleOutput(label="first")
    r2 = SimpleOutput(label="second")
    provider = FakeLLMProvider(responses=[r1, r2])

    out1 = await provider.generate_structured(
        task_name="t1",
        system_prompt="s",
        user_payload={},
        response_model=SimpleOutput,
    )
    out2 = await provider.generate_structured(
        task_name="t2",
        system_prompt="s",
        user_payload={},
        response_model=SimpleOutput,
    )

    assert out1.parsed_output.label == "first"
    assert out2.parsed_output.label == "second"


@pytest.mark.asyncio
async def test_fake_provider_tracks_call_count() -> None:
    provider = FakeLLMProvider(responses=[SimpleOutput(label="x")])
    assert provider.call_count == 0

    await provider.generate_structured(
        task_name="t",
        system_prompt="s",
        user_payload={},
        response_model=SimpleOutput,
    )
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_fake_provider_always_raise() -> None:
    """When always_raise is set, every call raises that exception."""
    error = RuntimeError("simulated provider failure")
    provider = FakeLLMProvider(always_raise=error)

    with pytest.raises(RuntimeError, match="simulated provider failure"):
        await provider.generate_structured(
            task_name="t",
            system_prompt="s",
            user_payload={},
            response_model=SimpleOutput,
        )


@pytest.mark.asyncio
async def test_fake_provider_health_check_defaults() -> None:
    provider = FakeLLMProvider()
    health = await provider.health_check()

    assert health["configured"] is True
    assert health["reachable"] is True
    assert health["model_available"] is True
    assert health["error"] is None
    assert "api_key" not in str(health)


@pytest.mark.asyncio
async def test_fake_provider_custom_health_status() -> None:
    provider = FakeLLMProvider(
        health_status={
            "configured": True,
            "reachable": False,
            "model_available": None,
            "provider_name": "fake",
            "model_id": "fake-model-v0",
            "error": "connection refused",
        }
    )
    health = await provider.health_check()
    assert health["reachable"] is False
    assert health["error"] == "connection refused"


@pytest.mark.asyncio
async def test_fake_provider_records_last_call_args() -> None:
    provider = FakeLLMProvider(responses=[SimpleOutput(label="x")])

    await provider.generate_structured(
        task_name="my_task",
        system_prompt="s",
        user_payload={"key": "val"},
        response_model=SimpleOutput,
        temperature=0.1,
    )

    assert provider.last_call_args["task_name"] == "my_task"
    assert provider.last_call_args["temperature"] == 0.1
    assert provider.last_call_args["response_model"] is SimpleOutput


@pytest.mark.asyncio
async def test_fake_provider_provider_name_and_model() -> None:
    provider = FakeLLMProvider()
    assert provider.provider_name == "fake"
    assert provider.model_id == "fake-model-v0"
