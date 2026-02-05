"""
Notification service layer.

Handles sending notifications to users via multiple channels (email, push, in-app).
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import EmailMessage, get_email_backend
from app.core.templates import (
    render_booking_confirmed,
    render_session_cancelled,
    render_waitlist_promoted,
    render_session_reminder,
    render_new_player_registration,
    render_booking_cancelled,
    render_player_cancelled,
    render_waitlist_cancelled,
    render_session_approved,
    render_session_rejected,
    render_changes_requested,
    render_exhibition_unregistered,
    render_event_request_approved,
    render_event_request_rejected,
    render_event_request_changes,
    render_event_request_submitted,
)
from app.domain.notification.entity import Notification
from app.domain.notification.schemas import NotificationType, NotificationChannel

logger = logging.getLogger(__name__)


@dataclass
class NotificationRecipient:
    """Recipient of a notification."""
    user_id: UUID
    email: str
    full_name: Optional[str] = None
    locale: str = "en"


@dataclass
class SessionNotificationContext:
    """Context data for session-related notifications."""
    session_id: UUID
    session_title: str
    exhibition_id: UUID
    exhibition_title: str
    scheduled_start: datetime
    scheduled_end: datetime
    location: Optional[str] = None
    table_number: Optional[str] = None
    gm_name: Optional[str] = None
    cancellation_reason: Optional[str] = None
    # For booking notifications
    player_name: Optional[str] = None
    players_registered: Optional[int] = None
    max_players: Optional[int] = None


class NotificationService:
    """
    Service for sending notifications to users.

    Supports multiple channels:
    - Email (via configurable backend)
    - Push (via Firebase Cloud Messaging)
    - In-App (stored in database)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_backend = None

    @property
    def email_backend(self):
        """Lazy-load email backend."""
        if self._email_backend is None:
            self._email_backend = get_email_backend()
        return self._email_backend

    async def _create_notification_record(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        subject: str,
        body: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> Notification:
        """Create a notification record in the database."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type.value,
            channel=channel.value,
            subject=subject,
            body=body,
            context=context,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def _send_email(
        self,
        recipient: NotificationRecipient,
        subject: str,
        html_body: str,
        notification: Optional[Notification] = None,
    ) -> bool:
        """Send an email and update notification record."""
        if not settings.EMAIL_ENABLED:
            logger.info(f"Email disabled, would send to {recipient.email}: {subject}")
            return True

        message = EmailMessage(
            to_email=recipient.email,
            to_name=recipient.full_name,
            subject=subject,
            body_html=html_body,
        )

        success = await self.email_backend.send(message)

        if notification:
            notification.email_sent = success
            notification.email_sent_at = datetime.now(timezone.utc) if success else None
            if not success:
                notification.email_error = "Failed to send"
            await self.db.flush()

        return success

    async def _send_push(
        self,
        recipient: NotificationRecipient,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Send a push notification via Firebase Cloud Messaging."""
        if not settings.PUSH_NOTIFICATIONS_ENABLED:
            logger.info(f"Push disabled, would send to {recipient.user_id}: {title}")
            return True

        # TODO: Implement Firebase push notifications
        # This requires:
        # 1. Firebase service account credentials
        # 2. User device tokens stored in DB
        # 3. firebase-admin SDK
        logger.warning("Push notifications not yet implemented")
        return False

    async def notify_booking_confirmed(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that their booking is confirmed.

        Channels: Email, In-App
        """
        subject, html_body = render_booking_confirmed(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            gm_name=context.gm_name,
            location=context.location,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your booking for {context.session_title} is confirmed.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_session_cancelled(
        self,
        recipients: List[NotificationRecipient],
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> int:
        """
        Notify users that a session has been cancelled.

        Channels: Email, In-App, Push (high priority)

        Returns:
            Number of notifications sent
        """
        sent_count = 0

        for recipient in recipients:
            subject, html_body = render_session_cancelled(
                locale=recipient.locale,
                session_title=context.session_title,
                exhibition_title=context.exhibition_title,
                scheduled_start=context.scheduled_start,
                cancellation_reason=context.cancellation_reason,
                action_url=action_url,
            )

            # Create in-app notification
            notification = await self._create_notification_record(
                user_id=recipient.user_id,
                notification_type=NotificationType.SESSION_CANCELLED,
                channel=NotificationChannel.EMAIL,
                subject=subject,
                body=f"Session '{context.session_title}' has been cancelled.",
                context={
                    "session_id": str(context.session_id),
                    "reason": context.cancellation_reason,
                },
            )

            # Send email
            if await self._send_email(recipient, subject, html_body, notification):
                sent_count += 1

            # Also send push notification (high priority)
            await self._send_push(
                recipient,
                title="Session Cancelled",
                body=f"{context.session_title} has been cancelled",
                data={"session_id": str(context.session_id)},
            )

        return sent_count

    async def notify_waitlist_promoted(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that they've been promoted from waitlist.

        Channels: Email, In-App, Push (high priority)
        """
        subject, html_body = render_waitlist_promoted(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            location=context.location,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.WAITLIST_PROMOTED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"You've been promoted from waitlist for {context.session_title}!",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        email_sent = await self._send_email(recipient, subject, html_body, notification)

        # Also send push notification (high priority)
        await self._send_push(
            recipient,
            title="You're in!",
            body=f"A spot opened up for {context.session_title}",
            data={"session_id": str(context.session_id)},
        )

        return email_sent

    async def notify_session_reminder(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Send a session reminder notification.

        Channels: Email, Push
        """
        subject, html_body = render_session_reminder(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            location=context.location,
            table_number=context.table_number,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_REMINDER,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Reminder: {context.session_title} starts soon!",
            context={
                "session_id": str(context.session_id),
            },
        )

        # Send email
        email_sent = await self._send_email(recipient, subject, html_body, notification)

        # Also send push notification
        await self._send_push(
            recipient,
            title="Session Starting Soon",
            body=f"{context.session_title} starts soon!",
            data={"session_id": str(context.session_id)},
        )

        return email_sent

    async def notify_gm_new_player(
        self,
        gm_recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a GM that a new player has registered.

        Channels: Email, In-App
        """
        subject, html_body = render_new_player_registration(
            locale=gm_recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            player_name=context.player_name or "Unknown",
            players_registered=context.players_registered or 0,
            max_players=context.max_players or 0,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=gm_recipient.user_id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"{context.player_name} has registered for {context.session_title}.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(gm_recipient, subject, html_body, notification)

    async def notify_booking_cancelled_to_player(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a player that their booking has been cancelled.

        Channels: Email, In-App
        """
        subject, html_body = render_booking_cancelled(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_CANCELLED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your booking for {context.session_title} has been cancelled.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_waitlist_cancelled_to_player(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a player that they've been removed from the waitlist.

        Channels: Email, In-App
        """
        subject, html_body = render_waitlist_cancelled(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_CANCELLED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"You have been removed from the waitlist for {context.session_title}.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_gm_player_cancelled(
        self,
        gm_recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a GM that a player has cancelled their registration.

        Channels: Email, In-App
        """
        subject, html_body = render_player_cancelled(
            locale=gm_recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            player_name=context.player_name or "Unknown",
            players_registered=context.players_registered or 0,
            max_players=context.max_players or 0,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=gm_recipient.user_id,
            notification_type=NotificationType.SESSION_CANCELLED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"{context.player_name} has cancelled their registration for {context.session_title}.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(gm_recipient, subject, html_body, notification)

    # =========================================================================
    # Moderation Notifications
    # =========================================================================

    async def notify_session_approved(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a session proposer that their session has been approved.

        Channels: Email, In-App
        """
        subject, html_body = render_session_approved(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_APPROVED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your session '{context.session_title}' has been approved!",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_session_rejected(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        rejection_reason: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a session proposer that their session has been rejected.

        Channels: Email, In-App
        """
        subject, html_body = render_session_rejected(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            rejection_reason=rejection_reason,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_REJECTED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your session '{context.session_title}' was not approved.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
                "reason": rejection_reason,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_changes_requested(
        self,
        recipient: NotificationRecipient,
        context: SessionNotificationContext,
        comment: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a session proposer that changes have been requested.

        Channels: Email, In-App
        """
        subject, html_body = render_changes_requested(
            locale=recipient.locale,
            session_title=context.session_title,
            exhibition_title=context.exhibition_title,
            scheduled_start=context.scheduled_start,
            comment=comment,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.CHANGES_REQUESTED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Changes have been requested for your session '{context.session_title}'.",
            context={
                "session_id": str(context.session_id),
                "exhibition_id": str(context.exhibition_id),
                "comment": comment,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    # =========================================================================
    # Exhibition Registration Notifications (Issue #77)
    # =========================================================================

    async def notify_exhibition_unregistered(
        self,
        recipient: NotificationRecipient,
        exhibition_title: str,
        booking_count: int = 0,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that they have unregistered from an exhibition.

        Channels: Email, In-App
        """
        subject, html_body = render_exhibition_unregistered(
            locale=recipient.locale,
            exhibition_title=exhibition_title,
            booking_count=booking_count,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_CANCELLED,  # Reuse type for now
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your registration for {exhibition_title} has been cancelled.",
            context={
                "exhibition_title": exhibition_title,
                "booking_count": booking_count,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    # =========================================================================
    # In-App Notification Management
    # =========================================================================

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Notification], int, int]:
        """
        Get notifications for a user.

        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        # Base query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        # Get total count
        count_query = select(func.count()).select_from(
            select(Notification).where(Notification.user_id == user_id).subquery()
        )
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get unread count
        unread_query = select(func.count()).select_from(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).subquery()
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total_count, unread_count

    async def mark_notifications_read(
        self,
        user_id: UUID,
        notification_ids: List[UUID],
    ) -> int:
        """
        Mark notifications as read.

        Returns:
            Number of notifications updated
        """
        now = datetime.now(timezone.utc)

        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=now)
        )

        result = await self.db.execute(stmt)
        return result.rowcount

    async def mark_all_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.

        Returns:
            Number of notifications updated
        """
        now = datetime.now(timezone.utc)

        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=now)
        )

        result = await self.db.execute(stmt)
        return result.rowcount

    # =========================================================================
    # Event Request Notifications (Issue #92)
    # =========================================================================

    async def notify_event_request_approved(
        self,
        recipient: NotificationRecipient,
        event_title: str,
        exhibition_slug: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that their event request has been approved.

        Channels: Email, In-App
        """
        locale = recipient.locale or "en"
        if not action_url:
            action_url = f"{settings.FRONTEND_URL}/{locale}/exhibitions/{exhibition_slug}"

        subject, html_body = render_event_request_approved(
            locale=locale,
            event_title=event_title,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_APPROVED,  # Reuse type
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your event request '{event_title}' has been approved!",
            context={
                "event_title": event_title,
                "exhibition_slug": exhibition_slug,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_event_request_rejected(
        self,
        recipient: NotificationRecipient,
        event_title: str,
        admin_comment: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that their event request has been rejected.

        Channels: Email, In-App
        """
        locale = recipient.locale or "en"
        subject, html_body = render_event_request_rejected(
            locale=locale,
            event_title=event_title,
            admin_comment=admin_comment,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.SESSION_REJECTED,  # Reuse type
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Your event request '{event_title}' was not approved.",
            context={
                "event_title": event_title,
                "reason": admin_comment,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_event_request_changes(
        self,
        recipient: NotificationRecipient,
        event_title: str,
        admin_comment: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that changes have been requested for their event request.

        Channels: Email, In-App
        """
        locale = recipient.locale or "en"
        if not action_url:
            action_url = f"{settings.FRONTEND_URL}/{locale}/my/event-requests"

        subject, html_body = render_event_request_changes(
            locale=locale,
            event_title=event_title,
            admin_comment=admin_comment,
            action_url=action_url,
        )

        # Create in-app notification
        notification = await self._create_notification_record(
            user_id=recipient.user_id,
            notification_type=NotificationType.CHANGES_REQUESTED,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=f"Changes have been requested for your event '{event_title}'.",
            context={
                "event_title": event_title,
                "comment": admin_comment,
            },
        )

        # Send email
        return await self._send_email(recipient, subject, html_body, notification)

    async def notify_event_request_submitted(
        self,
        request,  # EventRequest - avoid circular import
        is_resubmission: bool = False,
    ) -> int:
        """
        Notify admins that a new event request has been submitted.

        Channels: Email

        Args:
            request: The event request
            is_resubmission: If True, this is a resubmission after changes were requested

        Returns:
            Number of notifications sent
        """
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole

        # Get all admins
        result = await self.db.execute(
            select(User).where(
                User.global_role.in_([GlobalRole.ADMIN, GlobalRole.SUPER_ADMIN]),
                User.is_active == True,
            )
        )
        admins = result.scalars().all()

        sent_count = 0
        for admin in admins:
            admin_locale = admin.locale or "en"
            action_url = f"{settings.FRONTEND_URL}/{admin_locale}/admin/event-requests/{request.id}"

            subject, html_body = render_event_request_submitted(
                locale=admin_locale,
                event_title=request.event_title,
                organization_name=request.organization_name,
                requester_name=request.requester.full_name if request.requester else "Unknown",
                requester_email=request.requester.email if request.requester else "unknown@example.com",
                action_url=action_url,
                is_resubmission=is_resubmission,
            )

            recipient = NotificationRecipient(
                user_id=admin.id,
                email=admin.email,
                full_name=admin.full_name,
                locale=admin.locale,
            )

            if await self._send_email(recipient, subject, html_body):
                sent_count += 1

        return sent_count

    async def notify_event_request_confirmation(
        self,
        request,  # EventRequest - avoid circular import
        action_url: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> bool:
        """
        Send confirmation email to the requester that their request was submitted.

        Channels: Email

        Args:
            request: The event request
            action_url: Optional URL to include in the email
            locale: Optional locale override (uses requester.locale if not provided)

        Returns:
            True if email was sent successfully
        """
        from app.core.templates import render_event_request_confirmation

        requester = request.requester
        if not requester:
            return False

        # Use provided locale, fall back to requester's locale, then default to "en"
        locale = locale or requester.locale or "en"
        if not action_url:
            action_url = f"{settings.FRONTEND_URL}/{locale}/my/event-requests"

        subject, html_body = render_event_request_confirmation(
            locale=locale,
            event_title=request.event_title,
            organization_name=request.organization_name,
            action_url=action_url,
        )

        recipient = NotificationRecipient(
            user_id=requester.id,
            email=requester.email,
            full_name=requester.full_name,
            locale=locale,
        )

        return await self._send_email(recipient, subject, html_body)