"""
Pydantic schemas for Supplier and SupplierPart API contracts.

Separates read (response), create, and update shapes.
All request payloads are validated before touching business logic.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---- SupplierPart -------------------------------------------


class SupplierPartBase(BaseModel):
    part_name: str = Field(..., min_length=1, max_length=500)
    part_number: str | None = Field(default=None, max_length=200)
    inventory_coverage_days: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Known inventory coverage in days. Null = unknown — never assumed zero.",
    )
    typical_lead_time_days: Decimal | None = Field(default=None, ge=Decimal("0"))
    recovery_duration_days: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Evidence-backed or user scenario assumption. Never hallucinated.",
    )
    alternative_supplier_available: Literal["yes", "no", "unknown"] = "unknown"
    business_unit: str | None = Field(default=None, max_length=200)
    relationship_source: Literal["user_input", "imported_file", "source_evidence"] = "user_input"


class SupplierPartCreate(SupplierPartBase):
    pass


class SupplierPartRead(SupplierPartBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier_id: str
    last_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---- Supplier -----------------------------------------------


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    aliases: list[str] = Field(default_factory=list)
    official_domains: list[str] = Field(default_factory=list)
    registry_ids: list[str] = Field(default_factory=list)
    country_or_region: str | None = Field(default=None, max_length=200)
    notes: str | None = None
    criticality: Literal["low", "medium", "high", "unknown"] = "unknown"
    active: bool = True

    @field_validator("aliases", "official_domains", "registry_ids", mode="before")
    @classmethod
    def deduplicate_list(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        return [x for x in v if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

    @field_validator("name")
    @classmethod
    def name_not_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            msg = "Supplier name must not be whitespace only"
            raise ValueError(msg)
        return stripped


class SupplierCreate(SupplierBase):
    parts: list[SupplierPartCreate] = Field(default_factory=list)


class SupplierUpdate(BaseModel):
    """Partial update — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=500)
    aliases: list[str] | None = None
    official_domains: list[str] | None = None
    registry_ids: list[str] | None = None
    country_or_region: str | None = None
    notes: str | None = None
    criticality: Literal["low", "medium", "high", "unknown"] | None = None
    active: bool | None = None


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parts: list[SupplierPartRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SupplierListItem(BaseModel):
    """Lightweight supplier list entry (no parts)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    aliases: list[str]
    criticality: Literal["low", "medium", "high", "unknown"]
    active: bool
    country_or_region: str | None = None
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    items: list[SupplierListItem]
    total: int
    limit: int
    offset: int
