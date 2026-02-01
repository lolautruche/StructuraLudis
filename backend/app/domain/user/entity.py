"""
User domain entities.

Contains: User, UserGroupMembership
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint

from app.domain.shared.entity import Base, TimestampMixin, GroupRole, GlobalRole, ExhibitionRole
from datetime import date

if TYPE_CHECKING:
    from app.domain.organization.entity import UserGroup
    from app.domain.media.entity import Media
    from app.domain.exhibition.entity import Exhibition


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
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # GDPR: Privacy policy consent (Issue #47)
    privacy_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Email verification (Issue #73)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    email_verification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Pending email change (Issue #60)
    pending_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pending_email_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    pending_email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset (Issue #60)
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    password_reset_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def get_age(self) -> Optional[int]:
        """Calculate age from birth_date."""
        if not self.birth_date:
            return None
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age
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
    exhibition_roles: Mapped[List["UserExhibitionRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
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


class UserExhibitionRole(Base, TimestampMixin):
    """
    Event-scoped role assignment (Issue #99).

    Links a user to an exhibition with a specific role.
    For PARTNER role, zone_ids specifies which zones they manage.
    """
    __tablename__ = "user_exhibition_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    role: Mapped[ExhibitionRole] = mapped_column(String(20))
    # For PARTNER: list of zone UUIDs they can manage (as strings)
    zone_ids: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="exhibition_roles")
    exhibition: Mapped["Exhibition"] = relationship()

    __table_args__ = (
        UniqueConstraint('user_id', 'exhibition_id', name='uq_user_exhibition_role'),
    )