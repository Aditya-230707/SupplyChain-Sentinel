"""
Typed error classes and FastAPI exception handlers.

Every error has an explicit code string (never raw Python exception class names
exposed to callers) and a safe message. Stack traces are never sent to clients.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

log = structlog.get_logger(__name__)


# ---- Error response schema -----------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    field: str | None = None  # for validation errors


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---- Typed application exceptions -----------------------------------


class SentinelError(Exception):
    """Base class for all application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(SentinelError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class ValidationError(SentinelError):
    status_code = HTTP_422
    code = "validation_error"


class ConflictError(SentinelError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ProviderError(SentinelError):
    """Raised when an external provider (LLM, search) fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "provider_error"


class ProviderUnavailableError(ProviderError):
    code = "provider_unavailable"


class ProviderAuthError(ProviderError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "provider_auth_error"


class ProviderQuotaError(ProviderError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "provider_quota_exceeded"


class SchemaValidationError(SentinelError):
    """LLM output did not pass Pydantic/schema validation."""

    status_code = HTTP_422
    code = "model_output_invalid"


class QuoteMismatchError(SentinelError):
    """Extracted quote does not match stored source text."""

    status_code = HTTP_422
    code = "quote_mismatch"


class InvestigationNotReadyError(SentinelError):
    status_code = status.HTTP_409_CONFLICT
    code = "investigation_not_ready"


class RateLimitError(SentinelError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"


# ---- Exception handler registration ---------------------------------


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(SentinelError)
    async def sentinel_error_handler(request: Request, exc: SentinelError) -> JSONResponse:
        rid = _request_id(request)
        log.warning(
            "sentinel_error",
            code=exc.code,
            message=exc.message,
            request_id=rid,
            # do not log exc.details — may contain sensitive path info
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code=exc.code, message=exc.message, request_id=rid)
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = _request_id(request)
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first.get("loc", []))
        log.info("request_validation_error", field=field, request_id=rid)
        return JSONResponse(
            status_code=HTTP_422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="request_invalid",
                    message=first.get("msg", "Invalid request"),
                    request_id=rid,
                    field=field or None,
                )
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = _request_id(request)
        log.exception("unhandled_error", request_id=rid, exc_type=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="internal_error",
                    message="An unexpected error occurred. Please try again.",
                    request_id=rid,
                )
            ).model_dump(),
        )
