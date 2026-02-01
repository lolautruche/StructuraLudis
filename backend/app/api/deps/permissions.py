"""
Permission dependencies.

Provides role-based access control for API endpoints.
"""
from typing import Callable, List
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.shared.entity import GlobalRole, GroupRole
from app.domain.user.entity import User, UserGroupMembership
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


async def can_manage_exhibition(
    user: User,
    exhibition: Exhibition,
    db: AsyncSession,
) -> bool:
    """
    Check if user can manage the specified exhibition.

    Returns True if:
    - User is SUPER_ADMIN
    - User is ORGANIZER and belongs to the exhibition's organization
    """
    if not user or not user.is_active:
        return False

    # SUPER_ADMIN can do anything
    if user.global_role == GlobalRole.SUPER_ADMIN:
        return True

    # Check if user is ORGANIZER
    if user.global_role != GlobalRole.ORGANIZER:
        return False

    # Check if user belongs to the exhibition's organization
    membership = await db.execute(
        select(UserGroupMembership)
        .join(UserGroupMembership.user_group)
        .where(
            UserGroupMembership.user_id == user.id,
            UserGroupMembership.user_group.has(
                organization_id=exhibition.organization_id
            ),
        )
    )

    return membership.scalar_one_or_none() is not None


async def require_exhibition_organizer(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Check if user can manage the specified exhibition.

    Allowed if:
    - User is SUPER_ADMIN
    - User is ORGANIZER and belongs to the exhibition's organization
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


async def require_zone_manager(
    zone_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Check if user can manage the specified zone.

    Allowed if:
    - User is SUPER_ADMIN
    - User is exhibition organizer
    - User is PARTNER and zone is delegated to their group
    """
    # SUPER_ADMIN can do anything
    if current_user.global_role == GlobalRole.SUPER_ADMIN:
        return current_user

    # Get the zone with exhibition
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Check if zone is delegated to user's group
    if zone.delegated_to_group_id:
        membership = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_id == current_user.id,
                UserGroupMembership.user_group_id == zone.delegated_to_group_id,
                UserGroupMembership.group_role.in_([GroupRole.OWNER, GroupRole.ADMIN]),
            )
        )
        if membership.scalar_one_or_none():
            return current_user

    # Fall back to exhibition organizer check
    return await require_exhibition_organizer(
        zone.exhibition_id, current_user, db
    )
