"""
Tavily search and content providers.

Both implement the SearchProvider and ContentProvider protocols.
TAVILY_API_KEY is required only when actually invoked — not at startup.
"""

from __future__ import annotations

import structlog

from app.core.errors import ProviderAuthError, ProviderQuotaError
from app.providers.content_base import ContentResult
from app.providers.search_base import SearchResponse, SearchResult

log = structlog.get_logger(__name__)


class TavilySearchProvider:
    """Tavily Search API adapter.

    Docs: https://docs.tavily.com/documentation/api-reference/endpoint/search
    """

    provider_name: str = "tavily_search"

    def __init__(self, api_key: str, max_results: int = 8, search_depth: str = "advanced") -> None:
        if not api_key:
            msg = "TAVILY_API_KEY is required for TavilySearchProvider"
            raise ProviderAuthError(msg)
        self._api_key = api_key  # never logged
        self._max_results = max_results
        self._search_depth = search_depth

    async def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        search_depth: str | None = None,
    ) -> SearchResponse:
        import httpx

        n = max_results or self._max_results
        depth = search_depth or self._search_depth

        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": n,
            "search_depth": depth,
            "include_raw_content": False,
            "include_answer": False,  # Do not use synthesized answer as evidence
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post("https://api.tavily.com/search", json=payload)

                if resp.status_code == 401:
                    raise ProviderAuthError("Tavily auth failed (key redacted)")
                if resp.status_code == 429:
                    raise ProviderQuotaError("Tavily quota exceeded")
                resp.raise_for_status()

                data = resp.json()
                results = [
                    SearchResult(
                        url=r.get("url", ""),
                        title=r.get("title"),
                        snippet=r.get("content"),
                        domain=r.get("url", "").split("/")[2] if r.get("url") else None,
                        published_date=r.get("published_date"),
                        provider_score=r.get("score"),
                    )
                    for r in data.get("results", [])
                ]

                log.info(
                    "tavily_search_ok",
                    query_len=len(query),
                    result_count=len(results),
                    depth=depth,
                )

                return SearchResponse(
                    query=query,
                    results=results,
                    provider_name=self.provider_name,
                    status="ok" if results else "no_results",
                )

        except (ProviderAuthError, ProviderQuotaError):
            raise
        except Exception as exc:
            log.warning("tavily_search_error", error=str(exc)[:200])
            return SearchResponse(
                query=query,
                results=[],
                provider_name=self.provider_name,
                status="provider_error",
                error_message=str(exc)[:200],
            )

    async def health_check(self) -> dict[str, object]:
        return {
            "configured": bool(self._api_key),
            "provider_name": self.provider_name,
            "reachable": None,  # only check on actual smoke test
            "error": None,
        }


class TavilyContentProvider:
    """Tavily Extract API adapter for content retrieval.

    Docs: https://docs.tavily.com/documentation/api-reference/endpoint/extract
    """

    provider_name: str = "tavily_extract"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            msg = "TAVILY_API_KEY is required for TavilyContentProvider"
            raise ProviderAuthError(msg)
        self._api_key = api_key

    async def extract(self, urls: list[str]) -> list[ContentResult]:
        if not urls:
            return []

        import httpx

        payload = {
            "api_key": self._api_key,
            "urls": urls,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post("https://api.tavily.com/extract", json=payload)

                if resp.status_code == 401:
                    raise ProviderAuthError("Tavily Extract auth failed (key redacted)")
                if resp.status_code == 429:
                    raise ProviderQuotaError("Tavily Extract quota exceeded")
                resp.raise_for_status()

                data = resp.json()
                results_map: dict[str, ContentResult] = {}

                for r in data.get("results", []):
                    url = r.get("url", "")
                    raw_content = r.get("raw_content") or r.get("content")
                    results_map[url] = ContentResult(
                        url=url,
                        status="available" if raw_content else "extraction_failed",
                        text=raw_content,
                        title=r.get("title"),
                    )

                for failed in data.get("failed_results", []):
                    url = failed.get("url", "")
                    results_map[url] = ContentResult(
                        url=url,
                        status="inaccessible",
                        text=None,
                        error_message=failed.get("error"),
                    )

                # Return in same order as input
                return [
                    results_map.get(
                        url,
                        ContentResult(url=url, status="extraction_failed", text=None),
                    )
                    for url in urls
                ]

        except (ProviderAuthError, ProviderQuotaError):
            raise
        except Exception as exc:
            log.warning("tavily_extract_error", error=str(exc)[:200])
            return [
                ContentResult(
                    url=u, status="extraction_failed", text=None, error_message=str(exc)[:100]
                )
                for u in urls
            ]

    async def health_check(self) -> dict[str, object]:
        return {
            "configured": bool(self._api_key),
            "provider_name": self.provider_name,
            "reachable": None,
            "error": None,
        }


def make_tavily_providers_from_settings() -> tuple[TavilySearchProvider, TavilyContentProvider]:
    from app.core.config import get_settings

    s = get_settings()
    return (
        TavilySearchProvider(
            api_key=s.tavily_api_key,
            max_results=s.tavily_max_results,
            search_depth=s.tavily_search_depth,
        ),
        TavilyContentProvider(api_key=s.tavily_api_key),
    )
