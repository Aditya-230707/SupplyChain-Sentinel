"""
DuckDuckGo search and live content retrieval provider.

Implements SearchProvider and ContentProvider without requiring API keys.
Handles rate limits, empty results, timeouts, and page blocking explicitly.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

from app.core.errors import ProviderError
from app.providers.content_base import ContentResult
from app.providers.search_base import SearchResponse, SearchResult

log = structlog.get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 SentinelIntelligence/1.0"
)


class DuckDuckGoSearchProvider:
    """Live public web search via DuckDuckGo news and text search."""

    provider_name: str = "duckduckgo_search"

    def __init__(self, max_results: int = 6) -> None:
        self._max_results = max_results

    async def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        search_depth: str | None = None,
    ) -> SearchResponse:
        n = max_results or self._max_results
        loop = asyncio.get_running_loop()

        def _do_ddg_search() -> list[dict[str, Any]]:
            from ddgs import DDGS

            ddg = DDGS()
            raw_items: list[dict[str, Any]] = []

            # First priority: news search (has publication dates and news publishers)
            try:
                news_results = list(ddg.news(query, max_results=n))
                for item in news_results:
                    raw_items.append(
                        {
                            "url": item.get("url") or item.get("href", ""),
                            "title": item.get("title", ""),
                            "content": item.get("body") or item.get("snippet", ""),
                            "published_date": item.get("date"),
                            "publisher": item.get("source"),
                        }
                    )
            except Exception as exc:
                log.warning("ddg_news_search_failed", query=query, error=str(exc))

            # If news yielded fewer than requested, augment with web text search
            if len(raw_items) < n:
                try:
                    text_results = list(ddg.text(query, max_results=n - len(raw_items)))
                    for item in text_results:
                        url = item.get("href") or item.get("url", "")
                        if not any(r["url"] == url for r in raw_items):
                            raw_items.append(
                                {
                                    "url": url,
                                    "title": item.get("title", ""),
                                    "content": item.get("body") or item.get("snippet", ""),
                                    "published_date": None,
                                    "publisher": None,
                                }
                            )
                except Exception as exc:
                    log.warning("ddg_text_search_failed", query=query, error=str(exc))

            return raw_items[:n]

        try:
            items = await loop.run_in_executor(None, _do_ddg_search)
        except Exception as exc:
            log.error("duckduckgo_search_failed", query=query, error=str(exc))
            raise ProviderError(f"DuckDuckGo search failed: {exc!s}") from exc

        results: list[SearchResult] = []
        for it in items:
            url = it.get("url", "")
            if not url or not url.startswith("http"):
                continue

            results.append(
                SearchResult(
                    url=url,
                    title=it.get("title", ""),
                    content=it.get("content", ""),
                    score=0.85,
                    published_date=it.get("published_date"),
                    raw_content=None,
                )
            )

        log.info("duckduckgo_search_completed", query=query, count=len(results))
        return SearchResponse(
            query=query,
            results=results,
            provider_name=self.provider_name,
        )

    async def health_check(self) -> dict[str, object]:
        """Check if DuckDuckGo search is functional."""
        loop = asyncio.get_running_loop()

        def _ping() -> bool:
            from ddgs import DDGS

            ddg = DDGS()
            r = list(ddg.text("supply chain", max_results=1))
            return len(r) >= 0  # no exception means reachable

        try:
            reachable = await loop.run_in_executor(None, _ping)
            return {
                "configured": True,
                "reachable": reachable,
                "provider_name": self.provider_name,
                "error": None,
            }
        except Exception as exc:
            return {
                "configured": True,
                "reachable": False,
                "provider_name": self.provider_name,
                "error": f"DuckDuckGo unreachable: {exc!s}",
            }


class DuckDuckGoContentProvider:
    """Direct HTTP content extractor for discovered public pages with clean fallback."""

    provider_name: str = "duckduckgo_content"

    def __init__(self, timeout: float = 12.0) -> None:
        self._timeout = timeout

    async def fetch_content(self, url: str) -> ContentResult:
        """Fetch and extract visible text from public URL."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        retrieved_at = datetime.now(UTC)

        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)

                if resp.status_code >= 400:
                    log.warning(
                        "public_page_blocked_or_missing",
                        url=url,
                        status_code=resp.status_code,
                    )
                    return ContentResult(
                        url=url,
                        content=f"[Access Restricted: HTTP {resp.status_code}]",
                        title=None,
                        published_date=None,
                        retrieved_at=retrieved_at,
                        content_type="text/plain",
                        provider_name=self.provider_name,
                        raw_bytes_length=0,
                    )

                html_text = resp.text
                soup = BeautifulSoup(html_text, "html.parser")

                # Remove non-content tags
                for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "svg"]):
                    tag.decompose()

                title = soup.title.string.strip() if soup.title and soup.title.string else None

                # Extract article body or main content
                article = soup.find("article") or soup.find("main") or soup.body
                if article:
                    clean_text = " ".join(article.stripped_strings)
                else:
                    clean_text = " ".join(soup.stripped_strings)

                # Cap content length
                clean_text = clean_text[:15_000]

                return ContentResult(
                    url=url,
                    content=clean_text or "[Empty Page Content]",
                    title=title,
                    published_date=None,
                    retrieved_at=retrieved_at,
                    content_type="text/html",
                    provider_name=self.provider_name,
                    raw_bytes_length=len(html_text.encode("utf-8")),
                )

        except Exception as exc:
            log.warning("public_page_fetch_failed", url=url, error=str(exc))
            return ContentResult(
                url=url,
                content=f"[Retrieval Failure: {exc!s}]",
                title=None,
                published_date=None,
                retrieved_at=retrieved_at,
                content_type="text/plain",
                provider_name=self.provider_name,
                raw_bytes_length=0,
            )


def make_ddg_providers() -> tuple[DuckDuckGoSearchProvider, DuckDuckGoContentProvider]:
    """Construct DuckDuckGo search and content retrieval providers."""
    return DuckDuckGoSearchProvider(), DuckDuckGoContentProvider()
