"""
Game domain entities.

Contains: GameCategory, Game, GameTable, TableParticipant
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
    GameTableStatus,
    ParticipantRole,
    ParticipantStatus,
)

if TYPE_CHECKING:
    from app.domain.exhibition.entity import Exhibition, TimeSlot
    from app.domain.organization.entity import UserGroup
    from app.domain.user.entity import User


class GameCategory(Base):
    """
    Category of game (RPG, Board Game, Card Game, LARP, etc.).
    """
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
    A game that can be played at tables.

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
    game_tables: Mapped[List["GameTable"]] = relationship(back_populates="game")


class GameTable(Base, TimestampMixin):
    """
    A scheduled game session at an exhibition.

    Business rules:
    - Must be approved by a MODERATOR or ADMIN of the providing group
    - Participants must meet min_age requirement
    - No schedule conflicts for participants within the same exhibition
    """
    __tablename__ = "game_tables"

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
    provided_by_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_players_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[GameTableStatus] = mapped_column(
        String(20), default=GameTableStatus.PENDING
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    safety_tools: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    is_accessible_disability: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="game_tables")
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="game_tables")
    game: Mapped["Game"] = relationship(back_populates="game_tables")
    provided_by_group: Mapped[Optional["UserGroup"]] = relationship()
    created_by_user: Mapped["User"] = relationship()
    participants: Mapped[List["TableParticipant"]] = relationship(
        back_populates="game_table", cascade="all, delete-orphan"
    )


class TableParticipant(Base):
    """
    A user registered to participate in a game table.
    """
    __tablename__ = "table_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_tables.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    role: Mapped[ParticipantRole] = mapped_column(String(20))
    status: Mapped[ParticipantStatus] = mapped_column(String(20))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    game_table: Mapped["GameTable"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()