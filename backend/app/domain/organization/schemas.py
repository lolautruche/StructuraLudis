"""
Organization domain schemas (DTOs).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
