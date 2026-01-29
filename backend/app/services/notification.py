"""
Notification service layer.

Handles sending notifications to users (email, push, etc.).
This is a stub implementation that logs notifications for now.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications."""
    SESSION_CANCELLED = "session_cancelled"
    SESSION_REMINDER = "session_reminder"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    WAITLIST_PROMOTED = "waitlist_promoted"


@dataclass
class NotificationRecipient:
    """Recipient of a notification."""
    user_id: UUID
    email: str
    full_name: Optional[str] = None


@dataclass
class NotificationPayload:
    """Payload for a notification."""
    notification_type: NotificationType
    session_id: UUID
    session_title: str
    exhibition_title: str
    scheduled_start: datetime
    scheduled_end: datetime
    cancellation_reason: Optional[str] = None
    gm_name: Optional[str] = None


class NotificationService:
    """
    Service for sending notifications to users.

    This is a stub implementation that logs notifications.
    In production, this would integrate with:
    - Email service (SendGrid, AWS SES, etc.)
    - Push notifications (Firebase, etc.)
    - In-app notifications (WebSocket/SSE)
    """

    async def notify_session_cancelled(
        self,
        recipients: List[NotificationRecipient],
        payload: NotificationPayload,
    ) -> int:
        """
        Notify users that a session has been cancelled.

        Args:
            recipients: List of users to notify
            payload: Notification details

        Returns:
            Number of notifications sent
        """
        for recipient in recipients:
            logger.info(
                "NOTIFICATION [%s] to %s <%s>: Session '%s' scheduled for %s has been cancelled. Reason: %s",
                payload.notification_type.value,
                recipient.full_name or "User",
                recipient.email,
                payload.session_title,
                payload.scheduled_start.isoformat(),
                payload.cancellation_reason or "Not specified",
            )

        # TODO: Implement actual notification sending
        # - Queue emails for batch sending
        # - Send push notifications
        # - Create in-app notification records

        return len(recipients)

    async def notify_waitlist_promoted(
        self,
        recipient: NotificationRecipient,
        payload: NotificationPayload,
    ) -> bool:
        """
        Notify a user that they've been promoted from waitlist.

        Args:
            recipient: User to notify
            payload: Notification details

        Returns:
            True if notification was sent
        """
        logger.info(
            "NOTIFICATION [%s] to %s <%s>: You've been promoted from waitlist for session '%s' on %s!",
            NotificationType.WAITLIST_PROMOTED.value,
            recipient.full_name or "User",
            recipient.email,
            payload.session_title,
            payload.scheduled_start.isoformat(),
        )

        # TODO: Implement actual notification sending

        return True

    async def notify_booking_confirmed(
        self,
        recipient: NotificationRecipient,
        payload: NotificationPayload,
    ) -> bool:
        """
        Notify a user that their booking is confirmed.

        Args:
            recipient: User to notify
            payload: Notification details

        Returns:
            True if notification was sent
        """
        logger.info(
            "NOTIFICATION [%s] to %s <%s>: Booking confirmed for session '%s' on %s",
            NotificationType.BOOKING_CONFIRMED.value,
            recipient.full_name or "User",
            recipient.email,
            payload.session_title,
            payload.scheduled_start.isoformat(),
        )

        # TODO: Implement actual notification sending

        return True