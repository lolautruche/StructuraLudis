"""
Event request service layer (Issue #92).

Handles business logic for self-service event creation requests.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.event_request.entity import EventRequest
from app.domain.event_request.schemas import (
    EventRequestCreate,
    EventRequestUpdate,
    EventRequestAdminUpdate,
    EventRequestReview,
    EventRequestRead,
)
from app.domain.exhibition.entity import Exhibition
from app.domain.organization.entity import Organization, UserGroup
from app.domain.user.entity import User, UserGroupMembership, UserExhibitionRole
from app.domain.shared.entity import (
    EventRequestStatus,
    ExhibitionStatus,
    ExhibitionRole,
    GroupRole,
    UserGroupType,
)


class EventRequestService:
    """Service for event request business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Slug Generation
    # =========================================================================

    async def _generate_unique_event_slug(self, title: str) -> str:
        """Generate a unique slug for an exhibition."""
        base_slug = slugify(title, max_length=90)
        slug = base_slug

        # Check uniqueness against both existing exhibitions and pending requests
        suffix = 1
        while True:
            # Check exhibitions
            existing_exhibition = await self.db.execute(
                select(Exhibition).where(Exhibition.slug == slug)
            )
            # Check pending/changes_requested event requests
            existing_request = await self.db.execute(
                select(EventRequest).where(
                    EventRequest.event_slug == slug,
                    EventRequest.status.in_([
                        EventRequestStatus.PENDING,
                        EventRequestStatus.CHANGES_REQUESTED,
                    ]),
                )
            )
            if not existing_exhibition.scalar_one_or_none() and not existing_request.scalar_one_or_none():
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return slug

    async def _generate_unique_org_slug(self, name: str) -> str:
        """Generate a unique slug for an organization."""
        base_slug = slugify(name, max_length=90)
        slug = base_slug

        # Check uniqueness against both existing organizations and pending requests
        suffix = 1
        while True:
            # Check organizations
            existing_org = await self.db.execute(
                select(Organization).where(Organization.slug == slug)
            )
            # Check pending/changes_requested event requests
            existing_request = await self.db.execute(
                select(EventRequest).where(
                    EventRequest.organization_slug == slug,
                    EventRequest.status.in_([
                        EventRequestStatus.PENDING,
                        EventRequestStatus.CHANGES_REQUESTED,
                    ]),
                )
            )
            if not existing_org.scalar_one_or_none() and not existing_request.scalar_one_or_none():
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return slug

    # =========================================================================
    # Create Request
    # =========================================================================

    async def create_request(
        self,
        data: EventRequestCreate,
        requester: User,
    ) -> EventRequest:
        """
        Create a new event request.

        Validates:
        - User has verified email
        - No pending request from this user
        """
        # Check email verification
        if not requester.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required to submit event requests",
            )

        # Check for existing pending/changes_requested request
        existing = await self.db.execute(
            select(EventRequest).where(
                EventRequest.requester_id == requester.id,
                EventRequest.status.in_([
                    EventRequestStatus.PENDING,
                    EventRequestStatus.CHANGES_REQUESTED,
                ]),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending event request",
            )

        # Generate unique slugs
        event_slug = await self._generate_unique_event_slug(data.event_title)
        org_slug = await self._generate_unique_org_slug(data.organization_name)

        # Create request
        request = EventRequest(
            requester_id=requester.id,
            status=EventRequestStatus.PENDING,
            event_title=data.event_title,
            event_slug=event_slug,
            event_description=data.event_description,
            event_start_date=data.event_start_date,
            event_end_date=data.event_end_date,
            event_location_name=data.event_location_name,
            event_city=data.event_city,
            event_country_code=data.event_country_code,
            event_region=data.event_region,
            event_timezone=data.event_timezone,
            organization_name=data.organization_name,
            organization_slug=org_slug,
            organization_contact_email=data.organization_contact_email,
            requester_message=data.requester_message,
        )
        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)

        return request

    # =========================================================================
    # List Requests
    # =========================================================================

    async def list_requests(
        self,
        status_filter: Optional[EventRequestStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[EventRequest], int, int]:
        """
        List event requests (admin view).

        Returns: (requests, total_count, pending_count)
        """
        query = select(EventRequest).options(selectinload(EventRequest.requester))

        if status_filter:
            query = query.where(EventRequest.status == status_filter)

        # Get total count
        count_query = select(func.count(EventRequest.id))
        if status_filter:
            count_query = count_query.where(EventRequest.status == status_filter)
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get pending count
        pending_query = select(func.count(EventRequest.id)).where(
            EventRequest.status == EventRequestStatus.PENDING
        )
        pending_result = await self.db.execute(pending_query)
        pending_count = pending_result.scalar() or 0

        # Get paginated results
        query = query.order_by(EventRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        return requests, total_count, pending_count

    async def list_my_requests(self, user_id: UUID) -> List[EventRequest]:
        """List requests submitted by a user."""
        result = await self.db.execute(
            select(EventRequest)
            .where(EventRequest.requester_id == user_id)
            .order_by(EventRequest.created_at.desc())
        )
        return list(result.scalars().all())

    # =========================================================================
    # Get Request
    # =========================================================================

    async def get_request(self, request_id: UUID) -> Optional[EventRequest]:
        """Get a request by ID with requester loaded."""
        result = await self.db.execute(
            select(EventRequest)
            .options(selectinload(EventRequest.requester))
            .where(EventRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Update Request
    # =========================================================================

    async def update_request(
        self,
        request_id: UUID,
        data: EventRequestUpdate,
        user: User,
    ) -> EventRequest:
        """
        Update a request (by owner).

        Only allowed if status is CHANGES_REQUESTED.
        """
        request = await self.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event request not found",
            )

        # Check ownership
        if request.requester_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this request",
            )

        # Check status
        if request.status != EventRequestStatus.CHANGES_REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update requests with status CHANGES_REQUESTED",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(request, field, value)

        # Regenerate slugs if names changed
        if "event_title" in update_data:
            request.event_slug = await self._generate_unique_event_slug(data.event_title)
        if "organization_name" in update_data:
            request.organization_slug = await self._generate_unique_org_slug(data.organization_name)

        await self.db.flush()
        await self.db.refresh(request)

        return request

    async def admin_update_request(
        self,
        request_id: UUID,
        data: EventRequestAdminUpdate,
    ) -> EventRequest:
        """Update a request (admin can modify slugs)."""
        request = await self.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event request not found",
            )

        # Can only update pending or changes_requested
        if request.status not in [EventRequestStatus.PENDING, EventRequestStatus.CHANGES_REQUESTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update requests that are already approved or rejected",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(request, field, value)

        await self.db.flush()
        await self.db.refresh(request)

        return request

    # =========================================================================
    # Review Request
    # =========================================================================

    async def review_request(
        self,
        request_id: UUID,
        review: EventRequestReview,
        reviewer: User,
    ) -> Tuple[EventRequest, Optional[Exhibition], Optional[Organization]]:
        """
        Review an event request (admin action).

        Actions:
        - approve: Create organization + exhibition, set APPROVED
        - request_changes: Set CHANGES_REQUESTED with comment
        - reject: Set REJECTED with comment

        Returns: (request, exhibition, organization) - exhibition/org only on approve
        """
        request = await self.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event request not found",
            )

        # Validate status for review
        if review.action == "approve":
            if request.status != EventRequestStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only approve requests with status PENDING",
                )
        elif review.action == "request_changes":
            if request.status != EventRequestStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only request changes for requests with status PENDING",
                )
        elif review.action == "reject":
            if request.status not in [EventRequestStatus.PENDING, EventRequestStatus.CHANGES_REQUESTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only reject requests with status PENDING or CHANGES_REQUESTED",
                )

        now = datetime.now(timezone.utc)
        request.reviewed_by_id = reviewer.id
        request.reviewed_at = now
        request.admin_comment = review.admin_comment

        exhibition = None
        organization = None

        if review.action == "approve":
            # Create organization
            organization = Organization(
                name=request.organization_name,
                slug=request.organization_slug,
                contact_email=request.organization_contact_email,
                legal_registration_number=request.organization_legal_number,
            )
            self.db.add(organization)
            await self.db.flush()

            # Create STAFF user group for the organization
            staff_group = UserGroup(
                organization_id=organization.id,
                name=f"{request.organization_name} Staff",
                type=UserGroupType.STAFF,
                is_public=False,
            )
            self.db.add(staff_group)
            await self.db.flush()

            # Add requester as ADMIN of the group
            membership = UserGroupMembership(
                user_id=request.requester_id,
                user_group_id=staff_group.id,
                group_role=GroupRole.ADMIN,
            )
            self.db.add(membership)

            # Create exhibition
            # Use requester's locale for primary language, default to "en" if not set
            primary_language = request.requester.locale if request.requester and request.requester.locale else "en"
            exhibition = Exhibition(
                organization_id=organization.id,
                created_by_id=request.requester_id,
                title=request.event_title,
                slug=request.event_slug,
                description=request.event_description,
                start_date=request.event_start_date,
                end_date=request.event_end_date,
                location_name=request.event_location_name,
                city=request.event_city,
                country_code=request.event_country_code,
                region=request.event_region,
                timezone=request.event_timezone,
                status=ExhibitionStatus.PUBLISHED,
                primary_language=primary_language,
            )
            self.db.add(exhibition)
            await self.db.flush()

            # Assign requester as ORGANIZER
            organizer_role = UserExhibitionRole(
                user_id=request.requester_id,
                exhibition_id=exhibition.id,
                role=ExhibitionRole.ORGANIZER,
            )
            self.db.add(organizer_role)

            # Update request
            request.status = EventRequestStatus.APPROVED
            request.created_exhibition_id = exhibition.id
            request.created_organization_id = organization.id

        elif review.action == "request_changes":
            request.status = EventRequestStatus.CHANGES_REQUESTED

        elif review.action == "reject":
            request.status = EventRequestStatus.REJECTED

        await self.db.flush()
        await self.db.refresh(request)

        return request, exhibition, organization

    # =========================================================================
    # Resubmit Request
    # =========================================================================

    async def resubmit_request(
        self,
        request_id: UUID,
        user: User,
    ) -> EventRequest:
        """
        Resubmit a request after making changes.

        Only allowed if status is CHANGES_REQUESTED.
        """
        request = await self.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event request not found",
            )

        # Check ownership
        if request.requester_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to resubmit this request",
            )

        # Check status
        if request.status != EventRequestStatus.CHANGES_REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resubmit requests with status CHANGES_REQUESTED",
            )

        request.status = EventRequestStatus.PENDING
        request.reviewed_by_id = None
        request.reviewed_at = None
        # Keep admin_comment for reference

        await self.db.flush()
        await self.db.refresh(request)

        return request

    # =========================================================================
    # Cancel Request
    # =========================================================================

    async def cancel_request(
        self,
        request_id: UUID,
        user: User,
    ) -> EventRequest:
        """
        Cancel an event request.

        Only allowed if status is PENDING or CHANGES_REQUESTED.
        """
        request = await self.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event request not found",
            )

        # Check ownership
        if request.requester_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this request",
            )

        # Check status - can only cancel pending or changes_requested
        if request.status not in [EventRequestStatus.PENDING, EventRequestStatus.CHANGES_REQUESTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel requests with status PENDING or CHANGES_REQUESTED",
            )

        request.status = EventRequestStatus.CANCELLED

        await self.db.flush()
        await self.db.refresh(request)

        return request

    # =========================================================================
    # Helpers
    # =========================================================================

    def to_read_schema(self, request: EventRequest) -> EventRequestRead:
        """Convert entity to read schema with joined fields."""
        return EventRequestRead(
            id=request.id,
            requester_id=request.requester_id,
            status=request.status.value if isinstance(request.status, EventRequestStatus) else request.status,
            event_title=request.event_title,
            event_slug=request.event_slug,
            event_description=request.event_description,
            event_start_date=request.event_start_date,
            event_end_date=request.event_end_date,
            event_location_name=request.event_location_name,
            event_city=request.event_city,
            event_country_code=request.event_country_code,
            event_region=request.event_region,
            event_timezone=request.event_timezone,
            organization_name=request.organization_name,
            organization_slug=request.organization_slug,
            organization_contact_email=request.organization_contact_email,
            requester_message=request.requester_message,
            admin_comment=request.admin_comment,
            reviewed_by_id=request.reviewed_by_id,
            reviewed_at=request.reviewed_at,
            created_exhibition_id=request.created_exhibition_id,
            created_organization_id=request.created_organization_id,
            created_at=request.created_at,
            updated_at=request.updated_at,
            requester_email=request.requester.email if request.requester else None,
            requester_name=request.requester.full_name if request.requester else None,
        )
