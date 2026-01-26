"""
User domain entities.

Contains: User, UserGroupMembership
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import Base, TimestampMixin, GroupRole, GlobalRole

if TYPE_CHECKING:
    from app.domain.organization.entity import UserGroup
    from app.domain.media.entity import Media


class User(Base, TimestampMixin):
    """Application user."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Platform-wide role (Issue #12)
    global_role: Mapped[GlobalRole] = mapped_column(
        String(20), default=GlobalRole.USER
    )

    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    memberships: Mapped[List["UserGroupMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    media: Mapped[List["Media"]] = relationship(
        back_populates="uploaded_by_user", cascade="all, delete-orphan"
    )


class UserGroupMembership(Base):
    """
    Association between User and UserGroup with a role.

    This is a many-to-many with extra data (group_role, joined_at).
    """
    __tablename__ = "user_group_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE")
    )
    group_role: Mapped[GroupRole] = mapped_column(String(20))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memberships")
    user_group: Mapped["UserGroup"] = relationship(back_populates="memberships")