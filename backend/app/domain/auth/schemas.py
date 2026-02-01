"""
Authentication schemas (DTOs).

Pydantic models for login, registration, and tokens.
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(default=False, description="Keep user logged in for longer")


class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(None, max_length=255)
    accept_privacy_policy: bool = Field(
        ...,
        description="User must accept the privacy policy to register"
    )


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded JWT payload."""
    sub: str  # User ID