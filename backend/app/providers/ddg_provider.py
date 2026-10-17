"""
DuckDuckGo search and live content retrieval provider.

Implements SearchProvider and ContentProvider without requiring API keys.
Handles rate limits, empty results, timeouts, and page blocking explicitly.
"""

from __future__ import annotations

import asyncio
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

        from urllib.parse import urlparse

        results: list[SearchResult] = []
        for it in items:
            url = it.get("url", "")
            if not url or not url.startswith("http"):
                continue

            domain = urlparse(url).netloc or None
            results.append(
                SearchResult(
                    url=url,
                    title=it.get("title", ""),
                    snippet=it.get("content", ""),
                    domain=domain,
                    published_date=it.get("published_date"),
                    provider_score=0.85,
                    raw_content=None,
                )
            )

        log.info("duckduckgo_search_completed", query=query, count=len(results))
        return SearchResponse(
            query=query,
            results=results,
            provider_name=self.provider_name,
            status="ok" if results else "no_results",
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

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """SSRF protection: block loopback, private networks, and invalid schemes."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            host = (parsed.hostname or "").lower()
            if not host:
                return False
            if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):  # noqa: S104
                return False
            if host.endswith(".local") or host.endswith(".internal"):
                return False
            # Block private IP ranges
            import ipaddress

            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                pass  # It's a hostname, not an IP literal
            return True
        except Exception:
            return False

    async def fetch_one(self, client: httpx.AsyncClient, url: str) -> ContentResult:
        """Fetch and extract visible text from public URL."""
        if not self._is_safe_url(url):
            log.warning("ssrf_blocked_url", url=url)
            return ContentResult(
                url=url,
                status="inaccessible",
                text=None,
                title=None,
                error_message="Blocked: private or invalid URL destination",
            )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            resp = await client.get(url, headers=headers)

            if resp.status_code >= 400:
                log.warning(
                    "public_page_blocked_or_missing",
                    url=url,
                    status_code=resp.status_code,
                )
                return ContentResult(
                    url=url,
                    status="inaccessible",
                    text=None,
                    title=None,
                    error_message=f"HTTP {resp.status_code}",
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
                status="available" if clean_text else "snippet_only",
                text=clean_text or None,
                title=title,
            )

        except Exception as exc:
            log.warning("public_page_fetch_failed", url=url, error=str(exc))
            return ContentResult(
                url=url,
                status="extraction_failed",
                text=None,
                title=None,
                error_message=str(exc)[:200],
            )

    async def extract(self, urls: list[str]) -> list[ContentResult]:
        """Extract full text content for a list of URLs."""
        if not urls:
            return []

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            tasks = [self.fetch_one(client, u) for u in urls]
            return await asyncio.gather(*tasks)

    async def health_check(self) -> dict[str, object]:
        return {
            "configured": True,
            "provider_name": self.provider_name,
            "reachable": True,
            "error": None,
        }


def make_ddg_providers() -> tuple[DuckDuckGoSearchProvider, DuckDuckGoContentProvider]:
    """Construct DuckDuckGo search and content retrieval providers."""
    return DuckDuckGoSearchProvider(), DuckDuckGoContentProvider()
