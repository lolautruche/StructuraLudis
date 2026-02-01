"""
Exhibition domain schemas (DTOs).

Pydantic models used for API input/output validation.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.shared.entity import (
    ExhibitionStatus as ExhibitionStatusEnum,
    ExhibitionRole,
    ZoneType,
    PhysicalTableStatus,
)


# Type alias for i18n JSONB fields: {"en": "...", "fr": "...", ...}
I18nField = Optional[dict[str, str]]


# =============================================================================
# Exhibition Schemas
# =============================================================================

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

    # Registration control (Issue #39 - JS.03)
    is_registration_open: bool = Field(default=False)
    registration_opens_at: Optional[datetime] = Field(
        None, description="When registrations open for this exhibition"
    )
    registration_closes_at: Optional[datetime] = Field(
        None, description="When registrations close for this exhibition"
    )

    # Language settings (Issue #39 - JS.03)
    primary_language: str = Field(
        default="en", max_length=10, description="Main event language"
    )
    secondary_languages: Optional[List[str]] = Field(
        None, description="Additional supported languages"
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        # Validate registration dates if provided
        if self.registration_opens_at and self.registration_closes_at:
            if self.registration_opens_at >= self.registration_closes_at:
                raise ValueError("registration_opens_at must be before registration_closes_at")
        return self


class ExhibitionCreate(ExhibitionBase):
    """Schema for creating a new exhibition."""
    organization_id: UUID
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    # i18n fields (#34)
    title_i18n: I18nField = Field(None, description="Translations for title")
    description_i18n: I18nField = Field(None, description="Translations for description")


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
    status: Optional[ExhibitionStatusEnum] = None
    # Registration control (Issue #39 - JS.03)
    is_registration_open: Optional[bool] = None
    registration_opens_at: Optional[datetime] = None
    registration_closes_at: Optional[datetime] = None
    # Language settings (Issue #39 - JS.03)
    primary_language: Optional[str] = Field(None, max_length=10)
    secondary_languages: Optional[List[str]] = None
    # i18n fields (#34)
    title_i18n: I18nField = Field(None, description="Translations for title")
    description_i18n: I18nField = Field(None, description="Translations for description")


class ExhibitionRead(ExhibitionBase):
    """Schema for reading an exhibition (includes id and timestamps)."""
    id: UUID
    organization_id: UUID
    slug: str
    status: ExhibitionStatusEnum
    settings: Optional[dict] = None
    address: Optional[str] = None
    # i18n fields (#34)
    title_i18n: I18nField = None
    description_i18n: I18nField = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Permission flag (computed based on authenticated user)
    can_manage: bool = False

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TimeSlot Schemas
# =============================================================================

class TimeSlotBase(BaseModel):
    """Base schema for time slots."""
    name: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    end_time: datetime
    max_duration_minutes: int = Field(default=240, ge=30, le=720)  # 30min to 12h
    buffer_time_minutes: int = Field(default=15, ge=0, le=60)

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")

        # Check max_duration doesn't exceed slot amplitude
        slot_duration = (self.end_time - self.start_time).total_seconds() / 60
        if self.max_duration_minutes > slot_duration:
            raise ValueError(
                f"max_duration_minutes ({self.max_duration_minutes}) cannot exceed "
                f"slot duration ({int(slot_duration)} minutes)"
            )

        return self


class TimeSlotCreate(TimeSlotBase):
    """Schema for creating a time slot."""
    pass


class TimeSlotRead(TimeSlotBase):
    """Schema for reading a time slot."""
    id: UUID
    exhibition_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TimeSlotUpdate(BaseModel):
    """Schema for updating a time slot."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_duration_minutes: Optional[int] = Field(None, ge=30, le=720)
    buffer_time_minutes: Optional[int] = Field(None, ge=0, le=60)

    @model_validator(mode="after")
    def validate_times(self):
        # Only validate if both times are provided
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time")
        return self


# =============================================================================
# Zone Schemas
# =============================================================================

class ZoneBase(BaseModel):
    """Base schema for zones."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: ZoneType = Field(default=ZoneType.MIXED)


class ZoneCreate(ZoneBase):
    """Schema for creating a zone."""
    exhibition_id: UUID
    delegated_to_group_id: Optional[UUID] = None
    # i18n fields (#34)
    name_i18n: I18nField = Field(None, description="Translations for name")
    description_i18n: I18nField = Field(None, description="Translations for description")


class ZoneUpdate(BaseModel):
    """Schema for updating a zone."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    type: Optional[ZoneType] = None
    # i18n fields (#34)
    name_i18n: I18nField = Field(None, description="Translations for name")
    description_i18n: I18nField = Field(None, description="Translations for description")


class ZoneDelegate(BaseModel):
    """Schema for delegating a zone to a partner group."""
    delegated_to_group_id: Optional[UUID] = Field(
        None,
        description="UserGroup ID to delegate zone to. Set to null to remove delegation."
    )


class ZoneRead(ZoneBase):
    """Schema for reading a zone."""
    id: UUID
    exhibition_id: UUID
    delegated_to_group_id: Optional[UUID] = None
    # i18n fields (#34)
    name_i18n: I18nField = None
    description_i18n: I18nField = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# PhysicalTable Schemas
# =============================================================================

class PhysicalTableBase(BaseModel):
    """Base schema for physical tables."""
    label: str = Field(..., min_length=1, max_length=50)
    capacity: int = Field(default=6, ge=1, le=20)
    status: PhysicalTableStatus = Field(default=PhysicalTableStatus.AVAILABLE)


class PhysicalTableCreate(PhysicalTableBase):
    """Schema for creating a physical table."""
    pass


class PhysicalTableRead(PhysicalTableBase):
    """Schema for reading a physical table."""
    id: UUID
    zone_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PhysicalTableUpdate(BaseModel):
    """Schema for updating a physical table."""
    label: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, ge=1, le=20)
    status: Optional[PhysicalTableStatus] = None


class BatchTablesCreate(BaseModel):
    """Schema for batch creating physical tables."""
    prefix: str = Field(default="Table ", max_length=30)
    count: int = Field(..., ge=1, le=200)
    starting_number: int = Field(default=1, ge=1)
    capacity: int = Field(default=6, ge=1, le=20)


class BatchTablesResponse(BaseModel):
    """Response for batch table creation."""
    created_count: int
    tables: List[PhysicalTableRead]


# =============================================================================
# SafetyTool Schemas (JS.A5)
# =============================================================================

class SafetyToolBase(BaseModel):
    """Base schema for safety tools."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = Field(None, max_length=500)
    is_required: bool = Field(default=False)
    display_order: int = Field(default=0, ge=0)


class SafetyToolCreate(SafetyToolBase):
    """Schema for creating a safety tool."""
    exhibition_id: UUID
    # i18n fields (#34)
    name_i18n: I18nField = Field(None, description="Translations for name")
    description_i18n: I18nField = Field(None, description="Translations for description")


class SafetyToolUpdate(BaseModel):
    """Schema for updating a safety tool."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = Field(None, max_length=500)
    is_required: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)
    # i18n fields (#34)
    name_i18n: I18nField = Field(None, description="Translations for name")
    description_i18n: I18nField = Field(None, description="Translations for description")


class SafetyToolRead(SafetyToolBase):
    """Schema for reading a safety tool."""
    id: UUID
    exhibition_id: UUID
    # i18n fields (#34)
    name_i18n: I18nField = None
    description_i18n: I18nField = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SafetyToolBatchCreate(BaseModel):
    """Schema for batch creating common safety tools."""
    exhibition_id: UUID
    include_defaults: bool = Field(
        default=True,
        description="Include common safety tools (X-Card, Lines & Veils, etc.)"
    )


class SafetyToolBatchResponse(BaseModel):
    """Response for batch safety tool creation."""
    created_count: int
    tools: List[SafetyToolRead]


# =============================================================================
# Dashboard Schemas
# =============================================================================

class SessionStatusCount(BaseModel):
    """Count of sessions by status."""
    status: str
    count: int


class ExhibitionDashboard(BaseModel):
    """Dashboard status for an exhibition."""
    exhibition_id: UUID
    total_zones: int
    total_tables: int
    tables_available: int
    tables_occupied: int
    occupation_rate: float = Field(description="Percentage of occupied tables")
    sessions_by_status: List[SessionStatusCount]
    total_sessions: int
    total_bookings: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Exhibition Role Schemas (#99)
# =============================================================================

class ExhibitionRoleCreate(BaseModel):
    """Schema for assigning a role to a user for an exhibition."""
    user_id: UUID = Field(..., description="User to assign the role to")
    role: ExhibitionRole = Field(..., description="ORGANIZER or PARTNER")
    zone_ids: Optional[List[UUID]] = Field(
        None,
        description="Zone IDs this user can manage (required for PARTNER role)"
    )

    @model_validator(mode="after")
    def validate_partner_zones(self) -> "ExhibitionRoleCreate":
        """PARTNER role requires zone_ids."""
        if self.role == ExhibitionRole.PARTNER and not self.zone_ids:
            raise ValueError("PARTNER role requires at least one zone_id")
        return self


class ExhibitionRoleUpdate(BaseModel):
    """Schema for updating a role assignment."""
    role: Optional[ExhibitionRole] = Field(None, description="New role")
    zone_ids: Optional[List[UUID]] = Field(
        None,
        description="Updated zone IDs (for PARTNER role)"
    )


class ExhibitionRoleRead(BaseModel):
    """Schema for reading a role assignment."""
    id: UUID
    user_id: UUID
    exhibition_id: UUID
    role: ExhibitionRole
    zone_ids: Optional[List[str]] = Field(None, description="Zone IDs as strings")
    # User info for display
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
