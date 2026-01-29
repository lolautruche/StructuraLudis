"""
Exhibition domain entities.

Contains: Exhibition, TimeSlot, Zone, PhysicalTable
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
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
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Location
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    # Configuration (Issue #6, #12)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=15)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    status: Mapped[ExhibitionStatus] = mapped_column(
        String(20), default=ExhibitionStatus.DRAFT
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="exhibitions")
    time_slots: Mapped[List["TimeSlot"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    zones: Mapped[List["Zone"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    safety_tools: Mapped[List["SafetyTool"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    game_sessions: Mapped[List["GameSession"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )


class TimeSlot(Base, TimestampMixin):
    """
    A time slot within an exhibition during which games can be scheduled.

    Important: All times should be stored in UTC.
    """
    __tablename__ = "time_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Duration and buffer constraints (Issue #1)
    max_duration_minutes: Mapped[int] = mapped_column(Integer, default=240)  # 4h default
    buffer_time_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="time_slots")
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

    # Partner delegation (Issue #2, #3 - JS.A4)
    delegated_to_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="zones")
    delegated_to_group: Mapped[Optional["UserGroup"]] = relationship()
    physical_tables: Mapped[List["PhysicalTable"]] = relationship(
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
