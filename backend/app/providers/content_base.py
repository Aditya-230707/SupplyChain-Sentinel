"""
Content provider interface.

Tavily Extract (or any replacement) must implement ContentProvider.
SSRF protections apply to any direct URL fetching — prefer provider extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ContentResult:
    """Extracted content for one URL."""

    url: str
    # available | snippet_only | inaccessible | extraction_failed
    status: str
    text: str | None  # Extracted plain text; may be None if inaccessible
    title: str | None = None
    error_message: str | None = None


@runtime_checkable
class ContentProvider(Protocol):
    """Protocol for content extraction providers."""

    provider_name: str

    async def extract(self, urls: list[str]) -> list[ContentResult]:
        """Extract full text content for a list of URLs.

        - Never follow redirects to internal/private IP addresses.
        - Limit response size; honour provider terms.
        - Return ContentResult with status=inaccessible for paywall/auth failures.
        - Return ContentResult with status=extraction_failed for provider errors.
        """
        ...

    async def health_check(self) -> dict[str, object]:
        """Return provider health without exposing the API key."""
        ...
