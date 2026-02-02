"""
Exhibition API endpoints.

CRUD operations + TimeSlots + Dashboard.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition import Exhibition, TimeSlot
from app.domain.shared.entity import GlobalRole, ExhibitionRole, ExhibitionStatus
from app.domain.exhibition.entity import SafetyTool, Zone
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
    ExhibitionRoleCreate,
    ExhibitionRoleRead,
    ExhibitionRoleUpdate,
)
from app.domain.user.entity import User, UserExhibitionRole
from app.api.deps import (
    get_current_active_user,
    get_current_user_optional,
    has_any_exhibition_role,
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
        and current_user.global_role == GlobalRole.SUPER_ADMIN
    )

    # Add can_manage flag and filter based on permissions
    responses = []
    for exhibition in all_exhibitions:
        can_manage = False
        user_exhibition_role = None

        if current_user:
            # Check if user has any role (ORGANIZER or PARTNER) for this exhibition
            can_manage = await has_any_exhibition_role(current_user, exhibition, db)

            # Get specific role if user can manage
            if can_manage:
                if is_admin:
                    user_exhibition_role = "ORGANIZER"  # Admins have full access
                else:
                    role_result = await db.execute(
                        select(UserExhibitionRole).where(
                            UserExhibitionRole.user_id == current_user.id,
                            UserExhibitionRole.exhibition_id == exhibition.id,
                        )
                    )
                    role_assignment = role_result.scalar_one_or_none()
                    if role_assignment:
                        user_exhibition_role = role_assignment.role.value

        # Filter: show if PUBLISHED, or if user is admin, or if user can manage
        if exhibition.status == ExhibitionStatus.PUBLISHED or is_admin or can_manage:
            response = ExhibitionRead.model_validate(exhibition)
            response.can_manage = can_manage
            response.user_exhibition_role = user_exhibition_role
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

    # Check if current user has any role (ORGANIZER or PARTNER) for this exhibition
    user_can_manage = False
    user_exhibition_role = None

    if current_user:
        user_can_manage = await has_any_exhibition_role(current_user, exhibition, db)

        # Get specific role if user can manage
        if user_can_manage:
            # Check for super admin or admin (they can manage all exhibitions)
            if current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
                user_exhibition_role = "ORGANIZER"  # Admins have full access
            else:
                # Get user's exhibition role
                role_result = await db.execute(
                    select(UserExhibitionRole).where(
                        UserExhibitionRole.user_id == current_user.id,
                        UserExhibitionRole.exhibition_id == exhibition_id,
                    )
                )
                role_assignment = role_result.scalar_one_or_none()
                if role_assignment:
                    user_exhibition_role = role_assignment.role.value

    # Create response with can_manage flag and user role
    response = ExhibitionRead.model_validate(exhibition)
    response.can_manage = user_can_manage
    response.user_exhibition_role = user_exhibition_role

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


# =============================================================================
# User Search for Role Assignment (#99)
# =============================================================================


class UserSearchResult(BaseModel):
    """Minimal user info for role assignment search."""
    id: UUID
    email: str
    full_name: Optional[str] = None


@router.get("/{exhibition_id}/users/search", response_model=List[UserSearchResult])
async def search_users_for_role(
    exhibition_id: UUID,
    q: str,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Search users by email or name for role assignment.

    Returns users matching the query who don't already have a role for this exhibition.
    Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.

    Query must be at least 3 characters.
    """
    if len(q) < 3:
        return []

    search_pattern = f"%{q.lower()}%"

    # Get users already assigned to this exhibition
    existing_users = await db.execute(
        select(UserExhibitionRole.user_id).where(
            UserExhibitionRole.exhibition_id == exhibition_id
        )
    )
    existing_user_ids = {row[0] for row in existing_users.fetchall()}

    # Search users by email or name
    result = await db.execute(
        select(User)
        .where(
            User.is_active == True,
            (
                User.email.ilike(search_pattern) |
                User.full_name.ilike(search_pattern)
            ),
            ~User.id.in_(existing_user_ids) if existing_user_ids else True,
        )
        .order_by(User.full_name.asc(), User.email.asc())
        .limit(20)
    )
    users = result.scalars().all()

    return [
        UserSearchResult(id=u.id, email=u.email, full_name=u.full_name)
        for u in users
    ]


# =============================================================================
# Exhibition Role Management (#99)
# =============================================================================

@router.get("/{exhibition_id}/roles", response_model=List[ExhibitionRoleRead])
async def list_exhibition_roles(
    exhibition_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    List all role assignments for an exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
    """
    # Get the exhibition to find the main organizer (creator)
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = exhibition_result.scalar_one_or_none()
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    result = await db.execute(
        select(UserExhibitionRole, User.email, User.full_name)
        .join(User, UserExhibitionRole.user_id == User.id)
        .where(UserExhibitionRole.exhibition_id == exhibition_id)
        .order_by(UserExhibitionRole.role, User.email)
    )
    rows = result.all()

    return [
        ExhibitionRoleRead(
            id=role.id,
            user_id=role.user_id,
            exhibition_id=role.exhibition_id,
            role=role.role,
            zone_ids=role.zone_ids,
            user_email=email,
            user_full_name=full_name,
            is_main_organizer=(
                role.role == ExhibitionRole.ORGANIZER
                and exhibition.created_by_id is not None
                and role.user_id == exhibition.created_by_id
            ),
            created_at=role.created_at,
            updated_at=role.updated_at,
        )
        for role, email, full_name in rows
    ]


@router.post(
    "/{exhibition_id}/roles",
    response_model=ExhibitionRoleRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_exhibition_role(
    exhibition_id: UUID,
    role_in: ExhibitionRoleCreate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a role to a user for this exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.

    For PARTNER role, zone_ids must be specified and all zones must belong
    to this exhibition.
    """
    # Check user exists
    user_result = await db.execute(
        select(User).where(User.id == role_in.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check no existing role for this user/exhibition
    existing = await db.execute(
        select(UserExhibitionRole).where(
            UserExhibitionRole.user_id == role_in.user_id,
            UserExhibitionRole.exhibition_id == exhibition_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a role for this exhibition",
        )

    # For PARTNER, validate zone_ids belong to this exhibition
    zone_ids_str = None
    if role_in.role == ExhibitionRole.PARTNER and role_in.zone_ids:
        zones_result = await db.execute(
            select(Zone.id).where(
                Zone.id.in_(role_in.zone_ids),
                Zone.exhibition_id == exhibition_id,
            )
        )
        valid_zones = {row[0] for row in zones_result.all()}

        invalid_zones = set(role_in.zone_ids) - valid_zones
        if invalid_zones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid zone IDs for this exhibition: {invalid_zones}",
            )

        zone_ids_str = [str(z) for z in role_in.zone_ids]

    # Create role assignment
    role = UserExhibitionRole(
        user_id=role_in.user_id,
        exhibition_id=exhibition_id,
        role=role_in.role,
        zone_ids=zone_ids_str,
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)

    return ExhibitionRoleRead(
        id=role.id,
        user_id=role.user_id,
        exhibition_id=role.exhibition_id,
        role=role.role,
        zone_ids=role.zone_ids,
        user_email=user.email,
        user_full_name=user.full_name,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.patch("/{exhibition_id}/roles/{role_id}", response_model=ExhibitionRoleRead)
async def update_exhibition_role(
    exhibition_id: UUID,
    role_id: UUID,
    role_in: ExhibitionRoleUpdate,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a role assignment (e.g., change role or update PARTNER zone_ids).

    Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.
    """
    # Get existing role
    result = await db.execute(
        select(UserExhibitionRole, User.email, User.full_name)
        .join(User, UserExhibitionRole.user_id == User.id)
        .where(
            UserExhibitionRole.id == role_id,
            UserExhibitionRole.exhibition_id == exhibition_id,
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found",
        )

    role, email, full_name = row

    # Update role if provided
    if role_in.role is not None:
        role.role = role_in.role

    # Update zone_ids if provided
    if role_in.zone_ids is not None:
        # Validate zones belong to exhibition
        if role_in.zone_ids:
            zones_result = await db.execute(
                select(Zone.id).where(
                    Zone.id.in_(role_in.zone_ids),
                    Zone.exhibition_id == exhibition_id,
                )
            )
            valid_zones = {row[0] for row in zones_result.all()}
            invalid_zones = set(role_in.zone_ids) - valid_zones
            if invalid_zones:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid zone IDs for this exhibition: {invalid_zones}",
                )
            role.zone_ids = [str(z) for z in role_in.zone_ids]
        else:
            role.zone_ids = None

    # Validate PARTNER has zones
    if role.role == ExhibitionRole.PARTNER and not role.zone_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PARTNER role requires at least one zone_id",
        )

    await db.flush()
    await db.refresh(role)

    return ExhibitionRoleRead(
        id=role.id,
        user_id=role.user_id,
        exhibition_id=role.exhibition_id,
        role=role.role,
        zone_ids=role.zone_ids,
        user_email=email,
        user_full_name=full_name,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.delete(
    "/{exhibition_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_exhibition_role(
    exhibition_id: UUID,
    role_id: UUID,
    current_user: User = Depends(require_exhibition_organizer),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a role assignment from an exhibition.

    Requires: Exhibition organizer or SUPER_ADMIN/ADMIN.

    Restrictions:
    - Cannot remove yourself
    - Secondary organizers cannot remove the main organizer (first ORGANIZER by created_at)
    - SUPER_ADMIN/ADMIN can remove anyone except themselves
    """
    # Get the role to remove
    result = await db.execute(
        select(UserExhibitionRole).where(
            UserExhibitionRole.id == role_id,
            UserExhibitionRole.exhibition_id == exhibition_id,
        )
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found",
        )

    # Rule 1: Cannot remove yourself
    if role.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the exhibition",
        )

    # Rule 2: Secondary organizers cannot remove the main organizer (creator)
    # SUPER_ADMIN/ADMIN bypass this check
    if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        if role.role == ExhibitionRole.ORGANIZER:
            # Get the exhibition to check created_by_id
            exhibition_result = await db.execute(
                select(Exhibition).where(Exhibition.id == exhibition_id)
            )
            exhibition = exhibition_result.scalar_one_or_none()

            # If the role belongs to the creator, only the creator themselves can remove it
            if exhibition and exhibition.created_by_id and role.user_id == exhibition.created_by_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the main organizer or admins can remove the main organizer",
                )

    await db.delete(role)
