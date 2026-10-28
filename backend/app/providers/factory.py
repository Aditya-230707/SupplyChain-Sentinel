"""
Provider factory — returns the correct provider based on LLM_PROVIDER env var.

Centralised here so app code never imports provider SDKs directly.
Nebius Token Factory is the sole application-supported cloud inference provider.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.providers.llm_base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance.

    nebius → NebiusTokenFactoryProvider (production inference with NVIDIA Nemotron)
    fake   → FakeLLMProvider (offline tests, zero network)
    """
    settings = get_settings()
    name = settings.llm_provider

    if name == "nebius":
        from app.providers.nebius_provider import make_nebius_provider_from_settings

        return make_nebius_provider_from_settings(settings=settings)

    if name == "fake":
        from app.providers.fake_provider import FakeLLMProvider

        return FakeLLMProvider()

    msg = f"Unknown LLM_PROVIDER: {name!r}. Supported providers: nebius (or fake for offline tests)"
    raise ValueError(msg)
