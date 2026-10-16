"""
Search provider interface.

Tavily (and any replacement) must implement SearchProvider.
Business logic never imports Tavily SDK directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SearchResult:
    """One item from a search provider response."""

    url: str
    title: str | None
    snippet: str | None  # Provider-supplied snippet; not full content
    domain: str | None
    published_date: str | None  # ISO string or None; raw from provider
    provider_score: float | None  # Provider relevance score; not a truth signal
    provider_result_id: str | None = None
    raw_content: str | None = None  # Full content if provider returns it


@dataclass
class SearchResponse:
    """Result of one search query."""

    query: str
    results: list[SearchResult]
    provider_name: str
    # no_results | partial | ok | quota_exceeded | auth_error | provider_error
    status: str
    error_message: str | None = None


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for search providers (Tavily or replacement)."""

    provider_name: str

    async def search(
        self,
        query: str,
        *,
        max_results: int = 8,
        search_depth: str = "advanced",
    ) -> SearchResponse:
        """Execute a search and return structured results.

        - Do not follow synthesized answers as evidence.
        - Handle 401, 429, quota errors, timeout, and partial results explicitly.
        - Do not retry quota/payment errors.
        """
        ...

    async def health_check(self) -> dict[str, object]:
        """Return provider health without exposing the API key."""
        ...
