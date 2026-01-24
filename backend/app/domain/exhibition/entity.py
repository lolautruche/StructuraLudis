"""
Exhibition domain entities.

Contains: Exhibition, TimeSlot
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.entity import Base, TimestampMixin, ExhibitionStatus

if TYPE_CHECKING:
    from app.domain.organization.entity import Organization
    from app.domain.game.entity import GameTable


class Exhibition(Base, TimestampMixin):
    """
    A convention or event where game tables are organized.

    This is a core aggregate root in the domain.
    """
    __tablename__ = "exhibitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[ExhibitionStatus] = mapped_column(
        String(20), default=ExhibitionStatus.DRAFT
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="exhibitions")
    time_slots: Mapped[List["TimeSlot"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )
    game_tables: Mapped[List["GameTable"]] = relationship(
        back_populates="exhibition", cascade="all, delete-orphan"
    )


class TimeSlot(Base, TimestampMixin):
    """
    A time slot within an exhibition during which games can be scheduled.

    Important: All times should be stored in UTC.
    """
    __tablename__ = "time_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exhibition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity_bonus: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    exhibition: Mapped["Exhibition"] = relationship(back_populates="time_slots")
    game_tables: Mapped[List["GameTable"]] = relationship(
        back_populates="time_slot"
    )