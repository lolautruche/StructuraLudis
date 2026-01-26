"""
GameSession API endpoints.

Session management, workflow, and bookings.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
)
from app.domain.user.entity import User
from app.api.deps import get_current_active_user
from app.services.game_session import GameSessionService

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
