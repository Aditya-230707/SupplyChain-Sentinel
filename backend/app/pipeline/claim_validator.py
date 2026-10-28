"""
Quote and claim validation module.

Implements Rule E-005:
The extracted supporting quote MUST be an exact or conservative-whitespace match
of the stored source document text. If not, mark 'quote_mismatch' and prevent
the claim from being used in high-consequence recommendations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QuoteValidationResult:
    is_valid: bool
    status: str  # validated | quote_mismatch
    quote_start: int | None = None
    quote_end: int | None = None
    mismatch_reason: str | None = None


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace by collapsing multiple space characters into one."""
    return re.sub(r"\s+", " ", text).strip()


def verify_quote_against_source(
    quote: str | None,
    source_text: str | None,
) -> QuoteValidationResult:
    """Verify that a claim's quote actually exists within the source text.

    Steps:
    1. Direct exact substring search.
    2. Case-insensitive exact match.
    3. Whitespace-flexible regex search on original source text to find
       the exact character offsets without offset drift from normalization.
    4. If none matches, mark as quote_mismatch.
    """
    if not quote or not quote.strip():
        return QuoteValidationResult(
            is_valid=False,
            status="quote_mismatch",
            mismatch_reason="Quote is empty or missing",
        )

    if not source_text or not source_text.strip():
        return QuoteValidationResult(
            is_valid=False,
            status="quote_mismatch",
            mismatch_reason="Source document text is empty or unavailable",
        )

    clean_quote = quote.strip()

    # 1. Exact match
    idx = source_text.find(clean_quote)
    if idx != -1:
        return QuoteValidationResult(
            is_valid=True,
            status="validated",
            quote_start=idx,
            quote_end=idx + len(clean_quote),
        )

    # 2. Case-insensitive exact match
    idx_lower = source_text.lower().find(clean_quote.lower())
    if idx_lower != -1:
        return QuoteValidationResult(
            is_valid=True,
            status="validated",
            quote_start=idx_lower,
            quote_end=idx_lower + len(clean_quote),
        )

    # 3. Whitespace-flexible regex search on original source text
    tokens = clean_quote.split()
    if tokens:
        pattern = r"\s+".join(re.escape(t) for t in tokens)
        match = re.search(pattern, source_text)
        if match:
            return QuoteValidationResult(
                is_valid=True,
                status="validated",
                quote_start=match.start(),
                quote_end=match.end(),
            )
        # 4. Case-insensitive whitespace-flexible match
        match_ci = re.search(pattern, source_text, re.IGNORECASE)
        if match_ci:
            return QuoteValidationResult(
                is_valid=True,
                status="validated",
                quote_start=match_ci.start(),
                quote_end=match_ci.end(),
            )

        # 5. Typographical equivalence match (straight vs curly quotes, dashes, apostrophes)
        pattern_typo = _build_typographic_pattern(clean_quote)
        match_typo = re.search(pattern_typo, source_text, re.IGNORECASE)
        if match_typo:
            return QuoteValidationResult(
                is_valid=True,
                status="validated",
                quote_start=match_typo.start(),
                quote_end=match_typo.end(),
            )

    # Not found in source text
    return QuoteValidationResult(
        is_valid=False,
        status="quote_mismatch",
        mismatch_reason="Quote substring not found in stored source document",
    )


def _build_typographic_pattern(clean_quote: str) -> str:
    """Build regex pattern matching straight/curly quotes, apostrophes, and dashes."""
    escaped_tokens = []
    for token in clean_quote.split():
        escaped = re.escape(token)
        escaped = escaped.replace('"', '["\u201c\u201d]')
        escaped = escaped.replace("'", "['\u2018\u2019]")
        escaped = escaped.replace(r"\-", "[-\u2013\u2014]")
        escaped_tokens.append(escaped)
    return r"\s+".join(escaped_tokens)


def check_quote_relevance(
    quote: str | None,
    subject_text: str | None,
    object_text: str | None,
) -> bool:
    """Heuristic check: does the quote mention key terms from subject or object?"""
    if not quote:
        return False
    target_terms: set[str] = set()
    stopwords = {
        "inc",
        "ltd",
        "gmbh",
        "corp",
        "llc",
        "the",
        "and",
        "for",
        "with",
        "from",
        "was",
        "were",
    }
    for text in (subject_text, object_text):
        if text:
            for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower()):
                if w not in stopwords:
                    target_terms.add(w)
    if not target_terms:
        return True  # Cannot determine, give benefit of doubt
    quote_lower = quote.lower()
    return any(term in quote_lower for term in target_terms)
