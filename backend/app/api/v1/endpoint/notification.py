"""
Notification API endpoints.

Provides user notification management.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.domain.notification.schemas import (
    NotificationRead,
    NotificationMarkRead,
    NotificationMarkReadResponse,
    NotificationListResponse,
)
from app.domain.user.entity import User
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_my_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List current user's notifications.

    Returns notifications in reverse chronological order (newest first).
    """
    service = NotificationService(db)

    notifications, total, unread_count = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return NotificationListResponse(
        notifications=[NotificationRead.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    body: NotificationMarkRead,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark specific notifications as read.
    """
    service = NotificationService(db)

    updated = await service.mark_notifications_read(
        user_id=current_user.id,
        notification_ids=body.notification_ids,
    )

    await db.commit()

    return NotificationMarkReadResponse(updated_count=updated)


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all notifications as read.
    """
    service = NotificationService(db)

    updated = await service.mark_all_read(user_id=current_user.id)

    await db.commit()

    return NotificationMarkReadResponse(updated_count=updated)


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the count of unread notifications.

    Useful for displaying a badge/counter in the UI.
    """
    service = NotificationService(db)

    _, _, unread_count = await service.get_user_notifications(
        user_id=current_user.id,
        limit=0,
    )

    return {"unread_count": unread_count}