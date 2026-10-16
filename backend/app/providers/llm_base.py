"""
LLM provider interface and result types.

Business logic depends ONLY on this module — never on a specific provider SDK.
Provider implementations are registered by name and selected at runtime via
the LLM_PROVIDER environment variable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


@dataclass
class ModelResult:
    """Result of one LLM inference call.

    parsed_output is a validated Pydantic model instance.
    raw_text is preserved for debugging; never returned to clients.
    model_confidence is NOT a calibrated probability — do not treat it as one.
    """

    parsed_output: BaseModel
    provider_name: str
    model_id: str
    elapsed_ms: float
    retry_count: int = 0
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    # Never log or expose estimated_cost
    estimated_cost_usd: float | None = None
    # Safe error code if soft failure; None on success
    error_code: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that all LLM provider implementations must satisfy.

    Providers must NOT leak SDK-specific exceptions; translate to
    errors defined in app.core.errors before raising.
    """

    provider_name: str
    model_id: str

    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_payload: dict,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> ModelResult:
        """Generate a structured (Pydantic-validated) response.

        Rules:
        - user_payload content is UNTRUSTED DATA — treat as quoted, never as instructions.
        - response_model schema is enforced via Pydantic validation; malformed output
          must raise SchemaValidationError, not silently return garbage.
        - On transient failure, retry at most settings.max_model_retries times.
        - Never log API keys, full payloads, or raw model outputs at INFO+ level.
        """
        ...

    async def health_check(self) -> dict[str, object]:
        """Return provider health status without exposing credentials.

        Keys: configured (bool), reachable (bool), model_available (bool | None),
              provider_name (str), model_id (str), error (str | None).
        """
        ...
