"""
Exhibition domain entities.

Contains: Exhibition, TimeSlot, Zone, PhysicalTable, ExhibitionRegistration
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import (
    Base,
    TimestampMixin,
    ExhibitionStatus,
    ZoneType,
    PhysicalTableStatus,
)

if TYPE_CHECKING:
    from app.domain.organization.entity import Organization, UserGroup
    from app.domain.game.entity import GameSession
    from app.domain.user.entity import User


class Exhibition(Base, TimestampMixin):
    """
    A convention or event where game sessions are organized.

    This is a core aggregate root in the domain.
    """
    __tablename__ = "exhibitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    # Creator of the exhibition (main organizer) - Issue #99
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # i18n fields (#34) - JSONB with locale keys: {"en": "...", "fr": "..."}
    title_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Location
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    # Configuration (Issue #6, #12, #39)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=15)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Registration control (Issue #39 - JS.03)
    is_registration_open: Mapped[bool] = mapped_column(default=False)
    registration_opens_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_closes_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Language settings (Issue #39 - JS.03)
    primary_language: Mapped[str] = mapped_column(String(10), default="en")
    secondary_languages: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Registration requirement (Issue #77)
    requires_registration: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[ExhibitionStatus] = mapped_column(
        String(20), default=ExhibitionStatus.DRAFT
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="exhibitions")
    created_by: Mapped[Optional["User"]] = relationship()
    zones: Mapped[List["Zone"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    safety_tools: Mapped[List["SafetyTool"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    game_sessions: Mapped[List["GameSession"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    registrations: Mapped[List["ExhibitionRegistration"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )


class TimeSlot(Base, TimestampMixin):
    """
    A time slot within a zone during which games can be scheduled.

    Each zone can have its own schedule with different time slots (Issue #105).
    Important: All times should be stored in UTC.
    """
    __tablename__ = "time_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Duration and buffer constraints (Issue #1)
    max_duration_minutes: Mapped[int] = mapped_column(Integer, default=240)  # 4h default
    buffer_time_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # Relationships
    zone: Mapped["Zone"] = relationship(back_populates="time_slots")
    game_sessions: Mapped[List["GameSession"]] = relationship(
        back_populates="time_slot"
    )


class Zone(Base, TimestampMixin):
    """
    A physical area within an exhibition that can be delegated to a partner.

    Examples: RPG Area, Board Game Zone, Publisher Booth
    """
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[ZoneType] = mapped_column(String(20), default=ZoneType.MIXED)

    # i18n fields (#34) - JSONB with locale keys: {"en": "...", "fr": "..."}
    name_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Partner delegation (Issue #2, #3 - JS.A4)
    delegated_to_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True
    )

    # Session moderation (Issue #10 - JS.D3)
    # When True, public session proposals require moderation
    # Partner sessions are always auto-validated regardless of this setting
    moderation_required: Mapped[bool] = mapped_column(default=True)

    # Public session proposals (Issue #10)
    # When True, public users can propose sessions on tables in this zone
    # When False, only partners/organizers can create sessions
    allow_public_proposals: Mapped[bool] = mapped_column(default=False)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="zones")
    delegated_to_group: Mapped[Optional["UserGroup"]] = relationship()
    physical_tables: Mapped[List["PhysicalTable"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )
    time_slots: Mapped[List["TimeSlot"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class SafetyTool(Base, TimestampMixin):
    """
    A safety tool available for game sessions in an exhibition.

    Examples: X-Card, Lines & Veils, Script Change, etc.
    Organizers define the available tools, GMs select which ones they'll use.
    """
    __tablename__ = "safety_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50))  # For programmatic access
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Link to docs
    is_required: Mapped[bool] = mapped_column(default=False)  # Must be used by all sessions
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # i18n fields (#34) - JSONB with locale keys: {"en": "...", "fr": "..."}
    name_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description_i18n: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="safety_tools")


class PhysicalTable(Base, TimestampMixin):
    """
    A physical table resource within a zone.

    Represents the actual furniture that can host game sessions.
    """
    __tablename__ = "physical_tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(50))  # e.g., "A1", "Table 12"
    capacity: Mapped[int] = mapped_column(Integer, default=6)
    status: Mapped[PhysicalTableStatus] = mapped_column(
        String(20), default=PhysicalTableStatus.AVAILABLE
    )

    # Relationships
    zone: Mapped["Zone"] = relationship(back_populates="physical_tables")
    game_sessions: Mapped[List["GameSession"]] = relationship(
        back_populates="physical_table"
    )


class ExhibitionRegistration(Base):
    """
    Player registration to an exhibition (Issue #77).

    Users can register to exhibitions to track participation
    and optionally be required before booking sessions.
    """
    __tablename__ = "exhibition_registrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship()
    exhibition: Mapped["Exhibition"] = relationship(back_populates="registrations")

    __table_args__ = (
        UniqueConstraint('user_id', 'exhibition_id', name='uq_user_exhibition_registration'),
    )
