"""
Admin API endpoints.

Super Admin operations for user and platform management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.user.entity import User
from app.domain.user.schemas import UserRead, UserRoleUpdate, UserStatusUpdate
from app.domain.exhibition.entity import Exhibition
from app.domain.exhibition.schemas import ExhibitionRead
from app.domain.shared.entity import GlobalRole
from app.api.deps import get_current_active_user

router = APIRouter()


def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency that requires SUPER_ADMIN role."""
    if current_user.global_role != GlobalRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return current_user


# =============================================================================
# User Management
# =============================================================================

@router.get("/users", response_model=List[UserRead])
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users with optional filters.

    Filters:
    - role: filter by global role (SUPER_ADMIN, ORGANIZER, PARTNER, USER)
    - is_active: filter by active status

    Requires: SUPER_ADMIN
    """
    query = select(User)

    if role:
        query = query.where(User.global_role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.full_name.asc(), User.email.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a user by ID.

    Requires: SUPER_ADMIN
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch("/users/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's global role.

    Use this to promote a user to ORGANIZER or PARTNER,
    or to demote them back to USER.

    Requires: SUPER_ADMIN
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-demotion
    if user.id == current_user.id and role_update.global_role != GlobalRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself",
        )

    user.global_role = role_update.global_role
    await db.flush()
    await db.refresh(user)

    return user


@router.patch("/users/{user_id}/status", response_model=UserRead)
async def update_user_status(
    user_id: UUID,
    status_update: UserStatusUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate or deactivate a user.

    Deactivated users cannot log in or perform any actions.

    Requires: SUPER_ADMIN
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deactivation
    if user.id == current_user.id and not status_update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    user.is_active = status_update.is_active
    await db.flush()
    await db.refresh(user)

    return user


# =============================================================================
# Platform Overview
# =============================================================================

@router.get("/exhibitions", response_model=List[ExhibitionRead])
async def list_all_exhibitions(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all exhibitions across all organizations.

    Requires: SUPER_ADMIN
    """
    query = select(Exhibition)

    if status:
        query = query.where(Exhibition.status == status)

    query = query.order_by(Exhibition.start_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_platform_stats(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform-wide statistics.

    Requires: SUPER_ADMIN
    """
    # Count users by role
    users_by_role = await db.execute(
        select(User.global_role, func.count(User.id))
        .group_by(User.global_role)
    )
    user_counts = {str(row[0]): row[1] for row in users_by_role.fetchall()}

    # Count exhibitions by status
    exhibitions_by_status = await db.execute(
        select(Exhibition.status, func.count(Exhibition.id))
        .group_by(Exhibition.status)
    )
    exhibition_counts = {str(row[0]): row[1] for row in exhibitions_by_status.fetchall()}

    # Total counts
    total_users = sum(user_counts.values())
    total_exhibitions = sum(exhibition_counts.values())

    return {
        "users": {
            "total": total_users,
            "by_role": user_counts,
        },
        "exhibitions": {
            "total": total_exhibitions,
            "by_status": exhibition_counts,
        },
    }