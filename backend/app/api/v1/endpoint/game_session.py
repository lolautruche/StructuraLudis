"""
GameSession API endpoints.

Session management, workflow, and bookings.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.game.entity import GameSession, Booking
from app.domain.game.schemas import (
    GameSessionCreate,
    GameSessionRead,
    GameSessionUpdate,
    GameSessionModerate,
    BookingCreate,
    BookingCreateBody,
    BookingRead,
    SessionFilters,
    SessionSearchResult,
    SessionCancelRequest,
    SessionCancellationResult,
)
from app.domain.user.entity import User
from app.domain.exhibition.entity import Exhibition
from app.api.deps import get_current_active_user
from app.services.game_session import GameSessionService
from app.services.notification import (
    NotificationService,
    NotificationRecipient,
    NotificationPayload,
    NotificationType,
)

router = APIRouter()


# =============================================================================
# GameSession CRUD
# =============================================================================

@router.get("/", response_model=List[GameSessionRead])
async def list_sessions(
    exhibition_id: UUID,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List game sessions for an exhibition.

    Optional filters:
    - status: filter by session status (DRAFT, PENDING_MODERATION, VALIDATED, etc.)
    """
    query = select(GameSession).where(GameSession.exhibition_id == exhibition_id)

    if status:
        query = query.where(GameSession.status == status)

    query = query.order_by(GameSession.scheduled_start)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search", response_model=List[SessionSearchResult])
async def search_sessions(
    exhibition_id: UUID,
    category_id: Optional[UUID] = Query(None, description="Filter by game category"),
    language: Optional[str] = Query(None, description="Filter by language (en, fr)"),
    is_accessible_disability: Optional[bool] = Query(None, description="Accessibility filter"),
    max_age_requirement: Optional[int] = Query(None, ge=0, le=99, description="Max age requirement"),
    has_available_seats: Optional[bool] = Query(None, description="Only sessions with seats"),
    zone_id: Optional[UUID] = Query(None, description="Filter by zone"),
    time_slot_id: Optional[UUID] = Query(None, description="Filter by time slot"),
    starts_after: Optional[datetime] = Query(None, description="Sessions starting after"),
    starts_before: Optional[datetime] = Query(None, description="Sessions starting before"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search sessions with advanced filters for player discovery (JS.C1, JS.C6).

    Returns validated sessions with availability info.

    Filters:
    - category_id: Game type (RPG, Board Game, etc.)
    - language: Session language (en, fr, etc.)
    - is_accessible_disability: Accessibility for people with disabilities
    - max_age_requirement: Show sessions accessible to this age
    - has_available_seats: Only sessions with available spots
    - zone_id: Physical zone location
    - time_slot_id: Time slot
    - starts_after/starts_before: Time range
    """
    filters = SessionFilters(
        category_id=category_id,
        language=language,
        is_accessible_disability=is_accessible_disability,
        max_age_requirement=max_age_requirement,
        has_available_seats=has_available_seats,
        zone_id=zone_id,
        time_slot_id=time_slot_id,
        starts_after=starts_after,
        starts_before=starts_before,
    )

    service = GameSessionService(db)
    return await service.search_sessions(exhibition_id, filters)


@router.post("/", response_model=GameSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: GameSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new game session.

    The session is created in DRAFT status.
    Submit for moderation using POST /{id}/submit.
    """
    service = GameSessionService(db)
    return await service.create_session(session_in, current_user)


@router.get("/{session_id}", response_model=GameSessionRead)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single game session by ID."""
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    return session


@router.put("/{session_id}", response_model=GameSessionRead)
async def update_session(
    session_id: UUID,
    session_in: GameSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a game session.

    Only draft sessions can be fully edited.
    Validated sessions have limited editable fields.
    """
    service = GameSessionService(db)
    return await service.update_session(session_id, session_in, current_user)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a game session.

    Only draft sessions can be deleted.
    """
    service = GameSessionService(db)
    await service.delete_session(session_id, current_user)


# =============================================================================
# Table Assignment
# =============================================================================

@router.post("/{session_id}/assign-table", response_model=GameSessionRead)
async def assign_table(
    session_id: UUID,
    table_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a physical table to a session.

    Validates:
    - No collision with other sessions on the same table
    - Respects buffer time between sessions

    Requires: Organizer or SUPER_ADMIN.
    """
    service = GameSessionService(db)
    return await service.assign_table(session_id, table_id, current_user)


# =============================================================================
# Workflow Endpoints
# =============================================================================

@router.post("/{session_id}/submit", response_model=GameSessionRead)
async def submit_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a session for moderation.

    Transitions: DRAFT -> PENDING_MODERATION
    """
    service = GameSessionService(db)
    return await service.submit_for_moderation(session_id, current_user)


@router.post("/{session_id}/moderate", response_model=GameSessionRead)
async def moderate_session(
    session_id: UUID,
    moderation: GameSessionModerate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject a session.

    Body: { "action": "approve" } or { "action": "reject", "rejection_reason": "..." }

    Requires: Organizer or SUPER_ADMIN.
    """
    service = GameSessionService(db)
    return await service.moderate_session(session_id, moderation, current_user)


@router.post("/{session_id}/cancel", response_model=SessionCancellationResult)
async def cancel_session(
    session_id: UUID,
    cancel_request: SessionCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a session and notify registered players (JS.B4).

    Cancels the session and all associated bookings.
    Sends notifications to all affected users.

    Can be done by: session creator (GM), organizers, or super admin.

    Body: { "reason": "Reason for cancellation" }
    """
    service = GameSessionService(db)
    session, affected_users = await service.cancel_session(
        session_id, cancel_request.reason, current_user
    )

    # Get exhibition info for notification
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == session.exhibition_id)
    )
    exhibition = exhibition_result.scalar_one()

    # Send notifications
    notifications_sent = 0
    if affected_users:
        notification_service = NotificationService()
        recipients = [
            NotificationRecipient(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
            )
            for user in affected_users
        ]
        payload = NotificationPayload(
            notification_type=NotificationType.SESSION_CANCELLED,
            session_id=session.id,
            session_title=session.title,
            exhibition_title=exhibition.title,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            cancellation_reason=cancel_request.reason,
        )
        notifications_sent = await notification_service.notify_session_cancelled(
            recipients, payload
        )

    return SessionCancellationResult(
        session=session,
        affected_users=affected_users,
        notifications_sent=notifications_sent,
    )


# =============================================================================
# Booking Endpoints
# =============================================================================

@router.get("/{session_id}/bookings", response_model=List[BookingRead])
async def list_bookings(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all bookings for a session."""
    # Check session exists
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    bookings = await db.execute(
        select(Booking)
        .where(Booking.game_session_id == session_id)
        .order_by(Booking.registered_at)
    )
    return bookings.scalars().all()


@router.post("/{session_id}/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    session_id: UUID,
    booking_in: BookingCreateBody,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register for a game session.

    If session is full, booking goes to waitlist.
    """
    # Build full BookingCreate from path + body
    booking_data = BookingCreate(
        game_session_id=session_id,
        role=booking_in.role,
    )
    service = GameSessionService(db)
    return await service.create_booking(booking_data, current_user)


@router.delete("/bookings/{booking_id}", response_model=BookingRead)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a booking.

    May promote someone from waitlist.
    """
    service = GameSessionService(db)
    return await service.cancel_booking(booking_id, current_user)


@router.post("/bookings/{booking_id}/check-in", response_model=BookingRead)
async def check_in_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check in a booking.

    Can be done by: booking owner, session creator, or organizer.
    """
    service = GameSessionService(db)
    return await service.check_in_booking(booking_id, current_user)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingRead)
async def mark_no_show(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a booking as no-show.

    Frees up a spot and may promote someone from waitlist.

    Can be done by: session creator (GM) or organizer.
    """
    service = GameSessionService(db)
    return await service.mark_no_show(booking_id, current_user)
