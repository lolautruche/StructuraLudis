"""
Permission dependencies.

Provides role-based access control for API endpoints (Issue #99).
"""
from typing import Callable, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.shared.entity import GlobalRole, ExhibitionRole
from app.domain.user.entity import User, UserExhibitionRole
from app.domain.exhibition.entity import Exhibition, Zone
from app.api.deps.auth import get_current_active_user


def require_roles(allowed_roles: List[GlobalRole]) -> Callable:
    """
    Dependency factory that checks if user has one of the allowed global roles.

    Usage:
        @router.post("/", dependencies=[Depends(require_roles([GlobalRole.SUPER_ADMIN]))])
    """

    async def check_roles(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.global_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return check_roles


async def get_user_exhibition_role(
    user_id: UUID,
    exhibition_id: UUID,
    db: AsyncSession,
) -> Optional[UserExhibitionRole]:
    """Get a user's role assignment for a specific exhibition."""
    result = await db.execute(
        select(UserExhibitionRole).where(
            UserExhibitionRole.user_id == user_id,
            UserExhibitionRole.exhibition_id == exhibition_id,
        )
    )
    return result.scalar_one_or_none()


async def has_exhibition_role(
    user: User,
    exhibition_id: UUID,
    roles: List[ExhibitionRole],
    db: AsyncSession,
) -> bool:
    """
    Check if user has any of the specified exhibition roles.

    Returns True if:
    - User is SUPER_ADMIN or ADMIN (platform admins have all permissions)
    - User has one of the specified roles for this exhibition
    """
    if not user or not user.is_active:
        return False

    # Platform admins have all permissions
    if user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        return True

    # Check exhibition-scoped role
    result = await db.execute(
        select(UserExhibitionRole).where(
            UserExhibitionRole.user_id == user.id,
            UserExhibitionRole.exhibition_id == exhibition_id,
            UserExhibitionRole.role.in_([r.value for r in roles]),
        )
    )
    return result.scalar_one_or_none() is not None


async def can_manage_exhibition(
    user: User,
    exhibition: Exhibition,
    db: AsyncSession,
) -> bool:
    """
    Check if user can manage the specified exhibition.

    Returns True if:
    - User is SUPER_ADMIN or ADMIN
    - User has ORGANIZER role for this specific exhibition
    """
    return await has_exhibition_role(
        user, exhibition.id, [ExhibitionRole.ORGANIZER], db
    )


async def require_exhibition_organizer(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Check if user can manage the specified exhibition.

    Allowed if:
    - User is SUPER_ADMIN or ADMIN
    - User has ORGANIZER role for this exhibition
    """
    # Get the exhibition
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    if not await can_manage_exhibition(current_user, exhibition, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this exhibition",
        )

    return current_user


async def can_manage_zone(
    user: User,
    zone: Zone,
    db: AsyncSession,
) -> bool:
    """
    Check if user can manage the specified zone.

    Returns True if:
    - User is SUPER_ADMIN or ADMIN
    - User has ORGANIZER role for the exhibition (manages all zones)
    - User has PARTNER role for the exhibition with this zone in their zone_ids
    """
    if not user or not user.is_active:
        return False

    # Platform admins can manage all zones
    if user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        return True

    # Get user's exhibition role
    user_role = await get_user_exhibition_role(user.id, zone.exhibition_id, db)

    if not user_role:
        return False

    # ORGANIZER can manage all zones in their exhibition
    if user_role.role == ExhibitionRole.ORGANIZER:
        return True

    # PARTNER can only manage their assigned zones
    if user_role.role == ExhibitionRole.PARTNER:
        if user_role.zone_ids and str(zone.id) in user_role.zone_ids:
            return True

    return False


async def require_zone_manager(
    zone_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Check if user can manage the specified zone.

    Allowed if:
    - User is SUPER_ADMIN or ADMIN
    - User has ORGANIZER role for the exhibition
    - User has PARTNER role with this zone in their zone_ids
    """
    # Get the zone
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    if not await can_manage_zone(current_user, zone, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this zone",
        )

    return current_user
