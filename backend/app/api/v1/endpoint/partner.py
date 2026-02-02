"""
Partner API endpoints (Issue #10).

Dedicated endpoints for partners to manage their delegated zones.
"""
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition.entity import Exhibition, Zone, PhysicalTable, TimeSlot
from app.domain.game.entity import GameSession, Game, Booking
from app.domain.game.schemas import (
    GameSessionRead,
    SeriesCreate,
    SeriesCreateResponse,
)
from app.domain.user.entity import User, UserExhibitionRole
from app.domain.shared.entity import (
    GlobalRole,
    ExhibitionRole,
    SessionStatus,
    BookingStatus,
)
from app.api.deps import get_current_active_user
from app.api.deps.permissions import can_manage_zone
from app.services.game_session import GameSessionService

router = APIRouter()


# =============================================================================
# Partner Zone Access
# =============================================================================

async def _get_partner_zone_ids(
    user: User,
    exhibition_id: UUID,
    db: AsyncSession,
) -> List[UUID]:
    """Get the zone IDs that the partner user can manage for an exhibition."""
    # Super admins and admins can manage all zones
    if user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        result = await db.execute(
            select(Zone.id).where(Zone.exhibition_id == exhibition_id)
        )
        return list(result.scalars().all())

    # Get user's exhibition role
    result = await db.execute(
        select(UserExhibitionRole).where(
            UserExhibitionRole.user_id == user.id,
            UserExhibitionRole.exhibition_id == exhibition_id,
        )
    )
    role_assignment = result.scalar_one_or_none()

    if not role_assignment:
        return []

    # Organizers can manage all zones
    if role_assignment.role == ExhibitionRole.ORGANIZER:
        result = await db.execute(
            select(Zone.id).where(Zone.exhibition_id == exhibition_id)
        )
        return list(result.scalars().all())

    # Partners can only manage their assigned zones
    if role_assignment.zone_ids:
        return [UUID(zone_id) for zone_id in role_assignment.zone_ids]

    return []


@router.get("/exhibitions/{exhibition_id}/zones")
async def list_partner_zones(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List zones that the current user can manage as a partner.

    Returns zones with stats (table count, pending sessions count).
    """
    zone_ids = await _get_partner_zone_ids(current_user, exhibition_id, db)

    if not zone_ids:
        return []

    # Fetch zones with stats
    result = await db.execute(
        select(Zone).where(Zone.id.in_(zone_ids)).order_by(Zone.name)
    )
    zones = result.scalars().all()

    zones_with_stats = []
    for zone in zones:
        # Count tables
        table_count_result = await db.execute(
            select(func.count(PhysicalTable.id)).where(
                PhysicalTable.zone_id == zone.id
            )
        )
        table_count = table_count_result.scalar() or 0

        # Count pending sessions (sessions on tables in this zone)
        pending_count_result = await db.execute(
            select(func.count(GameSession.id))
            .join(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
            .where(
                PhysicalTable.zone_id == zone.id,
                GameSession.status == SessionStatus.PENDING_MODERATION,
            )
        )
        pending_count = pending_count_result.scalar() or 0

        # Count validated sessions
        validated_count_result = await db.execute(
            select(func.count(GameSession.id))
            .join(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
            .where(
                PhysicalTable.zone_id == zone.id,
                GameSession.status == SessionStatus.VALIDATED,
            )
        )
        validated_count = validated_count_result.scalar() or 0

        zones_with_stats.append({
            "id": zone.id,
            "exhibition_id": zone.exhibition_id,
            "name": zone.name,
            "description": zone.description,
            "type": zone.type,
            "partner_validation_enabled": zone.partner_validation_enabled,
            "table_count": table_count,
            "pending_sessions_count": pending_count,
            "validated_sessions_count": validated_count,
        })

    return zones_with_stats


@router.get("/exhibitions/{exhibition_id}/sessions")
async def list_partner_sessions(
    exhibition_id: UUID,
    zone_id: Optional[UUID] = Query(None, description="Filter by zone"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (PENDING_MODERATION, VALIDATED, etc.)"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List sessions in zones the current partner can manage.

    Returns sessions with computed fields (seats, game title, etc.).
    """
    zone_ids = await _get_partner_zone_ids(current_user, exhibition_id, db)

    if not zone_ids:
        return []

    # Filter to specific zone if requested
    if zone_id:
        if zone_id not in zone_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this zone",
            )
        zone_ids = [zone_id]

    # Build query for sessions in partner's zones
    query = (
        select(GameSession, Game.title.label("game_title"), Zone.name.label("zone_name"))
        .join(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .join(Zone, PhysicalTable.zone_id == Zone.id)
        .join(Game, GameSession.game_id == Game.id)
        .where(
            GameSession.exhibition_id == exhibition_id,
            Zone.id.in_(zone_ids),
        )
    )

    # Apply status filter
    if status_filter:
        try:
            status_enum = SessionStatus(status_filter)
            query = query.where(GameSession.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    query = query.order_by(GameSession.scheduled_start)

    result = await db.execute(query)
    rows = result.all()

    # Build response with computed fields
    sessions = []
    for session, game_title, zone_name in rows:
        # Count confirmed bookings
        booking_count = await db.execute(
            select(func.count(Booking.id)).where(
                Booking.game_session_id == session.id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            )
        )
        confirmed_count = booking_count.scalar() or 0
        available_seats = max(0, session.max_players_count - confirmed_count)

        # Get table label
        table_result = await db.execute(
            select(PhysicalTable.label).where(PhysicalTable.id == session.physical_table_id)
        )
        table_label = table_result.scalar_one_or_none()

        sessions.append({
            "id": session.id,
            "exhibition_id": session.exhibition_id,
            "time_slot_id": session.time_slot_id,
            "game_id": session.game_id,
            "physical_table_id": session.physical_table_id,
            "title": session.title,
            "description": session.description,
            "language": session.language,
            "min_age": session.min_age,
            "max_players_count": session.max_players_count,
            "status": session.status,
            "scheduled_start": session.scheduled_start,
            "scheduled_end": session.scheduled_end,
            "created_at": session.created_at,
            # Computed fields
            "game_title": game_title,
            "zone_name": zone_name,
            "table_label": table_label,
            "available_seats": available_seats,
            "confirmed_players_count": confirmed_count,
        })

    return sessions


# =============================================================================
# Series Creation (Batch Session Creation)
# =============================================================================

@router.post("/sessions/batch", response_model=SeriesCreateResponse)
async def create_series(
    data: SeriesCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a series of sessions (Issue #10).

    Creates multiple sessions with the same game/settings across
    the specified time slots, rotating through the provided tables.

    Requires: Partner with access to all specified tables' zones,
    or exhibition organizer.
    """
    # Validate exhibition exists
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == data.exhibition_id)
    )
    exhibition = exhibition_result.scalar_one_or_none()
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Validate game exists
    game_result = await db.execute(
        select(Game).where(Game.id == data.game_id)
    )
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    # Get tables and validate access
    tables_result = await db.execute(
        select(PhysicalTable, Zone)
        .join(Zone, PhysicalTable.zone_id == Zone.id)
        .where(PhysicalTable.id.in_(data.table_ids))
    )
    table_zone_pairs = tables_result.all()

    if len(table_zone_pairs) != len(data.table_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more tables not found",
        )

    # Validate user can manage all zones containing the tables
    for table, zone in table_zone_pairs:
        if not await can_manage_zone(current_user, zone, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have access to zone '{zone.name}'",
            )

    # Validate time slots
    slots_result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.id.in_(data.time_slot_ids),
            TimeSlot.exhibition_id == data.exhibition_id,
        )
    )
    time_slots = {slot.id: slot for slot in slots_result.scalars().all()}

    if len(time_slots) != len(data.time_slot_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more time slots not found or don't belong to this exhibition",
        )

    # Create sessions for each combination of slot × table
    created_sessions = []
    warnings = []
    tables = [table for table, zone in table_zone_pairs]

    service = GameSessionService(db)

    for slot_id in data.time_slot_ids:
        slot = time_slots[slot_id]

        for table in tables:
            # Calculate session times within the slot
            session_start = slot.start_time
            session_end = session_start + timedelta(minutes=data.duration_minutes)

            # Check if session fits within time slot
            if session_end > slot.end_time:
                warnings.append(
                    f"Session would exceed slot '{slot.name}' end time, skipped"
                )
                continue

            # Check for table collision
            collision = await service._check_table_collision(
                table_id=table.id,
                scheduled_start=session_start,
                scheduled_end=session_end,
                buffer_minutes=slot.buffer_time_minutes,
            )

            if collision:
                warnings.append(
                    f"Table '{table.label}' has conflict at slot '{slot.name}', skipped"
                )
                continue

            # Create the session with descriptive title
            session_title = f"{data.title} ({slot.name} - {table.label})"

            session = GameSession(
                exhibition_id=data.exhibition_id,
                time_slot_id=slot_id,
                game_id=data.game_id,
                physical_table_id=table.id,
                provided_by_group_id=data.provided_by_group_id,
                created_by_user_id=current_user.id,
                title=session_title,
                description=data.description,
                language=data.language,
                min_age=data.min_age,
                max_players_count=data.max_players_count,
                safety_tools=data.safety_tools,
                is_accessible_disability=data.is_accessible_disability,
                scheduled_start=session_start,
                scheduled_end=session_end,
                status=SessionStatus.DRAFT,
            )

            db.add(session)
            await db.flush()
            await db.refresh(session)
            created_sessions.append(session)

    # Build response
    session_reads = []
    for session in created_sessions:
        session_reads.append(GameSessionRead(
            id=session.id,
            exhibition_id=session.exhibition_id,
            time_slot_id=session.time_slot_id,
            game_id=session.game_id,
            physical_table_id=session.physical_table_id,
            provided_by_group_id=session.provided_by_group_id,
            created_by_user_id=session.created_by_user_id,
            title=session.title,
            description=session.description,
            language=session.language,
            min_age=session.min_age,
            max_players_count=session.max_players_count,
            safety_tools=session.safety_tools,
            is_accessible_disability=session.is_accessible_disability,
            status=session.status,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ))

    return SeriesCreateResponse(
        created_count=len(created_sessions),
        sessions=session_reads,
        warnings=warnings,
    )
