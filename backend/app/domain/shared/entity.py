"""
Shared domain entities: Base class, mixins, and enums.

Analogous to a Doctrine MappedSuperclass or Trait in Symfony.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class TimestampMixin:
    """
    Mixin providing created_at and updated_at timestamps.

    Similar to Gedmo Timestampable in Symfony/Doctrine.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class UUIDMixin:
    """Mixin providing a UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


# ============================================================================
# Enums
# ============================================================================

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