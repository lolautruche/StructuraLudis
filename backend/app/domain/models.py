"""
Central import of all domain entities.

This file ensures all SQLAlchemy models are loaded and their relationships
can be resolved. Import this file before using any model in queries.
"""
# Base and shared
from app.domain.shared.entity import Base

# All entities - order matters for relationship resolution
from app.domain.organization.entity import Organization, UserGroup, GroupPermission
from app.domain.user.entity import User, UserGroupMembership
from app.domain.exhibition.entity import Exhibition, TimeSlot, Zone, PhysicalTable
from app.domain.game.entity import GameCategory, Game, GameSession, Booking
from app.domain.media.entity import Media, AuditLog

__all__ = [
    "Base",
    "Organization",
    "UserGroup",
    "GroupPermission",
    "User",
    "UserGroupMembership",
    "Exhibition",
    "TimeSlot",
    "Zone",
    "PhysicalTable",
    "GameCategory",
    "Game",
    "GameSession",
    "Booking",
    "Media",
    "AuditLog",
]
