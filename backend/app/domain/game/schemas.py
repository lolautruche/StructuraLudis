"""
Game domain schemas (DTOs).

Pydantic models for GameCategory, Game, GameSession, and Booking.
"""
from datetime import datetime
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
# GameCategory Schemas
# =============================================================================

class GameCategoryBase(BaseModel):
    """Base schema for game categories."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")


class GameCategoryCreate(GameCategoryBase):
    """Schema for creating a game category."""
    pass


class GameCategoryRead(GameCategoryBase):
    """Schema for reading a game category."""
    id: UUID

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
    category_slug: Optional[str] = Field(
        None, description="Game category slug for display"
    )
    zone_name: Optional[str] = Field(
        None, description="Zone name for display"
    )
    game_title: Optional[str] = Field(
        None, description="Game title for display"
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
