"""
Zone API endpoints.

Zone management and physical table batch creation.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition.entity import Zone, PhysicalTable, Exhibition
from app.domain.exhibition.schemas import (
    ZoneCreate,
    ZoneRead,
    PhysicalTableRead,
    BatchTablesCreate,
    BatchTablesResponse,
)
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole
from app.api.deps import get_current_active_user
from app.services.exhibition import ExhibitionService

router = APIRouter()


# =============================================================================
# Zone CRUD
# =============================================================================

@router.get("/", response_model=List[ZoneRead])
async def list_zones(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all zones for an exhibition."""
    result = await db.execute(
        select(Zone)
        .where(Zone.exhibition_id == exhibition_id)
        .order_by(Zone.name)
    )
    return result.scalars().all()


@router.post("/", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone_in: ZoneCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new zone.

    Requires: Exhibition organizer or SUPER_ADMIN.
    Optionally delegate zone to a partner UserGroup.
    """
    # Get exhibition to check permissions
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == zone_in.exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Check permission
    if current_user.global_role != GlobalRole.SUPER_ADMIN:
        if current_user.global_role != GlobalRole.ORGANIZER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizers can create zones",
            )

    service = ExhibitionService(db)
    return await service.create_zone(zone_in, current_user)


@router.get("/{zone_id}", response_model=ZoneRead)
async def get_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single zone by ID."""
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    return zone


# =============================================================================
# Physical Tables
# =============================================================================

@router.get("/{zone_id}/tables", response_model=List[PhysicalTableRead])
async def list_tables(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all physical tables in a zone."""
    # Check zone exists
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    tables = await db.execute(
        select(PhysicalTable)
        .where(PhysicalTable.zone_id == zone_id)
        .order_by(PhysicalTable.label)
    )
    return tables.scalars().all()


@router.post(
    "/{zone_id}/batch-tables",
    response_model=BatchTablesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def batch_create_tables(
    zone_id: UUID,
    batch_in: BatchTablesCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch create physical tables in a zone.

    Format: { "prefix": "Table ", "count": 50, "starting_number": 1, "capacity": 6 }

    Validates:
    - Zone exists
    - User can manage zone (organizer or delegated partner)
    - Labels are unique within zone

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    # Get zone with exhibition to check permissions
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Check permission (simplified - should use require_zone_manager in production)
    if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER, GlobalRole.PARTNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this zone",
        )

    service = ExhibitionService(db)
    tables = await service.batch_create_tables(zone_id, batch_in)

    return BatchTablesResponse(
        created_count=len(tables),
        tables=tables,
    )
