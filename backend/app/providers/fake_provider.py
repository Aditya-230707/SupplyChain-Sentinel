"""
FakeLLMProvider — deterministic provider for unit tests.

Returns pre-configured responses without any network calls.
Responses are injected at construction time, making tests reproducible.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from pydantic import BaseModel

from app.providers.llm_base import ModelResult


class FakeLLMProvider:
    """A deterministic test double for LLMProvider.

    Usage in tests::

        provider = FakeLLMProvider(responses=[
            MySchema(field="value"),
        ])
        result = await provider.generate_structured(
            task_name="test",
            system_prompt="...",
            user_payload={},
            response_model=MySchema,
        )
        assert isinstance(result.parsed_output, MySchema)
    """

    provider_name: str = "fake"
    model_id: str = "fake-model-v0"

    def __init__(
        self,
        responses: list[BaseModel] | None = None,
        *,
        always_raise: Exception | None = None,
        health_status: dict[str, object] | None = None,
    ) -> None:
        """
        Args:
            responses: Ordered list of Pydantic models to return.
                       Cycles back to the last one when exhausted.
            always_raise: If set, every call raises this exception.
            health_status: Override health check response.
        """
        self._queue: deque[BaseModel] = deque(responses or [])
        self._always_raise = always_raise
        self._health_status = health_status or {
            "configured": True,
            "reachable": True,
            "model_available": True,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "error": None,
        }
        self.call_count = 0
        self.last_call_args: dict[str, Any] = {}

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
        self.call_count += 1
        self.last_call_args = {
            "task_name": task_name,
            "response_model": response_model,
            "temperature": temperature,
        }

        if self._always_raise is not None:
            raise self._always_raise

        if self._queue:
            output = self._queue.popleft()
        elif response_model.__name__ == "ClaimExtractionResponse":
            from app.schemas.claim import ClaimExtractionResponse, ExtractedClaimItem

            src_text = str(user_payload.get("source_text", ""))
            supplier_ctx = user_payload.get("supplier_context", {})
            supplier_name = supplier_ctx.get("name", "Supplier")

            claims: list[ExtractedClaimItem] = []
            if src_text:
                for sentence in src_text.split(". "):
                    s_clean = sentence.strip()
                    if not s_clean:
                        continue
                    if any(
                        kw in s_clean.lower()
                        for kw in (
                            "fire",
                            "explosion",
                            "strike",
                            "halt",
                            "shutdown",
                            "damage",
                            "drill",
                            "disruption",
                            "flood",
                            "earthquake",
                        )
                    ):
                        quote = s_clean if s_clean.endswith(".") else f"{s_clean}."
                        claims.append(
                            ExtractedClaimItem(
                                subject_text=supplier_name,
                                event_type="operational_disruption",
                                object_text=quote,
                                claim_type="incident",
                                polarity="supports",
                                supporting_quote=quote,
                            )
                        )
                        break
            output = ClaimExtractionResponse(claims=claims)
        else:
            # Return a default empty-ish valid instance if no responses configured
            # This allows smoke tests that don't care about output content
            try:
                output = response_model.model_construct()
            except Exception as exc:
                msg = (
                    f"FakeLLMProvider has no queued response for {response_model.__name__} "
                    f"and could not construct a default. Provide responses= in the constructor."
                )
                raise RuntimeError(msg) from exc

        return ModelResult(
            parsed_output=output,
            provider_name=self.provider_name,
            model_id=self.model_id,
            elapsed_ms=0.0,
            retry_count=0,
        )

    async def health_check(self) -> dict[str, object]:
        return self._health_status
