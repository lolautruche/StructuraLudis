import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


# Enums
class UserGroupType(str, Enum):
    STAFF = "STAFF"
    ASSOCIATION = "ASSOCIATION"
    EXHIBITOR = "EXHIBITOR"
    PLAYER_CLUB = "PLAYER_CLUB"


class GroupRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class ExhibitionStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class GameComplexity(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    EXPERT = "EXPERT"


class GameTableStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ParticipantRole(str, Enum):
    GM = "GM"
    PLAYER = "PLAYER"
    ASSISTANT = "ASSISTANT"
    SPECTATOR = "SPECTATOR"


class ParticipantStatus(str, Enum):
    REGISTERED = "REGISTERED"
    WAITING_LIST = "WAITING_LIST"
    CANCELLED = "CANCELLED"


# Models

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True)
    legal_registration_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user_groups: Mapped[List["UserGroup"]] = relationship(back_populates="organization")
    exhibitions: Mapped[List["Exhibition"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    locale: Mapped[str] = mapped_column(String, default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    memberships: Mapped[List["UserGroupMembership"]] = relationship(back_populates="user")
    media: Mapped[List["Media"]] = relationship(back_populates="uploaded_by_user")


class UserGroup(Base, TimestampMixin):
    __tablename__ = "user_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String)
    type: Mapped[UserGroupType] = mapped_column(String)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    organization: Mapped["Organization"] = relationship(back_populates="user_groups")
    memberships: Mapped[List["UserGroupMembership"]] = relationship(back_populates="user_group")
    permissions: Mapped[List["GroupPermission"]] = relationship(back_populates="user_group")


class UserGroupMembership(Base):
    __tablename__ = "user_group_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    user_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_groups.id"))
    group_role: Mapped[GroupRole] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="memberships")
    user_group: Mapped["UserGroup"] = relationship(back_populates="memberships")


class GroupPermission(Base):
    __tablename__ = "group_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_groups.id"))
    resource: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)

    user_group: Mapped["UserGroup"] = relationship(back_populates="permissions")


class Exhibition(Base, TimestampMixin):
    __tablename__ = "exhibitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[ExhibitionStatus] = mapped_column(String)

    organization: Mapped["Organization"] = relationship(back_populates="exhibitions")
    time_slots: Mapped[List["TimeSlot"]] = relationship(back_populates="exhibition")
    game_tables: Mapped[List["GameTable"]] = relationship(back_populates="exhibition")


class TimeSlot(Base, TimestampMixin):
    __tablename__ = "time_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exhibitions.id"))
    name: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity_bonus: Mapped[int] = mapped_column(Integer, default=0)

    exhibition: Mapped["Exhibition"] = relationship(back_populates="time_slots")
    game_tables: Mapped[List["GameTable"]] = relationship(back_populates="time_slot")


class GameCategory(Base):
    __tablename__ = "game_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True)

    games: Mapped[List["Game"]] = relationship(back_populates="category")


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_categories.id"))
    title: Mapped[str] = mapped_column(String)
    external_provider_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    complexity: Mapped[GameComplexity] = mapped_column(String)
    min_players: Mapped[int] = mapped_column(Integer)
    max_players: Mapped[int] = mapped_column(Integer)

    category: Mapped["GameCategory"] = relationship(back_populates="games")
    game_tables: Mapped[List["GameTable"]] = relationship(back_populates="game")


class GameTable(Base, TimestampMixin):
    __tablename__ = "game_tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exhibitions.id"))
    time_slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("time_slots.id"))
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id"))
    provided_by_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_groups.id"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String)
    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_players_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[GameTableStatus] = mapped_column(
        String, default=GameTableStatus.PENDING
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    safety_tools: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    is_accessible_disability: Mapped[bool] = mapped_column(Boolean, default=False)

    exhibition: Mapped["Exhibition"] = relationship(back_populates="game_tables")
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="game_tables")
    game: Mapped["Game"] = relationship(back_populates="game_tables")
    provided_by_group: Mapped[Optional["UserGroup"]] = relationship()
    created_by_user: Mapped["User"] = relationship()
    participants: Mapped[List["TableParticipant"]] = relationship(
        back_populates="game_table"
    )


class TableParticipant(Base):
    __tablename__ = "table_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_tables.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role: Mapped[ParticipantRole] = mapped_column(String)
    status: Mapped[ParticipantStatus] = mapped_column(String)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    game_table: Mapped["GameTable"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()


class Media(Base):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(
        String
    )  # USER, EXHIBITION, GAME, ORGANIZATION
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    storage_key: Mapped[str] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    uploaded_by_user: Mapped["User"] = relationship(back_populates="media")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    old_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )