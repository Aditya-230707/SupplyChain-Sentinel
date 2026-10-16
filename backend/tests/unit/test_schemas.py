"""
Unit tests for Pydantic domain schemas.

Verifies:
- Supplier creation, deduplication, whitespace-stripped name
- SupplierPart null-safety (inventory_coverage_days=None ≠ 0)
- InvestigationCreate category allowlist
- ExposureAssessment null gap days
- HumanReviewCreate action enum
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.decision import HumanReviewCreate
from app.schemas.incident import ExposureAssessmentRead
from app.schemas.investigation import VALID_CATEGORIES, InvestigationCreate
from app.schemas.supplier import SupplierCreate, SupplierPartCreate, SupplierUpdate

# ---- Supplier -----------------------------------------------


def test_supplier_create_minimal() -> None:
    s = SupplierCreate(name="Acme Corp")
    assert s.name == "Acme Corp"
    assert s.criticality == "unknown"
    assert s.active is True
    assert s.aliases == []


def test_supplier_name_strips_whitespace() -> None:
    s = SupplierCreate(name="  Acme Corp  ")
    assert s.name == "Acme Corp"


def test_supplier_name_whitespace_only_raises() -> None:
    with pytest.raises(ValidationError, match="whitespace"):
        SupplierCreate(name="   ")


def test_supplier_aliases_deduplicated() -> None:
    s = SupplierCreate(name="Acme", aliases=["A", "B", "A", "C", "B"])
    assert s.aliases == ["A", "B", "C"]


def test_supplier_criticality_enum() -> None:
    with pytest.raises(ValidationError):
        SupplierCreate(name="Acme", criticality="critical")  # type: ignore[arg-type]


def test_supplier_update_partial() -> None:
    u = SupplierUpdate(name="New Name")
    assert u.name == "New Name"
    assert u.criticality is None  # not set


# ---- SupplierPart -------------------------------------------


def test_part_null_inventory_stays_null() -> None:
    """inventory_coverage_days=None must remain None — never default to 0."""
    p = SupplierPartCreate(part_name="Widget", inventory_coverage_days=None)
    assert p.inventory_coverage_days is None


def test_part_negative_inventory_raises() -> None:
    with pytest.raises(ValidationError):
        SupplierPartCreate(part_name="Widget", inventory_coverage_days=Decimal("-1"))


def test_part_alternative_supplier_enum() -> None:
    p = SupplierPartCreate(part_name="Widget", alternative_supplier_available="unknown")
    assert p.alternative_supplier_available == "unknown"

    with pytest.raises(ValidationError):
        SupplierPartCreate(part_name="Widget", alternative_supplier_available="maybe")  # type: ignore[arg-type]


# ---- InvestigationCreate ------------------------------------


def test_investigation_create_default_categories() -> None:
    inv = InvestigationCreate(supplier_id="00000000-0000-0000-0000-000000000001")
    assert set(inv.requested_categories) == VALID_CATEGORIES


def test_investigation_create_valid_category() -> None:
    inv = InvestigationCreate(
        supplier_id="00000000-0000-0000-0000-000000000001",
        requested_categories=["operational_disruption"],
    )
    assert inv.requested_categories == ["operational_disruption"]


def test_investigation_supplier_id_required() -> None:
    with pytest.raises(ValidationError):
        InvestigationCreate()  # type: ignore[call-arg]


# ---- ExposureAssessment -------------------------------------


def test_exposure_gap_days_nullable() -> None:
    """Null gap days are valid — null means unknown, not zero."""
    exp = ExposureAssessmentRead(
        id="e1",
        incident_id="i1",
        input_values_json={},
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        potential_inventory_gap_days=None,  # unknown — must stay null
        criticality="unknown",
        alternative_available="unknown",
        exposure_band="unknown",
        assumptions=[],
        limitations=["recovery_duration_days unknown"],
        created_at="2026-10-01T00:00:00",
    )
    assert exp.potential_inventory_gap_days is None
    assert exp.exposure_band == "unknown"


# ---- HumanReview -------------------------------------------


def test_human_review_valid_actions() -> None:
    for action in [
        "approve_recommendation",
        "reject_recommendation",
        "request_more_information",
        "mark_monitor_only",
    ]:
        r = HumanReviewCreate(action=action)  # type: ignore[arg-type]
        assert r.action == action


def test_human_review_invalid_action_raises() -> None:
    with pytest.raises(ValidationError):
        HumanReviewCreate(action="suspend_supplier")  # type: ignore[arg-type]
        # No high-impact action may be expressed via this enum


def test_human_review_note_optional() -> None:
    r = HumanReviewCreate(action="approve_recommendation")
    assert r.reviewer_note is None
