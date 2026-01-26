"""
Exhibition domain schemas (DTOs).

Pydantic models used for API input/output validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared.entity import ExhibitionStatus


class ExhibitionBase(BaseModel):
    """Base schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    timezone: str = Field(default="UTC", max_length=50)
    grace_period_minutes: int = Field(default=15, ge=0, le=120)


class ExhibitionCreate(ExhibitionBase):
    """Schema for creating a new exhibition."""
    organization_id: UUID
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class ExhibitionUpdate(BaseModel):
    """Schema for updating an exhibition (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    timezone: Optional[str] = Field(None, max_length=50)
    grace_period_minutes: Optional[int] = Field(None, ge=0, le=120)
    status: Optional[ExhibitionStatus] = None


class ExhibitionRead(ExhibitionBase):
    """Schema for reading an exhibition (includes id and timestamps)."""
    id: UUID
    organization_id: UUID
    slug: str
    status: ExhibitionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
