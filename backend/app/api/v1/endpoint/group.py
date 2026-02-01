"""
UserGroup API endpoints (#31).

Group management and member administration for partners.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.organization.entity import Organization, UserGroup
from app.domain.organization.schemas import (
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
    GroupMemberAdd,
    GroupMemberUpdate,
    GroupMemberRead,
)
from app.domain.user.entity import User, UserGroupMembership
from app.domain.shared.entity import GlobalRole, GroupRole
from app.api.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# UserGroup CRUD
# =============================================================================

@router.get("/", response_model=List[UserGroupRead])
async def list_groups(
    organization_id: UUID = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List user groups.

    Optional filter by organization_id.
    """
    query = select(UserGroup)
    if organization_id:
        query = query.where(UserGroup.organization_id == organization_id)
    query = query.order_by(UserGroup.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_in: UserGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user group.

    Requires: ADMIN or SUPER_ADMIN.
    """
    if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create groups",
        )

    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == group_in.organization_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    group = UserGroup(**group_in.model_dump())
    db.add(group)
    await db.flush()
    await db.refresh(group)

    return group


@router.get("/{group_id}", response_model=UserGroupRead)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a user group by ID."""
    result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return group


@router.put("/{group_id}", response_model=UserGroupRead)
async def update_group(
    group_id: UUID,
    group_in: UserGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user group.

    Requires: ADMIN, SUPER_ADMIN, or group OWNER/ADMIN.
    """
    result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check permissions
    can_update = current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]

    if not can_update:
        # Check if user is group admin/owner
        membership_result = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.user_id == current_user.id,
                UserGroupMembership.group_role.in_([GroupRole.OWNER, GroupRole.ADMIN]),
            )
        )
        if membership_result.scalar_one_or_none():
            can_update = True

    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update this group",
        )

    update_data = group_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    await db.flush()
    await db.refresh(group)

    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user group.

    Requires: ADMIN or SUPER_ADMIN.
    """
    if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete groups",
        )

    result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    await db.delete(group)


# =============================================================================
# Group Members Management (#31)
# =============================================================================

@router.get("/{group_id}/members", response_model=List[GroupMemberRead])
async def list_group_members(
    group_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all members of a group.

    Visible to: group members, admins, or SUPER_ADMIN.
    """
    # Check group exists
    group_result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check permissions (public groups visible to all, private to members/admins)
    can_view = (
        group.is_public
        or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]
    )

    if not can_view:
        # Check if user is a member
        membership_check = await db.execute(
            select(UserGroupMembership.id).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.user_id == current_user.id,
            )
        )
        if membership_check.scalar_one_or_none():
            can_view = True

    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view members of this group",
        )

    # Fetch members with user info
    result = await db.execute(
        select(UserGroupMembership, User.email, User.full_name)
        .join(User, UserGroupMembership.user_id == User.id)
        .where(UserGroupMembership.user_group_id == group_id)
        .order_by(UserGroupMembership.joined_at)
    )
    rows = result.all()

    return [
        GroupMemberRead(
            id=membership.id,
            user_id=membership.user_id,
            user_email=email,
            user_full_name=full_name,
            group_role=membership.group_role,
            joined_at=membership.joined_at,
        )
        for membership, email, full_name in rows
    ]


@router.post("/{group_id}/members", response_model=GroupMemberRead, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: UUID,
    member_in: GroupMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a member to a group.

    Requires: ADMIN, SUPER_ADMIN, or group OWNER/ADMIN.
    """
    # Check group exists
    group_result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check permissions
    can_add = current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]

    if not can_add:
        membership_result = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.user_id == current_user.id,
                UserGroupMembership.group_role.in_([GroupRole.OWNER, GroupRole.ADMIN]),
            )
        )
        if membership_result.scalar_one_or_none():
            can_add = True

    if not can_add:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot add members to this group",
        )

    # Check user exists
    user_result = await db.execute(
        select(User).where(User.id == member_in.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    existing = await db.execute(
        select(UserGroupMembership).where(
            UserGroupMembership.user_group_id == group_id,
            UserGroupMembership.user_id == member_in.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group",
        )

    # Create membership
    membership = UserGroupMembership(
        user_group_id=group_id,
        user_id=member_in.user_id,
        group_role=member_in.group_role,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    return GroupMemberRead(
        id=membership.id,
        user_id=membership.user_id,
        user_email=user.email,
        user_full_name=user.full_name,
        group_role=membership.group_role,
        joined_at=membership.joined_at,
    )


@router.patch("/{group_id}/members/{user_id}", response_model=GroupMemberRead)
async def update_group_member(
    group_id: UUID,
    user_id: UUID,
    member_in: GroupMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a member's role in a group.

    Requires: ADMIN, SUPER_ADMIN, or group OWNER.
    Cannot demote yourself if you're the only OWNER.
    """
    # Check group exists
    group_result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Get membership
    membership_result = await db.execute(
        select(UserGroupMembership, User.email, User.full_name)
        .join(User, UserGroupMembership.user_id == User.id)
        .where(
            UserGroupMembership.user_group_id == group_id,
            UserGroupMembership.user_id == user_id,
        )
    )
    row = membership_result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )

    membership, email, full_name = row

    # Check permissions - only OWNER can change roles
    can_update = current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]

    if not can_update:
        owner_check = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.user_id == current_user.id,
                UserGroupMembership.group_role == GroupRole.OWNER,
            )
        )
        if owner_check.scalar_one_or_none():
            can_update = True

    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group owners can change member roles",
        )

    # Prevent demoting the last owner
    if membership.group_role == GroupRole.OWNER and member_in.group_role != GroupRole.OWNER:
        owner_count = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.group_role == GroupRole.OWNER,
            )
        )
        if len(owner_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last owner of a group",
            )

    membership.group_role = member_in.group_role
    await db.flush()
    await db.refresh(membership)

    return GroupMemberRead(
        id=membership.id,
        user_id=membership.user_id,
        user_email=email,
        user_full_name=full_name,
        group_role=membership.group_role,
        joined_at=membership.joined_at,
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a member from a group.

    Requires: ADMIN, SUPER_ADMIN, group OWNER/ADMIN, or self-removal.
    Cannot remove the last OWNER.
    """
    # Check group exists
    group_result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Get membership
    membership_result = await db.execute(
        select(UserGroupMembership).where(
            UserGroupMembership.user_group_id == group_id,
            UserGroupMembership.user_id == user_id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )

    # Check permissions
    can_remove = (
        current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]
        or user_id == current_user.id  # Self-removal
    )

    if not can_remove:
        admin_check = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.user_id == current_user.id,
                UserGroupMembership.group_role.in_([GroupRole.OWNER, GroupRole.ADMIN]),
            )
        )
        if admin_check.scalar_one_or_none():
            can_remove = True

    if not can_remove:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot remove members from this group",
        )

    # Prevent removing the last owner
    if membership.group_role == GroupRole.OWNER:
        owner_count = await db.execute(
            select(UserGroupMembership).where(
                UserGroupMembership.user_group_id == group_id,
                UserGroupMembership.group_role == GroupRole.OWNER,
            )
        )
        if len(owner_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner of a group",
            )

    await db.delete(membership)