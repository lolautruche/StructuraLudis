"""
Exhibition API endpoints.

CRUD operations + TimeSlots + Dashboard.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition import Exhibition, TimeSlot
from app.domain.shared.entity import GlobalRole, ExhibitionStatus
from app.domain.exhibition.entity import SafetyTool
from app.domain.exhibition.schemas import (
    ExhibitionCreate,
    ExhibitionRead,
    ExhibitionUpdate,
    ExhibitionDashboard,
    TimeSlotCreate,
    TimeSlotRead,
    TimeSlotUpdate,
    SafetyToolCreate,
    SafetyToolRead,
    SafetyToolUpdate,
    SafetyToolBatchCreate,
    SafetyToolBatchResponse,
)
from app.domain.user.entity import User
from app.api.deps import (
    get_current_active_user,
    get_current_user_optional,
    can_manage_exhibition,
    require_exhibition_organizer,
)
from app.services.exhibition import ExhibitionService

router = APIRouter()


# =============================================================================
# Exhibition CRUD
# =============================================================================

@router.get("", response_model=List[ExhibitionRead])
@router.get("/", response_model=List[ExhibitionRead])
async def list_exhibitions(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all exhibitions with pagination.

    For anonymous users and regular users: only PUBLISHED exhibitions.
    For admins (SUPER_ADMIN, ADMIN): all exhibitions.
    For organizers: PUBLISHED + exhibitions they can manage.
    """
    query = select(Exhibition).offset(skip).limit(limit)
    result = await db.execute(query)
    all_exhibitions = result.scalars().all()

    # Check if user is admin (can see all)
    is_admin = (
        current_user
        and current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]
    )

    # Add can_manage flag and filter based on permissions
    responses = []
    for exhibition in all_exhibitions:
        can_manage = False
        if current_user:
            can_manage = await can_manage_exhibition(current_user, exhibition, db)

        # Filter: show if PUBLISHED, or if user is admin, or if user can manage
        if exhibition.status == ExhibitionStatus.PUBLISHED or is_admin or can_manage:
            response = ExhibitionRead.model_validate(exhibition)
            response.can_manage = can_manage
            responses.append(response)

    return responses


@router.post("", response_model=ExhibitionRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExhibitionRead, status_code=status.HTTP_201_CREATED)
async def create_exhibition(
    exhibition_in: ExhibitionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new exhibition.

    Requires: ORGANIZER or SUPER_ADMIN role.
    User must be member of the target organization (unless SUPER_ADMIN).
    """
    service = ExhibitionService(db)
    return await service.create_exhibition(exhibition_in, current_user)


@router.get("/{exhibition_id}", response_model=ExhibitionRead)
async def get_exhibition(
    exhibition_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single exhibition by ID."""
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Check if current user can manage this exhibition
    user_can_manage = False
    if current_user:
        user_can_manage = await can_manage_exhibition(current_user, exhibition, db)

    # Create response with can_manage flag
    response = ExhibitionRead.model_validate(exhibition)
    response.can_manage = user_can_manage

    return response


@router.put("/{exhibition_id}", response_model=ExhibitionRead)
async def update_exhibition(
    exhibition_id: UUID,
    exhibition_in: ExhibitionUpdate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    update_data = exhibition_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exhibition, field, value)

    await db.flush()
    await db.refresh(exhibition)

    return exhibition


@router.delete("/{exhibition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exhibition(
    exhibition_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    await db.delete(exhibition)


# =============================================================================
# TimeSlot Endpoints
# =============================================================================

@router.get("/{exhibition_id}/slots", response_model=List[TimeSlotRead])
async def list_time_slots(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all time slots for an exhibition."""
    # Check exhibition exists
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    slots = await db.execute(
        select(TimeSlot)
        .where(TimeSlot.exhibition_id == exhibition_id)
        .order_by(TimeSlot.start_time)
    )
    return slots.scalars().all()


@router.post(
    "/{exhibition_id}/slots",
    response_model=TimeSlotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_slot(
    exhibition_id: UUID,
    slot_in: TimeSlotCreate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a time slot for an exhibition.

    Validates:
    - Slot is within exhibition dates
    - max_duration_minutes <= slot duration
    - buffer_time_minutes >= 0

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    service = ExhibitionService(db)
    return await service.create_time_slot(exhibition_id, slot_in)


@router.put(
    "/{exhibition_id}/slots/{slot_id}",
    response_model=TimeSlotRead,
)
async def update_time_slot(
    exhibition_id: UUID,
    slot_id: UUID,
    slot_in: TimeSlotUpdate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a time slot.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.id == slot_id,
            TimeSlot.exhibition_id == exhibition_id,
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )

    update_data = slot_in.model_dump(exclude_unset=True)

    # If updating times, validate consistency
    start_time = update_data.get("start_time", slot.start_time)
    end_time = update_data.get("end_time", slot.end_time)
    max_duration = update_data.get("max_duration_minutes", slot.max_duration_minutes)

    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )

    slot_duration = (end_time - start_time).total_seconds() / 60
    if max_duration > slot_duration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_duration_minutes ({max_duration}) cannot exceed slot duration ({int(slot_duration)} minutes)",
        )

    for field, value in update_data.items():
        setattr(slot, field, value)

    await db.flush()
    await db.refresh(slot)

    return slot


@router.delete(
    "/{exhibition_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_time_slot(
    exhibition_id: UUID,
    slot_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a time slot.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.id == slot_id,
            TimeSlot.exhibition_id == exhibition_id,
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )

    await db.delete(slot)


# =============================================================================
# Dashboard Endpoint
# =============================================================================

@router.get("/{exhibition_id}/status", response_model=ExhibitionDashboard)
async def get_exhibition_status(
    exhibition_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard statistics for an exhibition.

    Returns:
    - Zone and table counts
    - Table occupation rates
    - Session counts by status
    - Total bookings

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    service = ExhibitionService(db)
    return await service.get_exhibition_dashboard(exhibition_id)


# =============================================================================
# SafetyTool Endpoints (JS.A5)
# =============================================================================

@router.get("/{exhibition_id}/safety-tools", response_model=List[SafetyToolRead])
async def list_safety_tools(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    List all safety tools for an exhibition.

    Returns tools ordered by display_order, then name.
    Public endpoint - players can see available safety tools.
    """
    # Check exhibition exists
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    tools = await db.execute(
        select(SafetyTool)
        .where(SafetyTool.exhibition_id == exhibition_id)
        .order_by(SafetyTool.display_order, SafetyTool.name)
    )
    return tools.scalars().all()


@router.post(
    "/{exhibition_id}/safety-tools",
    response_model=SafetyToolRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_safety_tool(
    exhibition_id: UUID,
    tool_in: SafetyToolCreate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a safety tool for an exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    service = ExhibitionService(db)
    return await service.create_safety_tool(exhibition_id, tool_in)


@router.post(
    "/{exhibition_id}/safety-tools/defaults",
    response_model=SafetyToolBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_default_safety_tools(
    exhibition_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a set of common safety tools for an exhibition.

    Includes: X-Card, Lines & Veils, Script Change, Open Door Policy, etc.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    service = ExhibitionService(db)
    return await service.create_default_safety_tools(exhibition_id)


@router.get(
    "/{exhibition_id}/safety-tools/{tool_id}",
    response_model=SafetyToolRead,
)
async def get_safety_tool(
    exhibition_id: UUID,
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single safety tool by ID."""
    result = await db.execute(
        select(SafetyTool).where(
            SafetyTool.id == tool_id,
            SafetyTool.exhibition_id == exhibition_id,
        )
    )
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safety tool not found",
        )

    return tool


@router.put(
    "/{exhibition_id}/safety-tools/{tool_id}",
    response_model=SafetyToolRead,
)
async def update_safety_tool(
    exhibition_id: UUID,
    tool_id: UUID,
    tool_in: SafetyToolUpdate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a safety tool.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(SafetyTool).where(
            SafetyTool.id == tool_id,
            SafetyTool.exhibition_id == exhibition_id,
        )
    )
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safety tool not found",
        )

    update_data = tool_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)

    await db.flush()
    await db.refresh(tool)

    return tool


@router.delete(
    "/{exhibition_id}/safety-tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_safety_tool(
    exhibition_id: UUID,
    tool_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a safety tool.

    Requires: Exhibition organizer or SUPER_ADMIN.
    """
    result = await db.execute(
        select(SafetyTool).where(
            SafetyTool.id == tool_id,
            SafetyTool.exhibition_id == exhibition_id,
        )
    )
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safety tool not found",
        )

    await db.delete(tool)
