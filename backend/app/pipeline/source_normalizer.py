"""
Source URL and text normalizer.

Implements Rules:
- E-001: URL canonicalization and exact duplicate detection.
- E-002: Title/content normalization for candidate grouping.
- E-008: Separation of publication date and candidate event date.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAM_PREFIXES = ("utm_", "ga_", "mc_")
TRACKING_PARAMS = frozenset(
    [
        "fbclid",
        "gclid",
        "msclkid",
        "yclid",
        "_hsenc",
        "_hsmi",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
        "source",
    ]
)


def canonicalize_url(url: str) -> str:
    """Normalize a URL to its canonical representation.

    - Lowercases scheme and netloc.
    - Removes fragments.
    - Strips known marketing/click tracking query parameters while preserving content queries.
    - Normalizes trailing slashes on bare paths.
    """
    if not url:
        return ""

    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if (scheme == "http" and netloc.endswith(":80")) or (
        scheme == "https" and netloc.endswith(":443")
    ):
        netloc = netloc.rsplit(":", 1)[0]

    # Normalize path: preserve trailing slash unless root path
    path = parsed.path
    if not path:
        path = "/"
    elif path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")

    # Filter out tracking query params
    filtered_query: list[tuple[str, str]] = []
    if parsed.query:
        for k, v in parse_qsl(parsed.query, keep_blank_values=True):
            k_lower = k.lower()
            if any(k_lower.startswith(pfx) for pfx in TRACKING_PARAM_PREFIXES):
                continue
            if k_lower in TRACKING_PARAMS:
                continue
            filtered_query.append((k, v))

    # Sort query parameters for deterministic canonical URL
    filtered_query.sort(key=lambda x: x[0])
    query = urlencode(filtered_query)

    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def compute_content_hash(text: str | None) -> str | None:
    """Compute SHA-256 hash of normalized text for exact content duplicate check."""
    if not text:
        return None
    normalized = " ".join(text.split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def tokenize_title(title: str | None) -> set[str]:
    """Tokenize a title for near-duplicate candidate detection."""
    if not title:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    tokens = {t for t in cleaned.split() if len(t) > 2}
    return tokens


def title_similarity_jaccard(title_a: str | None, title_b: str | None) -> float:
    """Compute Jaccard token similarity between two titles."""
    tokens_a = tokenize_title(title_a)
    tokens_b = tokenize_title(title_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0
