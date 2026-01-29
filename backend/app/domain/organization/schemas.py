"""
Organization domain schemas (DTOs).
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.shared.entity import UserGroupType, GroupRole


# =============================================================================
# Organization Schemas
# =============================================================================

class OrganizationBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    legal_registration_number: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_registration_number: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None


class OrganizationRead(OrganizationBase):
    """Schema for reading an organization."""
    id: UUID
    slug: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# UserGroup Schemas
# =============================================================================

class UserGroupBase(BaseModel):
    """Base schema for user groups."""
    name: str = Field(..., min_length=1, max_length=255)
    type: UserGroupType = Field(default=UserGroupType.ASSOCIATION)
    is_public: bool = Field(default=False)


class UserGroupCreate(UserGroupBase):
    """Schema for creating a user group."""
    organization_id: UUID


class UserGroupUpdate(BaseModel):
    """Schema for updating a user group."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[UserGroupType] = None
    is_public: Optional[bool] = None


class UserGroupRead(UserGroupBase):
    """Schema for reading a user group."""
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# UserGroupMembership Schemas (#31)
# =============================================================================

class GroupMemberAdd(BaseModel):
    """Schema for adding a member to a group."""
    user_id: UUID
    group_role: GroupRole = Field(default=GroupRole.MEMBER)


class GroupMemberUpdate(BaseModel):
    """Schema for updating a member's role in a group."""
    group_role: GroupRole


class GroupMemberRead(BaseModel):
    """Schema for reading a group member."""
    id: UUID
    user_id: UUID
    user_email: str = Field(description="User's email for display")
    user_full_name: Optional[str] = Field(None, description="User's full name")
    group_role: GroupRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserGroupWithMembers(UserGroupRead):
    """Schema for reading a user group with its members."""
    members: List[GroupMemberRead] = Field(default_factory=list)
