"""
User API endpoints.

User profile and dashboard (JS.B6).
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.user.entity import User
from app.domain.user.schemas import (
    UserRead,
    UserProfileUpdate,
    MySessionSummary,
    MyBookingSummary,
    UserAgenda,
)
from app.domain.game.entity import GameSession, Booking
from app.domain.exhibition.entity import Exhibition, Zone, PhysicalTable
from app.domain.shared.entity import SessionStatus, BookingStatus
from app.api.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# User Profile
# =============================================================================

@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)

    return current_user


# =============================================================================
# User Dashboard / Agenda (JS.B6)
# =============================================================================

@router.get("/me/sessions", response_model=List[MySessionSummary])
async def list_my_sessions(
    exhibition_id: UUID = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List sessions created by the current user (as GM).

    Optionally filter by exhibition.
    """
    query = (
        select(
            GameSession,
            Exhibition.title.label("exhibition_title"),
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
        )
        .join(Exhibition, GameSession.exhibition_id == Exhibition.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(GameSession.created_by_user_id == current_user.id)
        .order_by(GameSession.scheduled_start)
    )

    if exhibition_id:
        query = query.where(GameSession.exhibition_id == exhibition_id)

    result = await db.execute(query)
    rows = result.all()

    sessions = []
    for row in rows:
        session = row[0]
        exhibition_title = row[1]
        zone_name = row[2]
        table_label = row[3]

        # Count confirmed and waitlist bookings
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session.id)
            .group_by(Booking.status)
        )
        counts = {row[0]: row[1] for row in booking_counts.fetchall()}

        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        sessions.append(MySessionSummary(
            id=session.id,
            title=session.title,
            exhibition_id=session.exhibition_id,
            exhibition_title=exhibition_title,
            status=session.status,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            zone_name=zone_name,
            table_label=table_label,
            max_players_count=session.max_players_count,
            confirmed_players=confirmed,
            waitlist_count=waitlist,
        ))

    return sessions


@router.get("/me/bookings", response_model=List[MyBookingSummary])
async def list_my_bookings(
    exhibition_id: UUID = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List bookings for the current user (as player).

    Optionally filter by exhibition.
    """
    query = (
        select(
            Booking,
            GameSession.title.label("session_title"),
            GameSession.scheduled_start,
            GameSession.scheduled_end,
            GameSession.exhibition_id,
            Exhibition.title.label("exhibition_title"),
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            User.full_name.label("gm_name"),
        )
        .join(GameSession, Booking.game_session_id == GameSession.id)
        .join(Exhibition, GameSession.exhibition_id == Exhibition.id)
        .join(User, GameSession.created_by_user_id == User.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(Booking.user_id == current_user.id)
        .order_by(GameSession.scheduled_start)
    )

    if exhibition_id:
        query = query.where(GameSession.exhibition_id == exhibition_id)

    result = await db.execute(query)
    rows = result.all()

    bookings = []
    for row in rows:
        booking = row[0]
        bookings.append(MyBookingSummary(
            id=booking.id,
            game_session_id=booking.game_session_id,
            session_title=row[1],
            exhibition_id=row[4],
            exhibition_title=row[5],
            status=booking.status,
            role=booking.role,
            scheduled_start=row[2],
            scheduled_end=row[3],
            zone_name=row[6],
            table_label=row[7],
            gm_name=row[8],
        ))

    return bookings


@router.get("/me/agenda/{exhibition_id}", response_model=UserAgenda)
async def get_my_agenda(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get combined agenda for an exhibition (JS.B6).

    Returns all sessions (as GM) and bookings (as player) with
    conflict detection for overlapping schedules.
    """
    # Get exhibition
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = exhibition_result.scalar_one_or_none()
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Get my sessions
    sessions_query = (
        select(
            GameSession,
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
        )
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(
            GameSession.created_by_user_id == current_user.id,
            GameSession.exhibition_id == exhibition_id,
            GameSession.status.notin_([SessionStatus.CANCELLED, SessionStatus.REJECTED]),
        )
        .order_by(GameSession.scheduled_start)
    )
    sessions_result = await db.execute(sessions_query)
    session_rows = sessions_result.all()

    my_sessions = []
    session_times = []  # For conflict detection

    for row in session_rows:
        session = row[0]

        # Count bookings
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session.id)
            .group_by(Booking.status)
        )
        counts = {r[0]: r[1] for r in booking_counts.fetchall()}
        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        my_sessions.append(MySessionSummary(
            id=session.id,
            title=session.title,
            exhibition_id=session.exhibition_id,
            exhibition_title=exhibition.title,
            status=session.status,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            zone_name=row[1],
            table_label=row[2],
            max_players_count=session.max_players_count,
            confirmed_players=confirmed,
            waitlist_count=waitlist,
        ))

        session_times.append({
            "type": "gm",
            "title": session.title,
            "start": session.scheduled_start,
            "end": session.scheduled_end,
        })

    # Get my bookings
    bookings_query = (
        select(
            Booking,
            GameSession.title.label("session_title"),
            GameSession.scheduled_start,
            GameSession.scheduled_end,
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            User.full_name.label("gm_name"),
        )
        .join(GameSession, Booking.game_session_id == GameSession.id)
        .join(User, GameSession.created_by_user_id == User.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(
            Booking.user_id == current_user.id,
            GameSession.exhibition_id == exhibition_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED,
                BookingStatus.CHECKED_IN,
                BookingStatus.WAITING_LIST,
            ]),
        )
        .order_by(GameSession.scheduled_start)
    )
    bookings_result = await db.execute(bookings_query)
    booking_rows = bookings_result.all()

    my_bookings = []
    for row in booking_rows:
        booking = row[0]
        my_bookings.append(MyBookingSummary(
            id=booking.id,
            game_session_id=booking.game_session_id,
            session_title=row[1],
            exhibition_id=exhibition_id,
            exhibition_title=exhibition.title,
            status=booking.status,
            role=booking.role,
            scheduled_start=row[2],
            scheduled_end=row[3],
            zone_name=row[4],
            table_label=row[5],
            gm_name=row[6],
        ))

        session_times.append({
            "type": "player",
            "title": row[1],
            "start": row[2],
            "end": row[3],
        })

    # Detect conflicts
    conflicts = []
    for i, t1 in enumerate(session_times):
        for t2 in session_times[i + 1:]:
            # Check overlap
            if t1["start"] < t2["end"] and t1["end"] > t2["start"]:
                conflicts.append(
                    f"Conflict: '{t1['title']}' ({t1['type']}) overlaps with "
                    f"'{t2['title']}' ({t2['type']})"
                )

    return UserAgenda(
        user_id=current_user.id,
        exhibition_id=exhibition_id,
        exhibition_title=exhibition.title,
        my_sessions=my_sessions,
        my_bookings=my_bookings,
        conflicts=conflicts,
    )
