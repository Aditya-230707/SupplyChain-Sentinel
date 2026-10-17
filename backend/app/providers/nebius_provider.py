"""
Nebius Token Factory LLM provider — hackathon submission mode.

Uses the OpenAI-compatible Nebius API endpoint.
NEBIUS_API_KEY and NEBIUS_MODEL must be set and validated at invocation time.
The exact model ID must be verified from the Token Factory console.
This provider is NOT required to start the application or run unit tests.
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderQuotaError,
    ProviderUnavailableError,
    SchemaValidationError,
)
from app.providers.llm_base import ModelResult

log = structlog.get_logger(__name__)


class NebiusTokenFactoryProvider:
    """Nebius Token Factory provider — NVIDIA Nemotron model via OpenAI SDK.

    The base_url must be the Token Factory endpoint (default:
    https://api.tokenfactory.nebius.com/v1/).
    The model_id must be the exact string from /v1/models in your account.
    """

    provider_name: str = "nebius"

    def __init__(
        self,
        api_key: str,
        model_id: str,
        base_url: str = "https://api.tokenfactory.nebius.com/v1/",
        max_retries: int = 1,
    ) -> None:
        if not api_key:
            msg = "NEBIUS_API_KEY is required for NebiusTokenFactoryProvider"
            raise ProviderUnavailableError(msg)
        if not model_id:
            msg = (
                "NEBIUS_MODEL is required. "
                "Verify the exact model ID from your Token Factory console."
            )
            raise ProviderUnavailableError(msg)

        # Store key reference only — never log it
        self._api_key = api_key
        self.model_id = model_id
        self.base_url = base_url.rstrip("/") + "/"
        self._max_retries = max_retries
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore[import]
            except ImportError as exc:
                msg = "openai package is required for NebiusTokenFactoryProvider"
                raise ProviderUnavailableError(msg) from exc

            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self.base_url,
            )
        return self._client

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
        schema = response_model.model_json_schema()
        user_content = json.dumps(user_payload, ensure_ascii=False)
        retry_count = 0
        start = time.perf_counter()

        @retry(
            retry=retry_if_exception_type((ProviderError,)),
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential_jitter(multiplier=2, max=30),
            reraise=True,
        )
        async def _call() -> Any:
            nonlocal retry_count
            client = self._get_client()
            try:
                # Try structured output first; fall back to JSON mode if not supported
                try:
                    response = await client.chat.completions.create(
                        model=self.model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content},
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": response_model.__name__,
                                "schema": schema,
                                "strict": True,
                            },
                        },
                    )
                except Exception:
                    # Fall back to basic JSON mode if structured output not supported
                    response = await client.chat.completions.create(
                        model=self.model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": (
                                    f"{user_content}\n\n"
                                    f"Return ONLY valid JSON matching this schema: "
                                    f"{json.dumps(schema, ensure_ascii=False)}"
                                ),
                            },
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format={"type": "json_object"},
                    )
                return response
            except Exception as exc:
                err_str = str(exc)
                if self._api_key and self._api_key in err_str:
                    err_str = err_str.replace(self._api_key, "[REDACTED_API_KEY]")
                if "401" in err_str or "403" in err_str:
                    raise ProviderAuthError(
                        f"Nebius auth error (key redacted): {err_str[:100]}"
                    ) from exc
                if "429" in err_str:
                    raise ProviderQuotaError(f"Nebius quota exceeded: {err_str[:100]}") from exc
                retry_count += 1
                raise ProviderError(f"Nebius provider error: {err_str[:200]}") from exc

        response = await _call()
        elapsed_ms = (time.perf_counter() - start) * 1000
        raw_text = response.choices[0].message.content or ""
        usage = response.usage

        try:
            parsed = response_model.model_validate_json(raw_text)
        except Exception as exc:
            log.warning(
                "nebius_schema_validation_failed",
                task=task_name,
                model=self.model_id,
                error=str(exc)[:200],
            )
            raise SchemaValidationError(
                f"Nebius output did not match {response_model.__name__} schema"
            ) from exc

        log.info(
            "nebius_inference_ok",
            task=task_name,
            model=self.model_id,
            elapsed_ms=round(elapsed_ms, 1),
            retry_count=retry_count,
            tokens_in=getattr(usage, "prompt_tokens", None),
            tokens_out=getattr(usage, "completion_tokens", None),
        )

        return ModelResult(
            parsed_output=parsed,
            provider_name=self.provider_name,
            model_id=self.model_id,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
            tokens_prompt=getattr(usage, "prompt_tokens", None),
            tokens_completion=getattr(usage, "completion_tokens", None),
        )

    async def health_check(self) -> dict[str, object]:
        """Verify key works and model is accessible. Never expose the key."""
        import httpx

        result: dict[str, object] = {
            "configured": bool(self._api_key and self.model_id),
            "reachable": False,
            "model_available": None,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "error": None,
        }

        try:
            async with httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=10.0,
            ) as client:
                resp = await client.get(f"{self.base_url}models")
                if resp.status_code == 401:
                    result["error"] = "Authentication failed (key redacted)"
                    return result
                resp.raise_for_status()
                result["reachable"] = True
                models_data = resp.json()
                model_ids = [m.get("id", "") for m in models_data.get("data", [])]
                result["model_available"] = self.model_id in model_ids
                if not result["model_available"]:
                    result["error"] = (
                        f"Model '{self.model_id}' not in catalog. Available: {model_ids[:5]}"
                    )
        except Exception as exc:
            err_str = str(exc)
            if self._api_key and self._api_key in err_str:
                err_str = err_str.replace(self._api_key, "[REDACTED_API_KEY]")
            # Ensure key is not in error output
            result["error"] = "Provider unreachable: " + err_str[:150]

        return result


def make_nebius_provider_from_settings() -> NebiusTokenFactoryProvider:
    """Construct NebiusTokenFactoryProvider from application settings."""
    from app.core.config import get_settings

    s = get_settings()
    return NebiusTokenFactoryProvider(
        api_key=s.nebius_api_key,
        model_id=s.nebius_model,
        base_url=s.nebius_base_url,
        max_retries=s.max_model_retries,
    )
