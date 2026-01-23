from datetime import datetime
from typing import Annotated, List
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

# Reusable types for consistency
pk_uuid = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]
timestamp = Annotated[datetime, mapped_column(DateTime, server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(DateTime, server_default=func.now(), onupdate=func.now())]

class User(Base):
    __tablename__ = "users"

    id: Mapped[pk_uuid]
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_at]

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[pk_uuid]
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    location_name: Mapped[str] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_at]
