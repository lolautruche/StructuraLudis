"""
Game domain entities.

Contains: GameCategory, Game, GameSession, Booking
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import (
    Base,
    TimestampMixin,
    GameComplexity,
    SessionStatus,
    ParticipantRole,
    BookingStatus,
)

if TYPE_CHECKING:
    from app.domain.exhibition.entity import Exhibition, TimeSlot, PhysicalTable
    from app.domain.organization.entity import UserGroup
    from app.domain.user.entity import User


class GameCategory(Base):
    """Category of game (RPG, Board Game, Card Game, LARP, etc.)."""
    __tablename__ = "game_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Relationships
    games: Mapped[List["Game"]] = relationship(back_populates="category")


class Game(Base, TimestampMixin):
    """
    A game that can be played at sessions.

    The external_provider_id allows syncing with external catalogs like GROG.
    """
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_categories.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(255))
    external_provider_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    complexity: Mapped[GameComplexity] = mapped_column(String(20))
    min_players: Mapped[int] = mapped_column(Integer)
    max_players: Mapped[int] = mapped_column(Integer)

    # Relationships
    category: Mapped["GameCategory"] = relationship(back_populates="games")
    game_sessions: Mapped[List["GameSession"]] = relationship(back_populates="game")


class GameSession(Base, TimestampMixin):
    """
    A scheduled game session at an exhibition.

    Distinct from PhysicalTable: this is the logical session (game + time + participants),
    while PhysicalTable is the physical resource where it takes place.

    Business rules:
    - Must be approved by a MODERATOR or ADMIN of the providing group
    - Participants must meet min_age requirement
    - No schedule conflicts for participants within the same exhibition
    """
    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    time_slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("time_slots.id", ondelete="RESTRICT")
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("games.id", ondelete="RESTRICT")
    )

    # Physical resource (Issue #2 - can be assigned later)
    physical_table_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("physical_tables.id", ondelete="SET NULL"), nullable=True
    )

    # Ownership
    provided_by_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )

    # Session details
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_players_count: Mapped[int] = mapped_column(Integer)

    # Safety tools (Issue #4)
    safety_tools: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    is_accessible_disability: Mapped[bool] = mapped_column(Boolean, default=False)

    # Workflow status (Issue #4)
    status: Mapped[SessionStatus] = mapped_column(
        String(20), default=SessionStatus.DRAFT
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Scheduling (Issue #1)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Check-in tracking (Issue #6)
    gm_checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # End-of-session report (Issue #35 - JS.B8)
    actual_player_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    table_condition: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # CLEAN, NEEDS_CLEANING, DAMAGED
    end_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="game_sessions")
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="game_sessions")
    game: Mapped["Game"] = relationship(back_populates="game_sessions")
    physical_table: Mapped[Optional["PhysicalTable"]] = relationship(
        back_populates="game_sessions"
    )
    provided_by_group: Mapped[Optional["UserGroup"]] = relationship()
    created_by_user: Mapped["User"] = relationship()
    bookings: Mapped[List["Booking"]] = relationship(
        back_populates="game_session", cascade="all, delete-orphan"
    )
    moderation_comments: Mapped[List["ModerationComment"]] = relationship(
        back_populates="game_session", cascade="all, delete-orphan"
    )


class ModerationComment(Base, TimestampMixin):
    """
    A comment in the moderation dialogue for a game session (#30).

    Enables two-way communication between session proposer and moderators
    during the approval process.
    """
    __tablename__ = "moderation_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(String(2000))

    # Relationships
    game_session: Mapped["GameSession"] = relationship(back_populates="moderation_comments")
    user: Mapped["User"] = relationship()


class Booking(Base):
    """
    A user's registration/booking for a game session.

    Tracks the full lifecycle: registration -> check-in -> attendance/no-show.
    """
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    role: Mapped[ParticipantRole] = mapped_column(String(20))
    status: Mapped[BookingStatus] = mapped_column(
        String(20), default=BookingStatus.PENDING
    )

    # Timestamps
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    game_session: Mapped["GameSession"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship()
