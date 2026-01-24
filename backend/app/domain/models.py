"""
Central import of all domain entities.

This file ensures all SQLAlchemy models are loaded and their relationships
can be resolved. Import this file before using any model in queries.

Similar to Doctrine's entity mapping configuration in Symfony.
"""
# Base and shared
from app.domain.shared.entity import Base

# All entities - order matters for relationship resolution
from app.domain.organization.entity import Organization, UserGroup, GroupPermission
from app.domain.user.entity import User, UserGroupMembership
from app.domain.exhibition.entity import Exhibition, TimeSlot
from app.domain.game.entity import GameCategory, Game, GameTable, TableParticipant
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
    "GameCategory",
    "Game",
    "GameTable",
    "TableParticipant",
    "Media",
    "AuditLog",
]
