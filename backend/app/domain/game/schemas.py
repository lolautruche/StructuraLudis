"""
Game domain schemas (DTOs).

Pydantic models for GameCategory, Game, GameSession, and Booking.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.shared.entity import (
    GameComplexity,
    SessionStatus,
    ParticipantRole,
    BookingStatus,
)


# =============================================================================
# i18n Type
# =============================================================================

# Type alias for i18n JSONB fields: {"en": "...", "fr": "...", ...}
I18nField = Optional[dict[str, str]]


# =============================================================================
# GameCategory Schemas
# =============================================================================

class GameCategoryBase(BaseModel):
    """Base schema for game categories."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")


class GameCategoryCreate(GameCategoryBase):
    """Schema for creating a game category."""
    name_i18n: I18nField = Field(
        None,
        description="Translations for name: {'en': '...', 'fr': '...'}"
    )


class GameCategoryUpdate(BaseModel):
    """Schema for updating a game category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    name_i18n: I18nField = Field(
        None,
        description="Translations for name: {'en': '...', 'fr': '...'}"
    )


class GameCategoryRead(GameCategoryBase):
    """Schema for reading a game category."""
    id: UUID
    name_i18n: I18nField = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Game Schemas
# =============================================================================

class GameBase(BaseModel):
    """Base schema for games."""
    title: str = Field(..., min_length=1, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    complexity: GameComplexity = Field(default=GameComplexity.INTERMEDIATE)
    min_players: int = Field(..., ge=1, le=100)
    max_players: int = Field(..., ge=1, le=100)

    @model_validator(mode="after")
    def validate_players(self):
        if self.min_players > self.max_players:
            raise ValueError("min_players cannot exceed max_players")
        return self


class GameCreate(GameBase):
    """Schema for creating a game."""
    category_id: UUID
    external_provider_id: Optional[str] = Field(None, max_length=100)


class GameRead(GameBase):
    """Schema for reading a game."""
    id: UUID
    category_id: UUID
    external_provider_id: Optional[str] = None
    # GROG fields (#55)
    external_provider: Optional[str] = None
    external_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    themes: Optional[List[str]] = None
    last_synced_at: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# GameSession Schemas
# =============================================================================

class GameSessionBase(BaseModel):
    """Base schema for game sessions."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="en", max_length=10)
    min_age: Optional[int] = Field(None, ge=0, le=99)
    max_players_count: int = Field(..., ge=1, le=100)
    safety_tools: Optional[List[str]] = None
    is_accessible_disability: bool = False
    scheduled_start: datetime
    scheduled_end: datetime

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_start >= self.scheduled_end:
            raise ValueError("scheduled_start must be before scheduled_end")
        return self


class GameSessionCreate(GameSessionBase):
    """Schema for creating a game session."""
    exhibition_id: UUID
    time_slot_id: UUID
    game_id: UUID
    provided_by_group_id: Optional[UUID] = None


class GameSessionUpdate(BaseModel):
    """Schema for updating a game session (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    min_age: Optional[int] = Field(None, ge=0, le=99)
    max_players_count: Optional[int] = Field(None, ge=1, le=100)
    safety_tools: Optional[List[str]] = None
    is_accessible_disability: Optional[bool] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    physical_table_id: Optional[UUID] = None


class GameSessionRead(GameSessionBase):
    """Schema for reading a game session."""
    id: UUID
    exhibition_id: UUID
    time_slot_id: UUID
    game_id: UUID
    physical_table_id: Optional[UUID] = None
    provided_by_group_id: Optional[UUID] = None
    provided_by_group_name: Optional[str] = Field(
        None, description="Partner/group name for 'Organized by' display"
    )
    created_by_user_id: UUID
    status: SessionStatus
    rejection_reason: Optional[str] = None
    gm_checked_in_at: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    # Session reporting fields (#35)
    actual_player_count: Optional[int] = None
    table_condition: Optional[str] = None
    end_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GameSessionSubmit(BaseModel):
    """Schema for submitting a session for moderation."""
    pass  # No additional fields needed


class GameSessionModerate(BaseModel):
    """Schema for moderating a session (approve/reject/request_changes)."""
    action: str = Field(..., pattern=r"^(approve|reject|request_changes)$")
    rejection_reason: Optional[str] = Field(None, max_length=1000)
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Comment explaining the moderation decision or requested changes"
    )

    @model_validator(mode="after")
    def validate_rejection(self):
        if self.action == "reject" and not self.rejection_reason:
            raise ValueError("rejection_reason is required when rejecting")
        if self.action == "request_changes" and not self.comment:
            raise ValueError("comment is required when requesting changes")
        return self


# =============================================================================
# Moderation Comment Schemas (#30)
# =============================================================================

class ModerationCommentCreate(BaseModel):
    """Schema for creating a moderation comment."""
    content: str = Field(..., min_length=1, max_length=2000)


class ModerationCommentRead(BaseModel):
    """Schema for reading a moderation comment."""
    id: UUID
    game_session_id: UUID
    user_id: UUID
    user_full_name: Optional[str] = Field(None, description="Author's name for display")
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Booking Schemas
# =============================================================================

class BookingBase(BaseModel):
    """Base schema for bookings."""
    role: ParticipantRole = Field(default=ParticipantRole.PLAYER)


class BookingCreate(BookingBase):
    """Schema for creating a booking (registering to a session)."""
    game_session_id: UUID


class BookingCreateBody(BookingBase):
    """Schema for booking creation request body (session_id from path)."""
    pass


class BookingRead(BookingBase):
    """Schema for reading a booking."""
    id: UUID
    game_session_id: UUID
    user_id: UUID
    status: BookingStatus
    registered_at: datetime
    checked_in_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # User info (populated by endpoint)
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BookingCheckIn(BaseModel):
    """Schema for checking in a booking."""
    pass  # No additional fields needed


class BookingMarkNoShow(BaseModel):
    """Schema for marking a booking as no-show."""
    pass  # No additional fields needed


# =============================================================================
# Session Discovery / Filter Schemas
# =============================================================================

class SessionFilters(BaseModel):
    """
    Filters for session discovery (JS.C1, JS.C6).

    All filters are optional and can be combined.
    """
    # Game type filter
    category_id: Optional[UUID] = Field(
        None, description="Filter by game category (RPG, Board Game, etc.)"
    )

    # Language filter
    language: Optional[str] = Field(
        None, max_length=10, description="Filter by session language (en, fr, etc.)"
    )

    # Accessibility filter
    is_accessible_disability: Optional[bool] = Field(
        None, description="Filter sessions accessible for people with disabilities"
    )

    # Age filter (show sessions accessible to this age)
    max_age_requirement: Optional[int] = Field(
        None, ge=0, le=99,
        description="Show sessions where min_age <= this value (or no age restriction)"
    )

    # Availability filter
    has_available_seats: Optional[bool] = Field(
        None, description="Only show sessions with available seats"
    )

    # Location filters
    zone_id: Optional[UUID] = Field(
        None, description="Filter by zone"
    )
    time_slot_id: Optional[UUID] = Field(
        None, description="Filter by time slot"
    )

    # Time filters
    starts_after: Optional[datetime] = Field(
        None, description="Sessions starting after this time"
    )
    starts_before: Optional[datetime] = Field(
        None, description="Sessions starting before this time"
    )


class SessionSearchResult(GameSessionRead):
    """
    Extended session read with computed fields for discovery.
    """
    available_seats: int = Field(
        ..., description="Number of available seats"
    )
    confirmed_players_count: int = Field(
        ..., description="Number of confirmed players"
    )
    waitlist_count: int = Field(
        0, description="Number of players on the waitlist"
    )
    has_available_seats: bool = Field(
        ..., description="Whether the session has available seats"
    )
    category_slug: Optional[str] = Field(
        None, description="Game category slug for display"
    )
    zone_name: Optional[str] = Field(
        None, description="Zone name for display"
    )
    table_label: Optional[str] = Field(
        None, description="Table label for display"
    )
    game_title: Optional[str] = Field(
        None, description="Game title for display"
    )
    gm_name: Optional[str] = Field(
        None, description="Game Master name for display"
    )


# =============================================================================
# Session Cancellation Schemas (JS.B4)
# =============================================================================

class SessionCancelRequest(BaseModel):
    """Schema for cancelling a session."""
    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Reason for cancellation (will be sent to registered players)"
    )


class AffectedUser(BaseModel):
    """User affected by a cancellation."""
    user_id: UUID
    email: str
    full_name: Optional[str] = None
    locale: Optional[str] = None
    booking_status: BookingStatus


class SessionCancellationResult(BaseModel):
    """Result of a session cancellation."""
    session: GameSessionRead
    affected_users: List[AffectedUser] = Field(
        default_factory=list,
        description="Users who were notified of the cancellation"
    )
    notifications_sent: int = Field(
        0, description="Number of notifications sent"
    )


# =============================================================================
# Session Copy Schemas
# =============================================================================

class SessionCopyRequest(BaseModel):
    """Schema for copying/duplicating a session."""
    time_slot_id: Optional[UUID] = Field(
        None,
        description="Target time slot (uses original if not specified)"
    )
    scheduled_start: Optional[datetime] = Field(
        None,
        description="New start time (required if time_slot_id changes)"
    )
    scheduled_end: Optional[datetime] = Field(
        None,
        description="New end time (required if time_slot_id changes)"
    )
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New title (defaults to 'Copy of [original]')"
    )


# =============================================================================
# Session Reporting Schemas (#35 - JS.B8)
# =============================================================================

class TableCondition(str, Enum):
    """Condition of the table after session ends."""
    CLEAN = "CLEAN"
    NEEDS_CLEANING = "NEEDS_CLEANING"
    DAMAGED = "DAMAGED"


class SessionStartRequest(BaseModel):
    """Schema for starting a session (optional, can be empty)."""
    pass  # actual_start is set automatically


class SessionEndReport(BaseModel):
    """Schema for ending a session with a report."""
    actual_player_count: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Actual number of players who attended"
    )
    table_condition: Optional[TableCondition] = Field(
        None,
        description="Condition of the table after the session"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Any notes about the session (issues, highlights, etc.)"
    )


class SessionReportRead(BaseModel):
    """Schema for reading session report data."""
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    actual_player_count: Optional[int] = None
    table_condition: Optional[str] = None
    end_notes: Optional[str] = None


# =============================================================================
# Series Creation Schemas (#10 - Partner Zone Management)
# =============================================================================

class SeriesCreate(BaseModel):
    """
    Schema for batch creating a series of sessions (Issue #10).

    A "Series" is a set of sessions with the same game and settings,
    scheduled across multiple time slots, rotating through tables.
    Example: "90-minute demo rotation" - same demo runs every slot on different tables.
    """
    exhibition_id: UUID
    game_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="en", max_length=10)
    min_age: Optional[int] = Field(None, ge=0, le=99)
    max_players_count: int = Field(..., ge=1, le=100)
    safety_tools: Optional[List[str]] = None
    is_accessible_disability: bool = False
    provided_by_group_id: Optional[UUID] = Field(
        None, description="Partner group for 'Organized by' display"
    )

    # Series-specific fields
    time_slot_ids: List[UUID] = Field(
        ..., min_length=1, description="Time slots to create sessions for"
    )
    table_ids: List[UUID] = Field(
        ..., min_length=1, description="Tables to rotate through"
    )
    duration_minutes: int = Field(
        ..., ge=15, le=720, description="Session duration in minutes"
    )


class SeriesCreateResponse(BaseModel):
    """Response for series creation."""
    created_count: int = Field(..., description="Number of sessions created")
    sessions: List[GameSessionRead] = Field(
        default_factory=list, description="Created sessions"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings (e.g., 'Table X unavailable at slot Y, skipped')"
    )


class PartnerSessionCreate(BaseModel):
    """
    Schema for creating a single session by a partner (Issue #10).

    Similar to SeriesCreate but for a single session with a single table.
    Auto-validates if the zone has partner_validation_enabled.
    """
    exhibition_id: UUID
    game_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="", max_length=10)
    min_age: Optional[int] = Field(None, ge=0, le=99)
    max_players_count: int = Field(..., ge=1, le=100)
    safety_tools: Optional[List[str]] = None
    is_accessible_disability: bool = False
    provided_by_group_id: Optional[UUID] = Field(
        None, description="Partner group for 'Organized by' display"
    )

    # Single session specific fields
    time_slot_id: UUID = Field(..., description="Time slot for the session")
    table_id: UUID = Field(..., description="Table for the session")
    duration_minutes: int = Field(
        ..., ge=15, le=720, description="Session duration in minutes"
    )
