"""
User domain schemas (DTOs).

Pydantic models for User management.
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.shared.entity import GlobalRole, SessionStatus, BookingStatus


class UserBase(BaseModel):
    """Base schema for users."""
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: str = Field(default="en", max_length=10)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    """Schema for reading a user."""
    id: UUID
    global_role: str  # String from DB, matches GlobalRole values
    is_active: bool
    email_verified: bool = False  # Email verification status (Issue #73)
    birth_date: Optional[date] = None  # For age-restricted sessions
    last_login: Optional[datetime] = None
    privacy_accepted_at: Optional[datetime] = None  # GDPR consent timestamp
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating a user (self-update)."""
    full_name: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's global role (Super Admin only)."""
    global_role: GlobalRole


class UserStatusUpdate(BaseModel):
    """Schema for activating/deactivating a user (Super Admin only)."""
    is_active: bool


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile including birth_date."""
    full_name: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    birth_date: Optional[date] = None


# =============================================================================
# User Dashboard Schemas (JS.B6)
# =============================================================================

class MySessionSummary(BaseModel):
    """Summary of a session created by the user (as GM)."""
    id: UUID
    title: str
    exhibition_id: UUID
    exhibition_title: str
    status: SessionStatus
    scheduled_start: datetime
    scheduled_end: datetime
    zone_name: Optional[str] = None
    table_label: Optional[str] = None
    max_players_count: int
    confirmed_players: int
    waitlist_count: int

    model_config = ConfigDict(from_attributes=True)


class MyBookingSummary(BaseModel):
    """Summary of a booking for the user (as player)."""
    id: UUID
    game_session_id: UUID
    session_title: str
    exhibition_id: UUID
    exhibition_title: str
    status: BookingStatus
    role: str
    scheduled_start: datetime
    scheduled_end: datetime
    zone_name: Optional[str] = None
    table_label: Optional[str] = None
    gm_name: Optional[str] = None
    max_players_count: int = 0
    confirmed_players: int = 0
    waitlist_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SessionConflict(BaseModel):
    """A scheduling conflict between two sessions."""
    session1_title: str
    session1_role: str  # "gm" or "player"
    session2_title: str
    session2_role: str  # "gm" or "player"


class UserAgenda(BaseModel):
    """
    Combined agenda for a user (JS.B6).

    Shows both sessions they're running (as GM) and sessions
    they're registered for (as player).
    """
    user_id: UUID
    exhibition_id: UUID
    exhibition_title: str
    my_sessions: List[MySessionSummary] = Field(
        default_factory=list,
        description="Sessions I'm running as GM"
    )
    my_bookings: List[MyBookingSummary] = Field(
        default_factory=list,
        description="Sessions I'm registered for as player"
    )
    conflicts: List[SessionConflict] = Field(
        default_factory=list,
        description="Scheduling conflicts between sessions"
    )

    model_config = ConfigDict(from_attributes=True)
