"""
Organization domain entities.

Contains: Organization, UserGroup, GroupPermission
"""
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import Base, TimestampMixin, UserGroupType

if TYPE_CHECKING:
    from app.domain.user.entity import UserGroupMembership
    from app.domain.exhibition.entity import Exhibition


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    legal_registration_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user_groups: Mapped[List["UserGroup"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    exhibitions: Mapped[List["Exhibition"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class UserGroup(Base, TimestampMixin):
    """A group within an organization (staff, exhibitor, association, etc.)."""
    __tablename__ = "user_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[UserGroupType] = mapped_column(String(50))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="user_groups")
    memberships: Mapped[List["UserGroupMembership"]] = relationship(
        back_populates="user_group", cascade="all, delete-orphan"
    )
    permissions: Mapped[List["GroupPermission"]] = relationship(
        back_populates="user_group", cascade="all, delete-orphan"
    )


class GroupPermission(Base):
    """Permission granted to a UserGroup on a specific resource."""
    __tablename__ = "group_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE")
    )
    resource: Mapped[str] = mapped_column(String(100))  # e.g. 'table', 'exhibition'
    action: Mapped[str] = mapped_column(String(50))  # e.g. 'create', 'approve'

    # Relationships
    user_group: Mapped["UserGroup"] = relationship(back_populates="permissions")