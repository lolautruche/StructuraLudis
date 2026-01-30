"""
Notification domain schemas (DTOs).

Pydantic models for Notification API input/output.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationType(str, Enum):
    """Types of notifications."""
    SESSION_CANCELLED = "session_cancelled"
    SESSION_REMINDER = "session_reminder"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    WAITLIST_PROMOTED = "waitlist_promoted"
    MODERATION_COMMENT = "moderation_comment"
    SESSION_APPROVED = "session_approved"
    SESSION_REJECTED = "session_rejected"
    CHANGES_REQUESTED = "changes_requested"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationRead(BaseModel):
    """Schema for reading a notification."""
    id: UUID
    notification_type: str
    channel: str
    subject: str
    body: Optional[str] = None
    context: Optional[dict] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="List of notification IDs to mark as read"
    )


class NotificationMarkReadResponse(BaseModel):
    """Response for marking notifications as read."""
    updated_count: int


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""
    notifications: list[NotificationRead]
    total: int
    unread_count: int