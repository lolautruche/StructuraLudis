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
from app.domain.exhibition.entity import Zone, PhysicalTable, Exhibition, TimeSlot
from app.domain.organization.entity import UserGroup
from app.domain.exhibition.schemas import (
    ZoneCreate,
    ZoneUpdate,
    ZoneDelegate,
    ZoneRead,
    PhysicalTableRead,
    PhysicalTableUpdate,
    BatchTablesCreate,
    BatchTablesResponse,
    TimeSlotCreate,
    TimeSlotRead,
    TimeSlotUpdate,
)
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole, ExhibitionRole
from app.api.deps import get_current_active_user, require_zone_manager, has_exhibition_role
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

    # Check permission: SUPER_ADMIN, ADMIN, or exhibition ORGANIZER
    can_create = await has_exhibition_role(
        current_user, exhibition.id, [ExhibitionRole.ORGANIZER], db
    )
    if not can_create:
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


@router.put("/{zone_id}", response_model=ZoneRead)
async def update_zone(
    zone_id: UUID,
    zone_in: ZoneUpdate,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a zone.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)

    await db.flush()
    await db.refresh(zone)

    return zone


@router.post("/{zone_id}/delegate", response_model=ZoneRead)
async def delegate_zone(
    zone_id: UUID,
    delegate_in: ZoneDelegate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delegate a zone to a partner group.

    Only exhibition organizers or SUPER_ADMIN can delegate zones.
    Set delegated_to_group_id to null to remove delegation.
    """
    # Get zone
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Only organizers can delegate zones
    can_delegate = await has_exhibition_role(
        current_user, zone.exhibition_id, [ExhibitionRole.ORGANIZER], db
    )
    if not can_delegate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers can delegate zones",
        )

    # Validate the group exists if specified
    if delegate_in.delegated_to_group_id:
        group_result = await db.execute(
            select(UserGroup).where(UserGroup.id == delegate_in.delegated_to_group_id)
        )
        if not group_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found",
            )

    zone.delegated_to_group_id = delegate_in.delegated_to_group_id
    await db.flush()
    await db.refresh(zone)

    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a zone.

    Only organizers or SUPER_ADMIN can delete zones.
    Deleting a zone will also delete all physical tables in it.
    """
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Only organizers can delete zones
    can_delete = await has_exhibition_role(
        current_user, zone.exhibition_id, [ExhibitionRole.ORGANIZER], db
    )
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers can delete zones",
        )

    await db.delete(zone)


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
    current_user: User = Depends(require_zone_manager),
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
    service = ExhibitionService(db)
    tables = await service.batch_create_tables(zone_id, batch_in)

    return BatchTablesResponse(
        created_count=len(tables),
        tables=tables,
    )


@router.put(
    "/{zone_id}/tables/{table_id}",
    response_model=PhysicalTableRead,
)
async def update_table(
    zone_id: UUID,
    table_id: UUID,
    table_in: PhysicalTableUpdate,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a physical table.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    result = await db.execute(
        select(PhysicalTable).where(
            PhysicalTable.id == table_id,
            PhysicalTable.zone_id == zone_id,
        )
    )
    table = result.scalar_one_or_none()

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical table not found",
        )

    update_data = table_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table, field, value)

    await db.flush()
    await db.refresh(table)

    return table


@router.delete(
    "/{zone_id}/tables/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_table(
    zone_id: UUID,
    table_id: UUID,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a physical table.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    result = await db.execute(
        select(PhysicalTable).where(
            PhysicalTable.id == table_id,
            PhysicalTable.zone_id == zone_id,
        )
    )
    table = result.scalar_one_or_none()

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical table not found",
        )

    await db.delete(table)


# =============================================================================
# Time Slots
# =============================================================================

@router.get("/{zone_id}/slots", response_model=List[TimeSlotRead])
async def list_time_slots(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all time slots in a zone."""
    # Check zone exists
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    slots = await db.execute(
        select(TimeSlot)
        .where(TimeSlot.zone_id == zone_id)
        .order_by(TimeSlot.start_time)
    )
    slots_list = slots.scalars().all()

    # Add zone_name for display
    return [
        TimeSlotRead(
            id=slot.id,
            zone_id=slot.zone_id,
            zone_name=zone.name,
            name=slot.name,
            start_time=slot.start_time,
            end_time=slot.end_time,
            max_duration_minutes=slot.max_duration_minutes,
            buffer_time_minutes=slot.buffer_time_minutes,
            created_at=slot.created_at,
            updated_at=slot.updated_at,
        )
        for slot in slots_list
    ]


@router.post(
    "/{zone_id}/slots",
    response_model=TimeSlotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_slot(
    zone_id: UUID,
    slot_in: TimeSlotCreate,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a time slot in a zone.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    from sqlalchemy.orm import selectinload

    # Check zone exists and get exhibition
    result = await db.execute(
        select(Zone).options(selectinload(Zone.exhibition)).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Validate time slot is within exhibition dates
    exhibition = zone.exhibition
    if slot_in.start_time < exhibition.start_date or slot_in.end_time > exhibition.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot must be within exhibition dates",
        )

    slot = TimeSlot(
        zone_id=zone_id,
        name=slot_in.name,
        start_time=slot_in.start_time,
        end_time=slot_in.end_time,
        max_duration_minutes=slot_in.max_duration_minutes,
        buffer_time_minutes=slot_in.buffer_time_minutes,
    )
    db.add(slot)
    await db.flush()
    await db.refresh(slot)

    return TimeSlotRead(
        id=slot.id,
        zone_id=slot.zone_id,
        zone_name=zone.name,
        name=slot.name,
        start_time=slot.start_time,
        end_time=slot.end_time,
        max_duration_minutes=slot.max_duration_minutes,
        buffer_time_minutes=slot.buffer_time_minutes,
        created_at=slot.created_at,
        updated_at=slot.updated_at,
    )


@router.put(
    "/{zone_id}/slots/{slot_id}",
    response_model=TimeSlotRead,
)
async def update_time_slot(
    zone_id: UUID,
    slot_id: UUID,
    slot_in: TimeSlotUpdate,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a time slot.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.id == slot_id,
            TimeSlot.zone_id == zone_id,
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )

    # Get zone for the response
    zone_result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = zone_result.scalar_one()

    update_data = slot_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(slot, field, value)

    await db.flush()
    await db.refresh(slot)

    return TimeSlotRead(
        id=slot.id,
        zone_id=slot.zone_id,
        zone_name=zone.name,
        name=slot.name,
        start_time=slot.start_time,
        end_time=slot.end_time,
        max_duration_minutes=slot.max_duration_minutes,
        buffer_time_minutes=slot.buffer_time_minutes,
        created_at=slot.created_at,
        updated_at=slot.updated_at,
    )


@router.delete(
    "/{zone_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_time_slot(
    zone_id: UUID,
    slot_id: UUID,
    current_user: User = Depends(require_zone_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a time slot.

    Requires: Zone manager (organizer, SUPER_ADMIN, or delegated partner).
    """
    result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.id == slot_id,
            TimeSlot.zone_id == zone_id,
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )

    await db.delete(slot)
