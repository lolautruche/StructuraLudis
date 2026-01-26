"""
User domain schemas (DTOs).

Pydantic models for User management.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.shared.entity import GlobalRole


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
    last_login: Optional[datetime] = None
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
