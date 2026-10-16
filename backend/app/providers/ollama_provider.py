"""
Ollama LLM provider — local development only.

Uses the OpenAI-compatible endpoint exposed by Ollama at /v1.
Structured output is requested via JSON-schema mode where supported.
Credentials: only requires OLLAMA_BASE_URL (no API key for local Ollama).
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
    ProviderError,
    ProviderUnavailableError,
    SchemaValidationError,
)
from app.providers.llm_base import ModelResult

log = structlog.get_logger(__name__)


class OllamaProvider:
    """Ollama LLM provider using the OpenAI-compatible /v1 endpoint.

    Raises app.core.errors exceptions; never leaks openai SDK exceptions.
    """

    provider_name: str = "ollama"

    def __init__(self, base_url: str, model: str, max_retries: int = 1) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_id = model
        self._max_retries = max_retries
        self._client: Any = None  # lazy-init to avoid import errors at test time

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore[import]
            except ImportError as exc:
                msg = "openai package is required for OllamaProvider"
                raise ProviderUnavailableError(msg) from exc

            self._client = AsyncOpenAI(
                base_url=f"{self.base_url}/v1",
                api_key="ollama",  # Ollama ignores this; required by SDK
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

        start = time.perf_counter()
        retry_count = 0

        @retry(
            retry=retry_if_exception_type((ProviderError,)),
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential_jitter(multiplier=1, max=10),
            reraise=True,
        )
        async def _call() -> Any:
            nonlocal retry_count
            client = self._get_client()
            try:
                response = await client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    # Ollama JSON-schema structured output
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_model.__name__,
                            "schema": schema,
                            "strict": True,
                        },
                    },
                )
                return response
            except Exception as exc:
                err_str = str(exc)
                # Classify error — do not retry auth/quota errors
                if "401" in err_str or "403" in err_str:
                    from app.core.errors import ProviderAuthError

                    raise ProviderAuthError(f"Ollama auth error: {err_str}") from exc
                if "429" in err_str:
                    from app.core.errors import ProviderQuotaError

                    raise ProviderQuotaError(f"Ollama quota: {err_str}") from exc
                retry_count += 1
                raise ProviderError(f"Ollama error: {err_str}") from exc

        response = await _call()
        elapsed_ms = (time.perf_counter() - start) * 1000

        raw_text = response.choices[0].message.content or ""
        usage = response.usage

        # Parse and validate against schema
        try:
            parsed = response_model.model_validate_json(raw_text)
        except Exception as exc:
            log.warning(
                "ollama_schema_validation_failed",
                task=task_name,
                model=self.model_id,
                error=str(exc)[:200],
            )
            raise SchemaValidationError(
                f"Ollama output did not match {response_model.__name__} schema"
            ) from exc

        log.info(
            "ollama_inference_ok",
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
        """Check if Ollama is reachable and the configured model is available."""
        import httpx

        result: dict[str, object] = {
            "configured": True,
            "reachable": False,
            "model_available": None,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "error": None,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                result["reachable"] = True
                models = [m.get("name", "") for m in data.get("models", [])]
                result["model_available"] = any(
                    self.model_id == m or self.model_id in m for m in models
                )
                if not result["model_available"]:
                    result["error"] = (
                        f"Model '{self.model_id}' not found. "
                        f"Available: {models[:5]}. Run: ollama pull {self.model_id}"
                    )
        except Exception as exc:
            result["error"] = f"Ollama unreachable at {self.base_url}: {exc!s}"

        return result


def make_ollama_provider_from_settings() -> OllamaProvider:
    """Construct OllamaProvider from application settings."""
    from app.core.config import get_settings

    s = get_settings()
    return OllamaProvider(
        base_url=s.ollama_base_url,
        model=s.ollama_model,
        max_retries=s.max_model_retries,
    )
