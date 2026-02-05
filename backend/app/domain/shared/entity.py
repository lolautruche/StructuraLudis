"""
Shared domain entities: Base class, mixins, and enums.
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
    """Mixin providing created_at and updated_at timestamps."""
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

# --- Platform-wide ---

class GlobalRole(str, Enum):
    """
    Platform-wide roles for users (Issue #12, #99).

    - SUPER_ADMIN: Platform owner, can promote/demote ADMIN
    - ADMIN: Platform administrator, admin access but cannot manage other admins
    - USER: Regular user
    """
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class ExhibitionRole(str, Enum):
    """
    Event-scoped roles for users within an exhibition (Issue #99).

    - ORGANIZER: Manages the exhibition (config, moderation, zones)
    - PARTNER: Delegated access to specific zone(s)
    """
    ORGANIZER = "ORGANIZER"
    PARTNER = "PARTNER"


# --- Organization & Groups ---

class UserGroupType(str, Enum):
    """Type of user group within an organization."""
    STAFF = "STAFF"
    ASSOCIATION = "ASSOCIATION"
    EXHIBITOR = "EXHIBITOR"
    PLAYER_CLUB = "PLAYER_CLUB"


class GroupRole(str, Enum):
    """Role of a user within a group."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


# --- Exhibition ---

class ExhibitionStatus(str, Enum):
    """
    Publication status of an exhibition.

    - DRAFT: Not yet published, only visible to organizers/admins
    - PUBLISHED: Publicly visible
    - SUSPENDED: Temporarily hidden from public (e.g., issues to resolve)
    - ARCHIVED: Past event, kept for reference but not active
    """
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


# --- Physical Topology ---

class ZoneType(str, Enum):
    """Type of physical zone (Issue #2)."""
    RPG = "RPG"
    BOARD_GAME = "BOARD_GAME"
    WARGAME = "WARGAME"
    TCG = "TCG"
    DEMO = "DEMO"
    MIXED = "MIXED"


class PhysicalTableStatus(str, Enum):
    """Availability status of a physical table."""
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    MAINTENANCE = "MAINTENANCE"


# --- Game & Sessions ---

class GameComplexity(str, Enum):
    """Complexity level of a game."""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    EXPERT = "EXPERT"


class SafetyTool(str, Enum):
    """Safety tools for game sessions (Issue #4)."""
    X_CARD = "X_CARD"
    LINES_AND_VEILS = "LINES_AND_VEILS"
    OPEN_DOOR = "OPEN_DOOR"
    CONSENT_CHECKLIST = "CONSENT_CHECKLIST"
    SCRIPT_CHANGE = "SCRIPT_CHANGE"


class SessionStatus(str, Enum):
    """Workflow status for game sessions (Issue #4, #30)."""
    DRAFT = "DRAFT"
    PENDING_MODERATION = "PENDING_MODERATION"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"  # Moderator requested changes (#30)
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


# --- Bookings ---

class ParticipantRole(str, Enum):
    """Role of a participant in a game session."""
    GM = "GM"
    PLAYER = "PLAYER"
    ASSISTANT = "ASSISTANT"
    SPECTATOR = "SPECTATOR"


class BookingStatus(str, Enum):
    """Status of a booking/registration (Issue #5)."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    WAITING_LIST = "WAITING_LIST"
    CHECKED_IN = "CHECKED_IN"
    ATTENDED = "ATTENDED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"


# --- Event Requests (Issue #92) ---

class EventRequestStatus(str, Enum):
    """
    Status of an event creation request (Issue #92).

    - PENDING: Submitted and awaiting admin review
    - CHANGES_REQUESTED: Admin requested modifications
    - APPROVED: Approved, exhibition and organization created
    - REJECTED: Rejected by admin
    """
    PENDING = "PENDING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"