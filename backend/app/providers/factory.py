"""
Provider factory — returns the correct provider based on LLM_PROVIDER env var.

Centralised here so app code never imports provider SDKs directly.
Changing LLM_PROVIDER requires only an env-var change, no code edits.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.providers.llm_base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance.

    fake  → FakeLLMProvider (tests, no network)
    ollama → OllamaProvider (local dev)
    nebius → NebiusTokenFactoryProvider (submission)
    """
    settings = get_settings()
    name = settings.llm_provider

    if name == "fake":
        from app.providers.fake_provider import FakeLLMProvider

        return FakeLLMProvider()

    if name == "ollama":
        from app.providers.ollama_provider import make_ollama_provider_from_settings

        return make_ollama_provider_from_settings()

    if name == "nebius":
        from app.providers.nebius_provider import make_nebius_provider_from_settings

        return make_nebius_provider_from_settings()

    msg = f"Unknown LLM_PROVIDER: {name!r}. Choose: fake | ollama | nebius"
    raise ValueError(msg)
