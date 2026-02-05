"""
Event request domain entity (Issue #92).

Handles self-service event creation requests before they become exhibitions.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import Base, TimestampMixin, EventRequestStatus

if TYPE_CHECKING:
    from app.domain.user.entity import User
    from app.domain.exhibition.entity import Exhibition
    from app.domain.organization.entity import Organization


class EventRequest(Base, TimestampMixin):
    """
    A request to create a new event (Issue #92).

    Users submit event requests which are then reviewed by admins.
    Upon approval, an Organization and Exhibition are created.
    """
    __tablename__ = "event_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[EventRequestStatus] = mapped_column(
        String(20), default=EventRequestStatus.PENDING
    )

    # Event details
    event_title: Mapped[str] = mapped_column(String(255))
    event_slug: Mapped[str] = mapped_column(String(100))
    event_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    event_region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris")

    # Organization details (new org to be created)
    organization_name: Mapped[str] = mapped_column(String(255))
    organization_slug: Mapped[str] = mapped_column(String(100))
    organization_contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organization_legal_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Message from requester to admins
    requester_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Review fields
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    admin_comment: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Result (filled upon approval)
    created_exhibition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="SET NULL"), nullable=True
    )
    created_organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    reviewed_by: Mapped[Optional["User"]] = relationship(foreign_keys=[reviewed_by_id])
    created_exhibition: Mapped[Optional["Exhibition"]] = relationship()
    created_organization: Mapped[Optional["Organization"]] = relationship()

    __table_args__ = (
        Index("ix_event_requests_status", "status"),
        Index("ix_event_requests_requester_id", "requester_id"),
        Index("ix_event_requests_event_city", "event_city"),
        Index("ix_event_requests_event_region", "event_region"),
        Index("ix_event_requests_event_start_date", "event_start_date"),
    )
