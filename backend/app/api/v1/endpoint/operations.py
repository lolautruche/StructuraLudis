"""
Operations API endpoints.

Real-time operations: available tables, auto-cancellation, GM check-in.
"""
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition.schemas import PhysicalTableRead
from app.domain.game.schemas import GameSessionRead
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole
from app.api.deps import get_current_active_user
from app.services.operations import OperationsService

router = APIRouter()


@router.get("/exhibitions/{exhibition_id}/available-tables", response_model=List[PhysicalTableRead])
async def get_available_tables(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get tables available for immediate use (pop-up games).

    Returns tables that are not currently occupied by any session.
    Useful for spontaneous games when someone wants to run a game right now.
    """
    service = OperationsService(db)
    return await service.get_available_tables(exhibition_id)


@router.post("/exhibitions/{exhibition_id}/auto-cancel", response_model=List[GameSessionRead])
async def auto_cancel_sessions(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-cancel sessions where GM hasn't checked in after grace period.

    This endpoint can be called manually by organizers or triggered by a background job.

    Requires: Organizer or SUPER_ADMIN.
    """
    if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers can trigger auto-cancellation",
        )

    service = OperationsService(db)
    cancelled = await service.auto_cancel_sessions(exhibition_id)

    return cancelled


@router.post("/sessions/{session_id}/gm-check-in", response_model=GameSessionRead)
async def gm_check_in(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check in the GM for a session.

    Marks the session as IN_PROGRESS and records the check-in time.
    This prevents the session from being auto-cancelled.

    Can be done by: session creator (GM) or organizer.
    """
    from sqlalchemy import select
    from app.domain.game.entity import GameSession

    # Get session to check permissions
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    # Check permission - GM or organizer
    can_check_in = (
        session.created_by_user_id == current_user.id
        or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]
    )
    if not can_check_in:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the GM or organizers can check in for a session",
        )

    service = OperationsService(db)
    updated_session = await service.gm_check_in(session_id)

    return updated_session