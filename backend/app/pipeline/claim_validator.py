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
    2. Normalized whitespace search (to handle line breaks in articles).
    3. If neither matches, mark as quote_mismatch.
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

    # 3. Whitespace-normalized match
    norm_source = normalize_whitespace(source_text)
    norm_quote = normalize_whitespace(clean_quote)

    norm_idx = norm_source.find(norm_quote)
    if norm_idx != -1:
        return QuoteValidationResult(
            is_valid=True,
            status="validated",
            quote_start=norm_idx,
            quote_end=norm_idx + len(norm_quote),
        )

    # 4. Whitespace-normalized case-insensitive match
    norm_idx_lower = norm_source.lower().find(norm_quote.lower())
    if norm_idx_lower != -1:
        return QuoteValidationResult(
            is_valid=True,
            status="validated",
            quote_start=norm_idx_lower,
            quote_end=norm_idx_lower + len(norm_quote),
        )

    # Not found in source text
    return QuoteValidationResult(
        is_valid=False,
        status="quote_mismatch",
        mismatch_reason="Quote substring not found in stored source document",
    )
