"""
Fixture-based Search and Content provider for offline testing and reproducible demos.

Implements SearchProvider and ContentProvider without making external network calls.
"""

from __future__ import annotations

from app.providers.content_base import ContentResult
from app.providers.search_base import SearchResponse, SearchResult


class FixtureSearchProvider:
    """Deterministic fixture search provider."""

    provider_name: str = "fixture_search"

    def __init__(
        self,
        canned_results: list[SearchResult] | None = None,
        *,
        always_raise: Exception | None = None,
        status: str = "ok",
    ) -> None:
        self._canned_results = canned_results or []
        self._always_raise = always_raise
        self._status = status
        self.last_query: str | None = None
        self.call_count = 0

    async def search(
        self,
        query: str,
        *,
        max_results: int = 8,
        search_depth: str = "advanced",
    ) -> SearchResponse:
        self.call_count += 1
        self.last_query = query

        if self._always_raise:
            raise self._always_raise

        results = self._canned_results[:max_results]
        return SearchResponse(
            query=query,
            results=results,
            provider_name=self.provider_name,
            status=self._status,
        )

    async def health_check(self) -> dict[str, object]:
        return {
            "configured": True,
            "provider_name": self.provider_name,
            "reachable": True,
            "error": None,
        }


class FixtureContentProvider:
    """Deterministic fixture content provider."""

    provider_name: str = "fixture_extract"

    def __init__(
        self,
        url_content_map: dict[str, str] | None = None,
        *,
        always_raise: Exception | None = None,
    ) -> None:
        self._url_content_map = url_content_map or {}
        self._always_raise = always_raise
        self.call_count = 0

    async def extract(self, urls: list[str]) -> list[ContentResult]:
        self.call_count += 1

        if self._always_raise:
            raise self._always_raise

        results: list[ContentResult] = []
        for url in urls:
            if url in self._url_content_map:
                content = self._url_content_map[url]
                results.append(
                    ContentResult(
                        url=url,
                        status="available" if content else "inaccessible",
                        text=content if content else None,
                    )
                )
            else:
                results.append(
                    ContentResult(
                        url=url,
                        status="inaccessible",
                        text=None,
                        error_message="URL not found in fixture map",
                    )
                )
        return results

    async def health_check(self) -> dict[str, object]:
        return {
            "configured": True,
            "provider_name": self.provider_name,
            "reachable": True,
            "error": None,
        }
