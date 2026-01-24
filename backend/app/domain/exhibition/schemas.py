"""
Exhibition domain schemas (DTOs).

Similar to Symfony's DTO classes or API Platform's ApiResource schemas.
These are Pydantic models used for API input/output validation.
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


class ExhibitionCreate(ExhibitionBase):
    """Schema for creating a new exhibition."""
    organization_id: UUID
    slug: str = Field(..., min_length=1, max_length=100)


class ExhibitionUpdate(BaseModel):
    """Schema for updating an exhibition (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    status: Optional[ExhibitionStatus] = None


class ExhibitionRead(ExhibitionBase):
    """Schema for reading an exhibition (includes id and timestamps)."""
    id: UUID
    organization_id: UUID
    slug: str
    status: ExhibitionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Enable ORM mode: allows creating from SQLAlchemy models
    # Similar to Symfony's serializer groups
    model_config = ConfigDict(from_attributes=True)