"""
Live integration smoke test with local Ollama using qwen3.5:9b.

Only runs if Ollama is reachable and qwen3.5:9b is installed locally;
otherwise gracefully skips.
"""

from __future__ import annotations

import httpx
import pytest

from app.providers.ollama_provider import OllamaProvider
from app.schemas.claim import ClaimExtractionResponse


@pytest.mark.asyncio
async def test_live_ollama_qwen3_5_structured_output() -> None:
    # Check reachability first
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code != 200:
                pytest.skip("Ollama is not responding")
            data = resp.json()
            model_names = [m.get("name", "") for m in data.get("models", [])]
            if not any("qwen3.5:9b" in m for m in model_names):
                pytest.skip(f"qwen3.5:9b not in models list: {model_names}")
    except Exception:
        pytest.skip("Ollama daemon is unreachable on localhost:11434")

    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5:9b")
    health = await provider.health_check()
    assert health["reachable"] is True
    assert health["model_available"] is True

    # Real structured extraction inference
    source_text = (
        "Global Microchip Fab 2 in Dresden suffered an electrical substation fire on Monday. "
        "Production of semiconductor wafers is expected to be delayed for 30 days."
    )
    system_prompt = (
        "You are an information extraction component. "
        "Extract discrete factual claims from the source text. "
        "Quote exact substrings. Return only valid JSON matching the schema."
    )

    result = await provider.generate_structured(
        task_name="live_smoke_test",
        system_prompt=system_prompt,
        user_payload={"source_text": source_text},
        response_model=ClaimExtractionResponse,
        temperature=0.0,
    )

    assert isinstance(result.parsed_output, ClaimExtractionResponse)
    assert result.elapsed_ms > 0
    assert result.provider_name == "ollama"
    assert result.model_id == "qwen3.5:9b"
    # Verify claims were extracted
    assert len(result.parsed_output.claims) >= 1
    extracted_claim = result.parsed_output.claims[0]
    assert (
        "Global Microchip" in extracted_claim.subject_text or "Fab" in extracted_claim.subject_text
    )
    # Verify exact quote exists in source text
    assert extracted_claim.supporting_quote in source_text
