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
        fail_on_query: str | None = None,
        status: str = "ok",
    ) -> None:
        self._canned_results = canned_results or []
        self._always_raise = always_raise
        self._fail_on_query = fail_on_query
        self._status = status
        self.last_query: str | None = None
        self.queries: list[str] = []
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
        self.queries.append(query)

        if self._always_raise:
            raise self._always_raise
        if self._fail_on_query == query:
            raise RuntimeError(f"Simulated failure for query: {query}")

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


def get_demo_fixture_providers(
    supplier_name: str | None = None,
) -> tuple[FixtureSearchProvider, FixtureContentProvider]:
    """Return a tailored pair of FixtureSearchProvider and FixtureContentProvider.

    Contains pre-packaged demo scenarios for:
    1. Genuine relevant incident (Silicon Foundry Dresden GmbH)
    2. True but irrelevant incident (Titan Energy Solutions)
    3. Similar name / misleading attribution (Vertex Components Ltd)
    4. Fallback simulated supplier incident
    """
    s_lower = (supplier_name or "").lower()

    if any(k in s_lower for k in ("titan", "energy")):
        # Scenario 2: True but irrelevant incident
        url1 = "https://news.titan-energy.com/press/houston-transformer"
        text1 = (
            "Titan Energy Solutions reported a transformer explosion at its "
            "Houston substation. The substation serves commercial retail office centers. "
            "Central battery pack manufacturing facilities were unaffected."
        )
        url2 = "https://houston-gazette.com/local/substation-incident"
        text2 = (
            "Fire officials confirmed a transformer explosion at "
            "Titan Energy Solutions Houston substation on Monday evening."
        )
        results = [
            SearchResult(
                url=url1,
                title="Titan Energy Press: Transformer Incident at Houston Substation",
                snippet="Titan Energy Solutions reported transformer explosion.",
                domain="titan-energy.com",
                published_date="2026-10-10",
                provider_score=0.92,
            ),
            SearchResult(
                url=url2,
                title="Houston Gazette: Power Substation Incident",
                snippet="Fire crews responded to explosion at Titan Energy Solutions substation.",
                domain="houston-gazette.com",
                published_date="2026-10-10",
                provider_score=0.88,
            ),
        ]
        content_map = {url1: text1, url2: text2}

    elif "vertex" in s_lower:
        # Scenario 3: Similar name / misleading attribution (Melbourne vs UK)
        url = "https://aussie-cyber-brief.com.au/breaches/vertex-melbourne"
        text = (
            "Vertex Ltd announced an immediate suspension of assembly lines "
            "following a cyber incident. The company is based in Melbourne, Australia "
            "and manufactures retail packaging."
        )
        results = [
            SearchResult(
                url=url,
                title="Aussie Cyber Brief: Vertex Ltd Operations Suspended",
                snippet="Vertex Ltd announced assembly line suspension following cyber incident.",
                domain="aussie-cyber-brief.com.au",
                published_date="2026-10-14",
                provider_score=0.89,
            )
        ]
        content_map = {url: text}

    else:
        # Scenario 1 (Default): Genuine relevant incident with syndicated reporting
        name = supplier_name or "Silicon Foundry Dresden GmbH"
        url1 = "https://press.silicon-dresden.de/statements/cleanroom-fire"
        text1 = (
            f"{name} experienced a severe cleanroom fire on Tuesday. "
            "Cleanroom repairs and equipment recalibration are estimated to "
            "require 45 days before production resumes."
        )
        url2 = "https://reuters.com/business/semiconductors/dresden-cleanroom-fire"
        text2 = (
            f"Reuters reports that {name} experienced a severe cleanroom fire on Tuesday. "
            "German industrial authorities are inspecting the cleanroom blaze."
        )
        url3 = "https://techwires.de/reuters-syndicated-dresden-fire"
        text3 = (
            f"According to Reuters, {name} experienced a severe cleanroom fire on Tuesday. "
            "Semiconductor wafer deliveries face delay."
        )
        results = [
            SearchResult(
                url=url1,
                title=f"{name} Official Statement: Cleanroom Fire",
                snippet=f"{name} experienced a severe cleanroom fire on Tuesday.",
                domain="silicon-dresden.de",
                published_date="2026-10-12",
                provider_score=0.98,
            ),
            SearchResult(
                url=url2,
                title=f"Reuters: {name} Halts Fab 1 Production",
                snippet=f"Reuters reports {name} experienced a severe cleanroom fire.",
                domain="reuters.com",
                published_date="2026-10-13",
                provider_score=0.94,
            ),
            SearchResult(
                url=url3,
                title=f"TechWires: Reuters Reports {name} Cleanroom Fire",
                snippet=f"According to Reuters, {name} experienced a severe cleanroom fire.",
                domain="techwires.de",
                published_date="2026-10-13",
                provider_score=0.85,
            ),
        ]
        content_map = {url1: text1, url2: text2, url3: text3}

    return FixtureSearchProvider(results), FixtureContentProvider(content_map)
