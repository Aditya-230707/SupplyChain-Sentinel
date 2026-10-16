"""
Supplier entity resolution module.

Implements Rules:
- ID-001: Name-only match cannot be 'confirmed' for common/ambiguous company names.
- ID-002: Exact identifier or multiple independent signals required for 'confirmed'.
- ID-003: Sourced parent/subsidiary required; do not infer blanket attribution.
- ID-004: 'ambiguous', 'mismatch', 'unknown' block strong recommendations.
- ID-005: All decisions expose matched signals, missing signals, and reasons.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Common company suffixes
CORP_SUFFIXES = re.compile(
    r"\b(inc|corp|corporation|ltd|limited|llc|gmbh|sa|bv|plc|co|company)\b",
    re.IGNORECASE,
)


@dataclass
class SupplierProfile:
    id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    official_domains: list[str] = field(default_factory=list)
    registry_ids: list[str] = field(default_factory=list)
    country_or_region: str | None = None
    parts: list[str] = field(default_factory=list)


@dataclass
class EntityResolutionResult:
    status: str  # confirmed | probable | ambiguous | mismatch | unknown
    matched_signals: list[str] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)
    ambiguity_reasons: list[str] = field(default_factory=list)
    explanation: str = ""


def _normalize_name(name: str) -> str:
    cleaned = CORP_SUFFIXES.sub("", name)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return " ".join(cleaned.lower().split())


def resolve_supplier_entity(
    supplier: SupplierProfile,
    subject_text: str | None,
    source_text: str | None = None,
    source_domain: str | None = None,
    location_text: str | None = None,
) -> EntityResolutionResult:
    """Resolve whether a source claim refers to the target supplier.

    Evaluates:
    1. Exact legal name match
    2. Normalized business name match
    3. Alias match
    4. Domain match
    5. Registry ID match
    6. Country / location compatibility
    """
    if not subject_text or not subject_text.strip():
        return EntityResolutionResult(
            status="unknown",
            missing_signals=["subject_text"],
            ambiguity_reasons=["No subject entity mentioned in claim"],
            explanation="The claim does not state a subject entity name.",
        )

    matched: list[str] = []
    missing: list[str] = []
    ambiguities: list[str] = []

    norm_target = _normalize_name(supplier.name)
    norm_subject = _normalize_name(subject_text)

    # 1. Exact full name match
    exact_full = supplier.name.lower().strip() == subject_text.lower().strip()
    norm_match = norm_target == norm_subject

    # Check aliases
    alias_matched: str | None = None
    for alias in supplier.aliases:
        if (
            _normalize_name(alias) == norm_subject
            or alias.lower().strip() == subject_text.lower().strip()
        ):
            alias_matched = alias
            break

    if exact_full:
        matched.append("exact_legal_name")
    elif norm_match:
        matched.append("normalized_name")
    elif alias_matched:
        matched.append(f"alias_match:{alias_matched}")
    else:
        # Check if subject mentions target name as a substring
        if norm_target in norm_subject:
            matched.append("name_substring")
            ambiguities.append(f"Subject '{subject_text}' is broader than target '{supplier.name}'")
        elif norm_subject in norm_target:
            matched.append("subject_is_abbreviation")
            ambiguities.append(
                f"Subject '{subject_text}' may be an abbreviation of '{supplier.name}'"
            )
        else:
            # Mismatch in company name
            return EntityResolutionResult(
                status="mismatch",
                missing_signals=["name_match", "alias_match"],
                ambiguity_reasons=[f"Subject '{subject_text}' does not match '{supplier.name}'"],
                explanation=(
                    f"Claim is about '{subject_text}', "
                    f"which is a distinct entity from '{supplier.name}'."
                ),
            )

    # 2. Domain signal
    domain_matched = False
    if supplier.official_domains and source_domain:
        clean_src_domain = source_domain.lower().replace("www.", "")
        for dom in supplier.official_domains:
            clean_dom = dom.lower().replace("www.", "")
            if clean_dom == clean_src_domain or clean_src_domain.endswith(f".{clean_dom}"):
                matched.append("official_domain")
                domain_matched = True
                break
    if not domain_matched and supplier.official_domains:
        missing.append("official_domain")

    # 3. Location / Country signal
    location_match = False
    if supplier.country_or_region:
        target_country = supplier.country_or_region.lower()
        search_space = f"{location_text or ''} {source_text or ''}".lower()
        if target_country in search_space:
            matched.append(f"country_match:{supplier.country_or_region}")
            location_match = True
        else:
            missing.append("country_match")
    else:
        missing.append("country_context_not_configured")

    # 4. Registry ID check
    registry_match = False
    if supplier.registry_ids and source_text:
        for reg in supplier.registry_ids:
            if reg.lower() in source_text.lower():
                matched.append(f"registry_id:{reg}")
                registry_match = True
                break

    # Determine status
    # ID-002: confirmed requires identifier (registry/domain) OR exact legal name + location/alias
    if registry_match or domain_matched:
        status = "confirmed"
        explanation = f"Entity confirmed via authoritative identifier ({', '.join(matched)})."
    elif exact_full and location_match:
        status = "confirmed"
        explanation = (
            f"Entity confirmed via exact name and location match ({supplier.country_or_region})."
        )
    elif exact_full and not ambiguities:
        # ID-001: Common short names without secondary signal are probable/ambiguous
        if len(norm_target.split()) <= 1 and len(norm_target) <= 6:
            status = "ambiguous"
            ambiguities.append(
                "Single-word short/common name without secondary location/domain signal"
            )
            explanation = (
                f"Name '{supplier.name}' matches but is a short/common name; "
                "secondary signal required."
            )
        else:
            status = "probable"
            explanation = f"Exact name match with no secondary identifier ({', '.join(matched)})."
    elif alias_matched and location_match:
        status = "probable"
        explanation = f"Alias match with confirming location ({', '.join(matched)})."
    elif norm_match or alias_matched:
        status = "probable"
        explanation = f"Compatible name or alias match ({', '.join(matched)})."
    else:
        status = "ambiguous"
        ambiguities.append("Weak name match without confirming secondary signals")
        explanation = f"Ambiguous attribution to '{supplier.name}'; name match only partial."

    return EntityResolutionResult(
        status=status,
        matched_signals=matched,
        missing_signals=missing,
        ambiguity_reasons=ambiguities,
        explanation=explanation,
    )
