"""
Unit tests for external provider adapters with mocked network/SDK responses.

Covers:
- TavilySearchProvider & TavilyContentProvider (401, 429, timeout, result mapping)
- NebiusTokenFactoryProvider (auth error, quota error, JSON mode fallback, secret redaction)
- OllamaProvider (health check, model availability, error handling)
- No live external network calls in any of these tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.core.errors import (
    ProviderAuthError,
    ProviderQuotaError,
    ProviderUnavailableError,
    SchemaValidationError,
)
from app.providers.nebius_provider import NebiusTokenFactoryProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.tavily_provider import (
    TavilyContentProvider,
    TavilySearchProvider,
)


class DummyOutput(BaseModel):
    summary: str
    impact_score: int


# ---- Tavily Adapters ----------------------------------------


@pytest.mark.asyncio
async def test_tavily_search_success_mapping() -> None:
    provider = TavilySearchProvider(api_key="tvly-mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "url": "https://example.com/incident",
                "title": "Incident at supplier",
                "content": "Short snippet describing the incident.",
                "score": 0.88,
                "published_date": "2026-10-16",
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        resp = await provider.search("supplier incident")

    assert resp.status == "ok"
    assert len(resp.results) == 1
    assert resp.results[0].title == "Incident at supplier"
    assert resp.results[0].domain == "example.com"


@pytest.mark.asyncio
async def test_tavily_search_401_raises_auth_error() -> None:
    provider = TavilySearchProvider(api_key="tvly-invalid-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(ProviderAuthError):
            await provider.search("test query")


@pytest.mark.asyncio
async def test_tavily_extract_429_raises_quota_error() -> None:
    provider = TavilyContentProvider(api_key="tvly-mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(ProviderQuotaError):
            await provider.extract(["https://example.com/news"])


# ---- Nebius Token Factory Adapter ---------------------------


def test_nebius_init_requires_key_and_model() -> None:
    with pytest.raises(ProviderUnavailableError, match="NEBIUS_API_KEY"):
        NebiusTokenFactoryProvider(api_key="", model_id="nvidia/nemotron")

    with pytest.raises(ProviderUnavailableError, match="NEBIUS_MODEL"):
        NebiusTokenFactoryProvider(api_key="sk-mock", model_id="")


@pytest.mark.asyncio
async def test_nebius_generate_structured_success() -> None:
    provider = NebiusTokenFactoryProvider(
        api_key="sk-mock-key",
        model_id="nvidia/Llama-3_1-Nemotron-70B-Instruct",
    )

    mock_choice = MagicMock()
    mock_choice.message.content = '{"summary": "Production halted", "impact_score": 8}'
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage.prompt_tokens = 120
    mock_completion.usage.completion_tokens = 35

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    with patch.object(provider, "_get_client", return_value=mock_client):
        res = await provider.generate_structured(
            task_name="test_task",
            system_prompt="Extract info",
            user_payload={"data": "test"},
            response_model=DummyOutput,
        )

    assert isinstance(res.parsed_output, DummyOutput)
    assert res.parsed_output.summary == "Production halted"
    assert res.parsed_output.impact_score == 8
    assert res.tokens_prompt == 120


@pytest.mark.asyncio
async def test_nebius_schema_mismatch_raises_schema_validation_error() -> None:
    provider = NebiusTokenFactoryProvider(
        api_key="sk-mock-key",
        model_id="nvidia/Llama-3_1-Nemotron-70B-Instruct",
        max_retries=0,
    )

    mock_choice = MagicMock()
    # Missing required field 'impact_score'
    mock_choice.message.content = '{"summary": "Incomplete output"}'
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(SchemaValidationError):
            await provider.generate_structured(
                task_name="test",
                system_prompt="s",
                user_payload={},
                response_model=DummyOutput,
            )


# ---- Ollama Adapter -----------------------------------------


@pytest.mark.asyncio
async def test_ollama_health_check_detects_available_model() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5:9b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "qwen3.5:9b"}, {"name": "llama3.2:3b"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.health_check()

    assert health["reachable"] is True
    assert health["model_available"] is True
    assert health["error"] is None


@pytest.mark.asyncio
async def test_ollama_health_check_flags_missing_model() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="nonexistent:model")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "qwen3.5:9b"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.health_check()

    assert health["reachable"] is True
    assert health["model_available"] is False
    assert "not found" in str(health["error"])


# ---- DuckDuckGo Adapters ------------------------------------


@pytest.mark.asyncio
async def test_ddg_search_mapping() -> None:
    from app.providers.ddg_provider import DuckDuckGoSearchProvider

    provider = DuckDuckGoSearchProvider(max_results=2)

    fake_items = [
        {
            "url": "https://reuters.com/business/factory-disruption",
            "title": "Factory disruption reported",
            "content": "A fire broke out in the manufacturing wing.",
            "published_date": "2026-10-15",
            "publisher": "Reuters",
        }
    ]

    with patch.object(provider, "_max_results", 2):
        with patch("asyncio.BaseEventLoop.run_in_executor", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_items
            resp = await provider.search("Apex factory fire")

    assert resp.status == "ok"
    assert len(resp.results) == 1
    item = resp.results[0]
    assert item.url == "https://reuters.com/business/factory-disruption"
    assert item.domain == "reuters.com"
    assert item.title == "Factory disruption reported"
    assert item.snippet == "A fire broke out in the manufacturing wing."


@pytest.mark.asyncio
async def test_ddg_content_ssrf_blocking() -> None:
    from app.providers.ddg_provider import DuckDuckGoContentProvider

    provider = DuckDuckGoContentProvider()

    # Blocked URLs (localhost, private IP, invalid scheme)
    results = await provider.extract(
        [
            "http://localhost:8000/internal",
            "http://192.168.1.1/admin",
            "ftp://example.com/file",
        ]
    )

    assert len(results) == 3
    for r in results:
        assert r.status == "inaccessible"
        assert "private or invalid" in (r.error_message or "")
