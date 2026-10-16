"""
Supplier CRUD endpoints — Phase 1 skeleton.

Full implementation in Phase 4. For now: list and create are wired up;
remaining endpoints return placeholder stubs so the frontend can import
the API module without errors.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.db.models import Supplier as SupplierModel
from app.db.session import get_db_session
from app.schemas.supplier import (
    SupplierCreate,
    SupplierListItem,
    SupplierListResponse,
    SupplierRead,
    SupplierUpdate,
)

log = structlog.get_logger(__name__)
router = APIRouter(tags=["suppliers"])


@router.get("/suppliers", response_model=SupplierListResponse)
async def list_suppliers(
    query: str | None = Query(default=None, description="Filter by name substring"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> SupplierListResponse:
    stmt = select(SupplierModel).where(SupplierModel.active == True)  # noqa: E712
    if query:
        stmt = stmt.where(SupplierModel.name.ilike(f"%{query}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(SupplierModel.name).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()

    return SupplierListResponse(
        items=[SupplierListItem.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/suppliers", response_model=SupplierRead, status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db_session),
) -> SupplierRead:
    from app.db.models import SupplierPart as SupplierPartModel

    supplier = SupplierModel(
        name=payload.name,
        aliases=payload.aliases,
        official_domains=payload.official_domains,
        registry_ids=payload.registry_ids,
        country_or_region=payload.country_or_region,
        notes=payload.notes,
        criticality=payload.criticality,
        active=payload.active,
    )
    db.add(supplier)
    await db.flush()  # get ID before adding parts

    for p in payload.parts:
        part = SupplierPartModel(
            supplier_id=supplier.id,
            part_name=p.part_name,
            part_number=p.part_number,
            inventory_coverage_days=p.inventory_coverage_days,
            typical_lead_time_days=p.typical_lead_time_days,
            recovery_duration_days=p.recovery_duration_days,
            alternative_supplier_available=p.alternative_supplier_available,
            business_unit=p.business_unit,
            relationship_source=p.relationship_source,
        )
        db.add(part)

    await db.flush()
    await db.refresh(supplier, attribute_names=["parts"])
    log.info("supplier_created", supplier_id=supplier.id, name=supplier.name)
    return SupplierRead.model_validate(supplier)


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> SupplierRead:
    stmt = (
        select(SupplierModel)
        .options(selectinload(SupplierModel.parts))
        .where(SupplierModel.id == supplier_id)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise NotFoundError(f"Supplier {supplier_id} not found")
    return SupplierRead.model_validate(row)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRead)
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> SupplierRead:
    stmt = (
        select(SupplierModel)
        .options(selectinload(SupplierModel.parts))
        .where(SupplierModel.id == supplier_id)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise NotFoundError(f"Supplier {supplier_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(row, field, value)

    await db.flush()
    await db.refresh(row, attribute_names=["parts"])
    return SupplierRead.model_validate(row)
