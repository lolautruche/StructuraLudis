"""
Event request API endpoints (Issue #92).

Self-service event creation workflow.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole, EventRequestStatus
from app.domain.event_request.schemas import (
    EventRequestCreate,
    EventRequestUpdate,
    EventRequestAdminUpdate,
    EventRequestRead,
    EventRequestReview,
    EventRequestListResponse,
)
from app.api.deps import get_current_active_user, get_current_verified_user
from app.services.event_request import EventRequestService
from app.services.notification import NotificationService, NotificationRecipient

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency that requires ADMIN or SUPER_ADMIN role."""
    if current_user.global_role not in [GlobalRole.ADMIN, GlobalRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# =============================================================================
# User Endpoints
# =============================================================================

@router.post("/", response_model=EventRequestRead, status_code=status.HTTP_201_CREATED)
async def create_event_request(
    data: EventRequestCreate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new event request.

    Requires:
    - Authenticated user with verified email
    - No pending request from this user

    Auto-generates slugs from event_title and organization_name.
    """
    service = EventRequestService(db)
    notification_service = NotificationService(db)

    request = await service.create_request(data, current_user)
    await db.commit()

    # Send confirmation email to requester
    await notification_service.notify_event_request_confirmation(request)

    # Notify admins about new submission
    await notification_service.notify_event_request_submitted(request)

    return service.to_read_schema(request)


@router.get("/my", response_model=List[EventRequestRead])
async def list_my_requests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List my event requests.

    Returns all requests submitted by the current user.
    """
    service = EventRequestService(db)
    requests = await service.list_my_requests(current_user.id)
    return [service.to_read_schema(r) for r in requests]


@router.get("/{request_id}", response_model=EventRequestRead)
async def get_event_request(
    request_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get an event request by ID.

    Accessible by:
    - Request owner
    - Admins (ADMIN, SUPER_ADMIN)
    """
    service = EventRequestService(db)
    request = await service.get_request(request_id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event request not found",
        )

    # Check access
    is_owner = request.requester_id == current_user.id
    is_admin = current_user.global_role in [GlobalRole.ADMIN, GlobalRole.SUPER_ADMIN]

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request",
        )

    return service.to_read_schema(request)


@router.put("/{request_id}", response_model=EventRequestRead)
async def update_event_request(
    request_id: UUID,
    data: EventRequestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an event request.

    Only the request owner can update, and only if status is CHANGES_REQUESTED.
    """
    service = EventRequestService(db)
    request = await service.update_request(request_id, data, current_user)
    await db.commit()
    return service.to_read_schema(request)


@router.post("/{request_id}/resubmit", response_model=EventRequestRead)
async def resubmit_event_request(
    request_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resubmit an event request after making changes.

    Only the request owner can resubmit, and only if status is CHANGES_REQUESTED.
    Changes status back to PENDING.
    """
    service = EventRequestService(db)
    notification_service = NotificationService(db)

    request = await service.resubmit_request(request_id, current_user)

    # Notify admins about resubmission (with different message)
    await notification_service.notify_event_request_submitted(request, is_resubmission=True)

    await db.commit()
    return service.to_read_schema(request)


# =============================================================================
# Admin Endpoints
# =============================================================================

@router.get("/", response_model=EventRequestListResponse)
async def list_event_requests(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all event requests (admin view).

    Filters:
    - status: PENDING, CHANGES_REQUESTED, APPROVED, REJECTED

    Requires: ADMIN or SUPER_ADMIN
    """
    service = EventRequestService(db)

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = EventRequestStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )

    requests, total, pending_count = await service.list_requests(status_filter, skip, limit)

    return EventRequestListResponse(
        items=[service.to_read_schema(r) for r in requests],
        total=total,
        pending_count=pending_count,
    )


@router.patch("/{request_id}", response_model=EventRequestRead)
async def admin_update_event_request(
    request_id: UUID,
    data: EventRequestAdminUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin update of an event request (can modify slugs).

    Requires: ADMIN or SUPER_ADMIN
    """
    service = EventRequestService(db)
    request = await service.admin_update_request(request_id, data)
    await db.commit()
    return service.to_read_schema(request)


@router.post("/{request_id}/review", response_model=EventRequestRead)
async def review_event_request(
    request_id: UUID,
    review: EventRequestReview,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Review an event request.

    Actions:
    - approve: Creates organization + exhibition, assigns requester as ORGANIZER
    - request_changes: Sets status to CHANGES_REQUESTED (requires admin_comment)
    - reject: Sets status to REJECTED (requires admin_comment)

    Requires: ADMIN or SUPER_ADMIN
    """
    service = EventRequestService(db)
    notification_service = NotificationService(db)

    request, exhibition, organization = await service.review_request(
        request_id, review, current_user
    )

    # Send notification to requester
    recipient = NotificationRecipient(
        user_id=request.requester_id,
        email=request.requester.email if request.requester else "",
        full_name=request.requester.full_name if request.requester else None,
        locale=request.requester.locale if request.requester else "en",
    )

    if review.action == "approve":
        await notification_service.notify_event_request_approved(
            recipient=recipient,
            event_title=request.event_title,
            exhibition_slug=request.event_slug,
        )
    elif review.action == "request_changes":
        await notification_service.notify_event_request_changes(
            recipient=recipient,
            event_title=request.event_title,
            admin_comment=review.admin_comment or "",
        )
    elif review.action == "reject":
        await notification_service.notify_event_request_rejected(
            recipient=recipient,
            event_title=request.event_title,
            admin_comment=review.admin_comment or "",
        )

    await db.commit()
    return service.to_read_schema(request)
