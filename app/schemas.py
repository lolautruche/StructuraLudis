import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

# We can reuse the Enums from models.py or redefine them if we want strict decoupling
from app.models import UserGroupType, GroupRole, ExhibitionStatus


# --- Shared Properties ---
class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Organization Schemas ---
class OrganizationBase(BaseModel):
    name: str
    slug: str
    legal_registration_number: Optional[str] = None
    contact_email: Optional[EmailStr] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization (POST request)"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization (PATCH request)"""
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    legal_registration_number: Optional[str] = None
    # Slug is typically not updatable or requires specific logic


class OrganizationResponse(OrganizationBase, TimestampSchema):
    """Schema for returning an organization (API Response)"""
    id: uuid.UUID

    # This tells Pydantic to read data from the SQLAlchemy ORM object
    model_config = ConfigDict(from_attributes=True)


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    locale: str = "en"


class UserCreate(UserBase):
    """Input schema containing the raw password"""
    password: str


class UserResponse(UserBase, TimestampSchema):
    """Output schema EXCLUDING the password"""
    id: uuid.UUID
    is_active: bool
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Token Schema (Example) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None