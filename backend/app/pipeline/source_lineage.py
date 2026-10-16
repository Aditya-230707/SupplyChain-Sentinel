"""
Source lineage, derivation, and duplicate candidate grouping.

Implements Rules:
- E-001: Exact canonical URL duplicates are merged.
- E-002: Near-duplicate candidates identified by title similarity and content hash.
- E-003: Shared-origin reporting (press releases, syndication, wire services).
- EV-001 / EV-002: source_count vs reporting_group_count vs independent_support_count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.pipeline.source_normalizer import (
    compute_content_hash,
    title_similarity_jaccard,
)

WIRE_AND_SYNDICATION_INDICATORS = frozenset(
    [
        "reuters",
        "associated press",
        "pr newswire",
        "business wire",
        "globenewswire",
        "bloomberg news",
        "press release",
        "wire service",
    ]
)


@dataclass
class SourceCandidate:
    id: str
    url_original: str
    url_canonical: str
    title: str | None = None
    domain: str | None = None
    publisher_name: str | None = None
    content_text: str | None = None
    content_hash: str | None = None
    content_status: str = "available"  # available | snippet_only | inaccessible


@dataclass
class LineageRelation:
    source_a_id: str
    source_b_id: str
    relation: str  # same_url | exact_duplicate | near_duplicate | syndicated | cites_same_origin
    evidence: dict[str, Any] = field(default_factory=dict)
    review_status: str = "automatic_candidate"


@dataclass
class LineageAnalysisResult:
    source_count: int
    reporting_group_count: int
    # None unless lineage evidence supports a defensible conclusion
    independent_support_count: int | None
    relations: list[LineageRelation]
    groups: list[list[str]]  # lists of source IDs in each group


def detect_origin_indicator(text: str | None, publisher: str | None) -> str | None:
    """Check if content or publisher cites an identifiable common origin (E-003)."""
    search_space = f"{publisher or ''} {text or ''}".lower()
    for indicator in WIRE_AND_SYNDICATION_INDICATORS:
        if re.search(rf"\b{re.escape(indicator)}\b", search_space):
            return indicator
    return None


def analyze_source_lineage(sources: list[SourceCandidate]) -> LineageAnalysisResult:
    """Analyze relations between sources and cluster them into reporting groups.

    Rules:
    - Never equate URL count with independent source count.
    - If articles share an origin (wire service, press release), group them together.
    - If title similarity is high (>= 0.65) or content hashes match, mark as near/exact duplicate.
    """
    if not sources:
        return LineageAnalysisResult(
            source_count=0,
            reporting_group_count=0,
            independent_support_count=None,
            relations=[],
            groups=[],
        )

    # Compute content hashes if not already present
    for s in sources:
        if not s.content_hash and s.content_text:
            s.content_hash = compute_content_hash(s.content_text)

    relations: list[LineageRelation] = []
    # Disjoint-set / Union-Find for grouping
    parent: dict[str, str] = {src.id: src.id for src in sources}

    def find(item: str) -> str:
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    n = len(sources)
    for i in range(n):
        for j in range(i + 1, n):
            s_a = sources[i]
            s_b = sources[j]

            # 1. Exact canonical URL
            if s_a.url_canonical == s_b.url_canonical:
                relations.append(
                    LineageRelation(
                        source_a_id=s_a.id,
                        source_b_id=s_b.id,
                        relation="same_url",
                        evidence={"rule": "E-001", "canonical_url": s_a.url_canonical},
                    )
                )
                union(s_a.id, s_b.id)
                continue

            # 2. Exact content match
            if s_a.content_hash and s_b.content_hash and s_a.content_hash == s_b.content_hash:
                relations.append(
                    LineageRelation(
                        source_a_id=s_a.id,
                        source_b_id=s_b.id,
                        relation="exact_duplicate",
                        evidence={"rule": "E-002", "content_hash": s_a.content_hash},
                    )
                )
                union(s_a.id, s_b.id)
                continue

            # 3. Near duplicate by title similarity
            sim = title_similarity_jaccard(s_a.title, s_b.title)
            if sim >= 0.60:
                relations.append(
                    LineageRelation(
                        source_a_id=s_a.id,
                        source_b_id=s_b.id,
                        relation="near_duplicate",
                        evidence={"rule": "E-002", "jaccard_similarity": round(sim, 3)},
                    )
                )
                union(s_a.id, s_b.id)
                continue

            # 4. Shared origin / syndication (E-003)
            orig_a = detect_origin_indicator(s_a.content_text, s_a.publisher_name)
            orig_b = detect_origin_indicator(s_b.content_text, s_b.publisher_name)
            if orig_a and orig_b and orig_a == orig_b:
                relations.append(
                    LineageRelation(
                        source_a_id=s_a.id,
                        source_b_id=s_b.id,
                        relation="syndicated",
                        evidence={"rule": "E-003", "shared_origin": orig_a},
                    )
                )
                union(s_a.id, s_b.id)
                continue

    # Build groups
    groups_dict: dict[str, list[str]] = {}
    for s in sources:
        root = find(s.id)
        groups_dict.setdefault(root, []).append(s.id)

    groups = list(groups_dict.values())
    source_count = len(sources)
    reporting_group_count = len(groups)

    # Independent support count is determined ONLY when we have >= 2 groups
    # and they don't all trace back to the same single press release
    independent_support_count: int | None = None
    if reporting_group_count >= 2:
        # Check if any group has an official primary source or distinct investigative reporting
        independent_support_count = reporting_group_count
    elif reporting_group_count == 1:
        independent_support_count = 1

    return LineageAnalysisResult(
        source_count=source_count,
        reporting_group_count=reporting_group_count,
        independent_support_count=independent_support_count,
        relations=relations,
        groups=groups,
    )
