"""
Event request schemas (Issue #92).

Pydantic schemas for event request CRUD operations.
"""
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class EventRequestCreate(BaseModel):
    """Schema for creating an event request (user submission)."""

    # Event details
    event_title: str = Field(..., min_length=1, max_length=255)
    event_description: Optional[str] = None
    event_start_date: datetime
    event_end_date: datetime
    event_location_name: Optional[str] = Field(None, max_length=255)
    event_city: Optional[str] = Field(None, max_length=100)
    event_country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    event_region: Optional[str] = Field(None, max_length=50)
    event_timezone: str = Field(default="Europe/Paris", max_length=50)

    # Organization details
    organization_name: str = Field(..., min_length=1, max_length=255)
    organization_contact_email: Optional[EmailStr] = None

    # Message to admins
    requester_message: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.event_start_date >= self.event_end_date:
            raise ValueError("start_date must be before end_date")
        return self


class EventRequestUpdate(BaseModel):
    """Schema for updating an event request (by user, if CHANGES_REQUESTED)."""

    event_title: Optional[str] = Field(None, min_length=1, max_length=255)
    event_description: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    event_location_name: Optional[str] = Field(None, max_length=255)
    event_city: Optional[str] = Field(None, max_length=100)
    event_country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    event_region: Optional[str] = Field(None, max_length=50)
    event_timezone: Optional[str] = Field(None, max_length=50)
    organization_name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization_contact_email: Optional[EmailStr] = None
    requester_message: Optional[str] = Field(None, max_length=2000)


class EventRequestAdminUpdate(EventRequestUpdate):
    """Schema for admin updates (can modify slugs)."""

    event_slug: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=100)
    organization_slug: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=100)


class EventRequestRead(BaseModel):
    """Schema for reading an event request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    status: str
    event_title: str
    event_slug: str
    event_description: Optional[str]
    event_start_date: datetime
    event_end_date: datetime
    event_location_name: Optional[str]
    event_city: Optional[str]
    event_country_code: Optional[str]
    event_region: Optional[str]
    event_timezone: str
    organization_name: str
    organization_slug: str
    organization_contact_email: Optional[str]
    requester_message: Optional[str]
    admin_comment: Optional[str]
    reviewed_by_id: Optional[UUID]
    reviewed_at: Optional[datetime]
    created_exhibition_id: Optional[UUID]
    created_organization_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    # Joined fields from requester
    requester_email: Optional[str] = None
    requester_name: Optional[str] = None


class EventRequestReview(BaseModel):
    """Schema for reviewing an event request (admin action)."""

    action: Literal["approve", "reject", "request_changes"]
    admin_comment: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_comment(self):
        if self.action in ("reject", "request_changes") and not self.admin_comment:
            raise ValueError("admin_comment required for reject/request_changes")
        return self


class EventRequestListResponse(BaseModel):
    """Schema for listing event requests with pagination metadata."""

    model_config = ConfigDict(from_attributes=True)

    items: list[EventRequestRead]
    total: int
    pending_count: int
