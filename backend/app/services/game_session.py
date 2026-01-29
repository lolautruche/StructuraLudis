"""
GameSession service layer.

Contains business logic for game sessions, bookings, and workflow.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.game.entity import GameSession, Game, GameCategory, Booking
from app.domain.game.schemas import (
    GameSessionCreate,
    GameSessionUpdate,
    GameSessionModerate,
    BookingCreate,
    SessionFilters,
    AffectedUser,
)
from app.domain.exhibition.entity import Exhibition, TimeSlot, PhysicalTable, Zone
from app.domain.user.entity import User
from app.domain.shared.entity import (
    SessionStatus,
    BookingStatus,
    ParticipantRole,
    GlobalRole,
    PhysicalTableStatus,
)


class GameSessionService:
    """Service for game session business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Session Discovery
    # =========================================================================

    async def search_sessions(
        self,
        exhibition_id: UUID,
        filters: SessionFilters,
        include_drafts: bool = False,
    ) -> List[dict]:
        """
        Search sessions with advanced filters (JS.C1, JS.C6).

        Returns sessions with computed fields like available_seats.
        By default, only returns VALIDATED sessions (public discovery).
        """
        # Base query with joins for filtering
        query = (
            select(
                GameSession,
                Game.title.label("game_title"),
                GameCategory.slug.label("category_slug"),
                Zone.name.label("zone_name"),
            )
            .join(Game, GameSession.game_id == Game.id)
            .join(GameCategory, Game.category_id == GameCategory.id)
            .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
            .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
            .where(GameSession.exhibition_id == exhibition_id)
        )

        # Default: only validated sessions for public discovery
        if not include_drafts:
            query = query.where(GameSession.status == SessionStatus.VALIDATED)

        # Apply filters
        if filters.category_id:
            query = query.where(Game.category_id == filters.category_id)

        if filters.language:
            query = query.where(GameSession.language == filters.language)

        if filters.is_accessible_disability is not None:
            query = query.where(
                GameSession.is_accessible_disability == filters.is_accessible_disability
            )

        if filters.max_age_requirement is not None:
            # Show sessions with no age requirement OR min_age <= given value
            query = query.where(
                or_(
                    GameSession.min_age.is_(None),
                    GameSession.min_age <= filters.max_age_requirement,
                )
            )

        if filters.zone_id:
            query = query.where(Zone.id == filters.zone_id)

        if filters.time_slot_id:
            query = query.where(GameSession.time_slot_id == filters.time_slot_id)

        if filters.starts_after:
            query = query.where(GameSession.scheduled_start >= filters.starts_after)

        if filters.starts_before:
            query = query.where(GameSession.scheduled_start <= filters.starts_before)

        # Order by start time
        query = query.order_by(GameSession.scheduled_start)

        result = await self.db.execute(query)
        rows = result.all()

        # Build results with computed fields
        sessions_with_availability = []
        for row in rows:
            session = row[0]
            game_title = row[1]
            category_slug = row[2]
            zone_name = row[3]

            # Count confirmed bookings
            booking_count = await self.db.execute(
                select(func.count(Booking.id)).where(
                    Booking.game_session_id == session.id,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.CHECKED_IN,
                    ]),
                )
            )
            confirmed_count = booking_count.scalar() or 0
            available_seats = max(0, session.max_players_count - confirmed_count)

            # Apply availability filter
            if filters.has_available_seats is True and available_seats == 0:
                continue
            if filters.has_available_seats is False and available_seats > 0:
                continue

            sessions_with_availability.append({
                "id": session.id,
                "exhibition_id": session.exhibition_id,
                "time_slot_id": session.time_slot_id,
                "game_id": session.game_id,
                "physical_table_id": session.physical_table_id,
                "provided_by_group_id": session.provided_by_group_id,
                "created_by_user_id": session.created_by_user_id,
                "title": session.title,
                "description": session.description,
                "language": session.language,
                "min_age": session.min_age,
                "max_players_count": session.max_players_count,
                "safety_tools": session.safety_tools,
                "is_accessible_disability": session.is_accessible_disability,
                "status": session.status,
                "rejection_reason": session.rejection_reason,
                "scheduled_start": session.scheduled_start,
                "scheduled_end": session.scheduled_end,
                "gm_checked_in_at": session.gm_checked_in_at,
                "actual_start": session.actual_start,
                "actual_end": session.actual_end,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                # Computed fields
                "available_seats": available_seats,
                "category_slug": category_slug,
                "zone_name": zone_name,
                "game_title": game_title,
            })

        return sessions_with_availability

    # =========================================================================
    # GameSession CRUD
    # =========================================================================

    async def create_session(
        self,
        data: GameSessionCreate,
        current_user: User,
    ) -> GameSession:
        """
        Create a new game session.

        Validates:
        - Exhibition exists and is published
        - TimeSlot belongs to the exhibition
        - Game exists
        - Schedule is within time slot bounds
        """
        # Validate exhibition
        exhibition = await self._get_exhibition(data.exhibition_id)
        if not exhibition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )

        # Validate time slot belongs to exhibition
        time_slot = await self._get_time_slot(data.time_slot_id)
        if not time_slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time slot not found",
            )
        if time_slot.exhibition_id != data.exhibition_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot does not belong to this exhibition",
            )

        # Validate game exists
        game = await self._get_game(data.game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found",
            )

        # Validate schedule within time slot
        if data.scheduled_start < time_slot.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session cannot start before time slot",
            )
        if data.scheduled_end > time_slot.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session cannot end after time slot",
            )

        # Validate duration
        duration_minutes = (data.scheduled_end - data.scheduled_start).total_seconds() / 60
        if duration_minutes > time_slot.max_duration_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session duration ({int(duration_minutes)} min) exceeds "
                       f"maximum allowed ({time_slot.max_duration_minutes} min)",
            )

        # Check GM schedule overlap - cannot run two sessions at the same time
        gm_session_conflict = await self._check_gm_session_overlap(
            user_id=current_user.id,
            exhibition_id=data.exhibition_id,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
        )
        if gm_session_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You are already running session '{gm_session_conflict.title}' "
                       f"({gm_session_conflict.scheduled_start.strftime('%H:%M')} - "
                       f"{gm_session_conflict.scheduled_end.strftime('%H:%M')})",
            )

        # Check GM booking overlap - cannot be a player at another table
        gm_booking_conflict = await self._check_booking_overlap(
            user_id=current_user.id,
            exhibition_id=data.exhibition_id,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
        )
        if gm_booking_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You are registered as a player for session '{gm_booking_conflict.title}' "
                       f"({gm_booking_conflict.scheduled_start.strftime('%H:%M')} - "
                       f"{gm_booking_conflict.scheduled_end.strftime('%H:%M')})",
            )

        session = GameSession(
            **data.model_dump(),
            created_by_user_id=current_user.id,
            status=SessionStatus.DRAFT,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def update_session(
        self,
        session_id: UUID,
        data: GameSessionUpdate,
        current_user: User,
    ) -> GameSession:
        """
        Update a game session.

        Only draft sessions can be fully edited.
        Validated sessions have limited editable fields.
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        # Check ownership or admin
        if not self._can_edit_session(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot edit this session",
            )

        # Only draft sessions can be fully edited
        if session.status not in [SessionStatus.DRAFT, SessionStatus.REJECTED]:
            # Limited fields for non-draft sessions
            allowed_fields = {"description", "physical_table_id"}
            update_data = data.model_dump(exclude_unset=True)
            for field in update_data:
                if field not in allowed_fields:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot modify '{field}' on a {session.status.value} session",
                    )

        update_data = data.model_dump(exclude_unset=True)

        # Check GM schedule overlap if times are being changed
        new_start = update_data.get("scheduled_start", session.scheduled_start)
        new_end = update_data.get("scheduled_end", session.scheduled_end)
        schedule_changed = (
            "scheduled_start" in update_data or "scheduled_end" in update_data
        )

        if schedule_changed:
            # Check GM session overlap
            gm_session_conflict = await self._check_gm_session_overlap(
                user_id=session.created_by_user_id,
                exhibition_id=session.exhibition_id,
                scheduled_start=new_start,
                scheduled_end=new_end,
                exclude_session_id=session_id,
            )
            if gm_session_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Schedule conflict with session '{gm_session_conflict.title}' "
                           f"({gm_session_conflict.scheduled_start.strftime('%H:%M')} - "
                           f"{gm_session_conflict.scheduled_end.strftime('%H:%M')})",
                )

            # Check GM booking overlap
            gm_booking_conflict = await self._check_booking_overlap(
                user_id=session.created_by_user_id,
                exhibition_id=session.exhibition_id,
                scheduled_start=new_start,
                scheduled_end=new_end,
                exclude_session_id=session_id,
            )
            if gm_booking_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"You are registered as a player for session '{gm_booking_conflict.title}' "
                           f"({gm_booking_conflict.scheduled_start.strftime('%H:%M')} - "
                           f"{gm_booking_conflict.scheduled_end.strftime('%H:%M')})",
                )

        for field, value in update_data.items():
            setattr(session, field, value)

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def delete_session(
        self,
        session_id: UUID,
        current_user: User,
    ) -> None:
        """
        Delete a game session.

        Only draft sessions can be deleted.
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        if not self._can_edit_session(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot delete this session",
            )

        if session.status != SessionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft sessions can be deleted",
            )

        await self.db.delete(session)

    # =========================================================================
    # Workflow Operations
    # =========================================================================

    async def submit_for_moderation(
        self,
        session_id: UUID,
        current_user: User,
    ) -> GameSession:
        """
        Submit a session for moderation.

        Transitions: DRAFT -> PENDING_MODERATION
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        if not self._can_edit_session(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot submit this session",
            )

        if session.status not in [SessionStatus.DRAFT, SessionStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit a {session.status.value} session",
            )

        session.status = SessionStatus.PENDING_MODERATION
        session.rejection_reason = None
        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def moderate_session(
        self,
        session_id: UUID,
        data: GameSessionModerate,
        current_user: User,
    ) -> GameSession:
        """
        Approve or reject a session.

        Requires: Organizer or SUPER_ADMIN.
        Transitions: PENDING_MODERATION -> VALIDATED or REJECTED
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        # Check moderator permissions
        if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizers can moderate sessions",
            )

        if session.status != SessionStatus.PENDING_MODERATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot moderate a {session.status.value} session",
            )

        if data.action == "approve":
            session.status = SessionStatus.VALIDATED
            session.rejection_reason = None
        else:
            session.status = SessionStatus.REJECTED
            session.rejection_reason = data.rejection_reason

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def cancel_session(
        self,
        session_id: UUID,
        reason: str,
        current_user: User,
    ) -> tuple[GameSession, list[AffectedUser]]:
        """
        Cancel a session and notify registered players (JS.B4).

        Cancels the session and all associated bookings.
        Returns the session and list of affected users for notification.

        Can be done by: session creator (GM), organizers, or super admin.
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        # Check permission - GM, organizers, or super admin
        can_cancel = (
            session.created_by_user_id == current_user.id
            or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]
        )
        if not can_cancel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot cancel this session",
            )

        # Cannot cancel already cancelled sessions
        if session.status == SessionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is already cancelled",
            )

        # Cannot cancel finished sessions
        if session.status == SessionStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a finished session",
            )

        # Get all active bookings for this session
        bookings_result = await self.db.execute(
            select(Booking, User)
            .join(User, Booking.user_id == User.id)
            .where(
                Booking.game_session_id == session_id,
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.CHECKED_IN,
                    BookingStatus.WAITING_LIST,
                ]),
            )
        )
        booking_rows = bookings_result.all()

        # Build list of affected users
        affected_users = []
        for booking, user in booking_rows:
            affected_users.append(AffectedUser(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                booking_status=booking.status,
            ))
            # Cancel the booking
            booking.status = BookingStatus.CANCELLED

        # Cancel the session
        session.status = SessionStatus.CANCELLED
        session.rejection_reason = reason

        await self.db.flush()
        await self.db.refresh(session)

        return session, affected_users

    async def copy_session(
        self,
        session_id: UUID,
        time_slot_id: UUID | None,
        scheduled_start: datetime | None,
        scheduled_end: datetime | None,
        title: str | None,
        current_user: User,
    ) -> GameSession:
        """
        Copy/duplicate an existing session (#33).

        Creates a new session in DRAFT status with the same properties.
        Useful for recurring sessions or similar events.

        Can be done by: session creator (GM), organizers, or super admin.
        """
        original = await self._get_session(session_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        # Check permission
        can_copy = (
            original.created_by_user_id == current_user.id
            or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]
        )
        if not can_copy:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot copy this session",
            )

        # Determine target time slot and schedule
        target_time_slot_id = time_slot_id or original.time_slot_id
        target_start = scheduled_start or original.scheduled_start
        target_end = scheduled_end or original.scheduled_end

        # Validate time slot if changed
        if time_slot_id and time_slot_id != original.time_slot_id:
            time_slot = await self._get_time_slot(time_slot_id)
            if not time_slot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Time slot not found",
                )
            if time_slot.exhibition_id != original.exhibition_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Time slot does not belong to this exhibition",
                )
            # Require new times if slot changed
            if not scheduled_start or not scheduled_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="scheduled_start and scheduled_end are required when changing time slot",
                )
            # Validate schedule within new time slot
            if target_start < time_slot.start_time or target_end > time_slot.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule must be within the time slot bounds",
                )

        # Generate title
        new_title = title or f"Copy of {original.title}"

        # Create the copy
        copied_session = GameSession(
            exhibition_id=original.exhibition_id,
            time_slot_id=target_time_slot_id,
            game_id=original.game_id,
            provided_by_group_id=original.provided_by_group_id,
            created_by_user_id=current_user.id,
            title=new_title,
            description=original.description,
            language=original.language,
            min_age=original.min_age,
            max_players_count=original.max_players_count,
            safety_tools=original.safety_tools,
            is_accessible_disability=original.is_accessible_disability,
            scheduled_start=target_start,
            scheduled_end=target_end,
            status=SessionStatus.DRAFT,
        )

        self.db.add(copied_session)
        await self.db.flush()
        await self.db.refresh(copied_session)

        return copied_session

    # =========================================================================
    # Booking Operations
    # =========================================================================

    async def create_booking(
        self,
        data: BookingCreate,
        current_user: User,
    ) -> Booking:
        """
        Register a user to a game session.

        Validates:
        - Session is validated
        - User is not already registered
        - User has no overlapping bookings
        - Session has available slots (or waitlist)
        """
        session = await self._get_session(data.game_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        if session.status != SessionStatus.VALIDATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only book validated sessions",
            )

        # Check minimum age requirement
        if session.min_age is not None:
            user_age = current_user.get_age()
            if user_age is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This session requires a minimum age of {session.min_age}. "
                           "Please update your profile with your birth date.",
                )
            if user_age < session.min_age:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You must be at least {session.min_age} years old to join this session",
                )

        # Check not already registered
        existing = await self.db.execute(
            select(Booking).where(
                Booking.game_session_id == data.game_session_id,
                Booking.user_id == current_user.id,
                Booking.status.notin_([BookingStatus.CANCELLED]),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already registered for this session",
            )

        # Check for overlapping bookings (Issue #5)
        overlapping = await self._check_booking_overlap(
            user_id=current_user.id,
            exhibition_id=session.exhibition_id,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
        )
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You have an overlapping booking for session '{overlapping.title}' "
                       f"({overlapping.scheduled_start.strftime('%H:%M')} - {overlapping.scheduled_end.strftime('%H:%M')})",
            )

        # Count current confirmed bookings
        confirmed_count = await self.db.execute(
            select(func.count(Booking.id)).where(
                Booking.game_session_id == data.game_session_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            )
        )
        current_count = confirmed_count.scalar() or 0

        # Determine booking status
        if current_count < session.max_players_count:
            booking_status = BookingStatus.CONFIRMED
        else:
            booking_status = BookingStatus.WAITING_LIST

        booking = Booking(
            game_session_id=data.game_session_id,
            user_id=current_user.id,
            role=data.role,
            status=booking_status,
        )
        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)

        return booking

    async def cancel_booking(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        """
        Cancel a booking.

        May promote someone from waitlist.
        """
        booking = await self._get_booking(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        # Check ownership
        if booking.user_id != current_user.id and current_user.global_role != GlobalRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot cancel this booking",
            )

        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled",
            )

        was_confirmed = booking.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
        booking.status = BookingStatus.CANCELLED
        await self.db.flush()

        # Promote from waitlist if spot opened
        if was_confirmed:
            await self._promote_from_waitlist(booking.game_session_id)

        await self.db.refresh(booking)
        return booking

    async def check_in_booking(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        """
        Check in a booking.

        Can be done by: booking owner, session creator, or organizer.
        """
        booking = await self._get_booking(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        session = await self._get_session(booking.game_session_id)

        # Check permission
        can_check_in = (
            booking.user_id == current_user.id
            or session.created_by_user_id == current_user.id
            or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]
        )
        if not can_check_in:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot check in this booking",
            )

        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot check in a {booking.status} booking",
            )

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = func.now()
        await self.db.flush()
        await self.db.refresh(booking)

        return booking

    async def mark_no_show(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        """
        Mark a booking as no-show.

        Can be done by: session creator (GM) or organizer.
        Frees up a spot and may promote someone from waitlist.
        """
        booking = await self._get_booking(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        session = await self._get_session(booking.game_session_id)

        # Check permission - only GM or organizers can mark no-show
        can_mark = (
            session.created_by_user_id == current_user.id
            or current_user.global_role in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]
        )
        if not can_mark:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the GM or organizers can mark no-shows",
            )

        if booking.status not in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark a {booking.status} booking as no-show",
            )

        booking.status = BookingStatus.NO_SHOW
        await self.db.flush()

        # Promote from waitlist since spot is now free
        await self._promote_from_waitlist(booking.game_session_id)

        await self.db.refresh(booking)
        return booking

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_exhibition(self, exhibition_id: UUID) -> Optional[Exhibition]:
        result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        return result.scalar_one_or_none()

    async def _get_time_slot(self, time_slot_id: UUID) -> Optional[TimeSlot]:
        result = await self.db.execute(
            select(TimeSlot).where(TimeSlot.id == time_slot_id)
        )
        return result.scalar_one_or_none()

    async def _get_game(self, game_id: UUID) -> Optional[Game]:
        result = await self.db.execute(
            select(Game).where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

    async def _get_session(self, session_id: UUID) -> Optional[GameSession]:
        result = await self.db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def _get_booking(self, booking_id: UUID) -> Optional[Booking]:
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    def _can_edit_session(self, session: GameSession, user: User) -> bool:
        """Check if user can edit the session."""
        if user.global_role == GlobalRole.SUPER_ADMIN:
            return True
        if session.created_by_user_id == user.id:
            return True
        return False

    async def _promote_from_waitlist(self, session_id: UUID) -> None:
        """Promote the first person from waitlist to confirmed."""
        result = await self.db.execute(
            select(Booking)
            .where(
                Booking.game_session_id == session_id,
                Booking.status == BookingStatus.WAITING_LIST,
            )
            .order_by(Booking.registered_at)
            .limit(1)
        )
        next_in_line = result.scalar_one_or_none()
        if next_in_line:
            next_in_line.status = BookingStatus.CONFIRMED
            await self.db.flush()

    async def _check_booking_overlap(
        self,
        user_id: UUID,
        exhibition_id: UUID,
        scheduled_start,
        scheduled_end,
        exclude_session_id: Optional[UUID] = None,
    ) -> Optional[GameSession]:
        """
        Check if user has an overlapping booking in the same exhibition.

        Returns the conflicting session if found, None otherwise.
        """
        # Find active bookings for this user in the same exhibition
        # that overlap with the given time range
        query = (
            select(GameSession)
            .join(Booking, Booking.game_session_id == GameSession.id)
            .where(
                Booking.user_id == user_id,
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.CHECKED_IN,
                    BookingStatus.WAITING_LIST,
                ]),
                GameSession.exhibition_id == exhibition_id,
                # Overlap check
                GameSession.scheduled_start < scheduled_end,
                GameSession.scheduled_end > scheduled_start,
            )
        )

        if exclude_session_id:
            query = query.where(GameSession.id != exclude_session_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _check_gm_session_overlap(
        self,
        user_id: UUID,
        exhibition_id: UUID,
        scheduled_start,
        scheduled_end,
        exclude_session_id: Optional[UUID] = None,
    ) -> Optional[GameSession]:
        """
        Check if user is already running a session that overlaps.

        A GM cannot run two sessions at the same time.
        Only considers non-draft sessions (submitted or validated).

        Returns the conflicting session if found, None otherwise.
        """
        query = select(GameSession).where(
            GameSession.created_by_user_id == user_id,
            GameSession.exhibition_id == exhibition_id,
            GameSession.status.notin_([SessionStatus.DRAFT, SessionStatus.REJECTED, SessionStatus.CANCELLED]),
            # Overlap check
            GameSession.scheduled_start < scheduled_end,
            GameSession.scheduled_end > scheduled_start,
        )

        if exclude_session_id:
            query = query.where(GameSession.id != exclude_session_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _check_table_collision(
        self,
        table_id: UUID,
        scheduled_start,
        scheduled_end,
        buffer_minutes: int,
        exclude_session_id: Optional[UUID] = None,
    ) -> Optional[GameSession]:
        """
        Check if assigning a table would cause a collision.

        A collision occurs when another session on the same table
        overlaps with the given time range (including buffer time).

        Returns the conflicting session if found, None otherwise.
        """
        # Add buffer to the time range
        buffered_start = scheduled_start - timedelta(minutes=buffer_minutes)
        buffered_end = scheduled_end + timedelta(minutes=buffer_minutes)

        # Find overlapping sessions on the same table
        query = select(GameSession).where(
            GameSession.physical_table_id == table_id,
            GameSession.status.in_([
                SessionStatus.VALIDATED,
                SessionStatus.IN_PROGRESS,
            ]),
            # Overlap check: sessions overlap if one starts before the other ends
            # (A.start < B.end) AND (A.end > B.start)
            GameSession.scheduled_start < buffered_end,
            GameSession.scheduled_end > buffered_start,
        )

        if exclude_session_id:
            query = query.where(GameSession.id != exclude_session_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def assign_table(
        self,
        session_id: UUID,
        table_id: UUID,
        current_user: User,
    ) -> GameSession:
        """
        Assign a physical table to a session.

        Validates:
        - Session exists and is validated
        - Table exists
        - No collision with other sessions (respecting buffer time)
        """
        session = await self._get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found",
            )

        # Check permission
        if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ORGANIZER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organizers can assign tables",
            )

        # Check table exists
        result = await self.db.execute(
            select(PhysicalTable).where(PhysicalTable.id == table_id)
        )
        table = result.scalar_one_or_none()
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical table not found",
            )

        # Get buffer time from time slot
        time_slot = await self._get_time_slot(session.time_slot_id)
        buffer_minutes = time_slot.buffer_time_minutes if time_slot else 0

        # Check for collisions
        conflicting = await self._check_table_collision(
            table_id=table_id,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            buffer_minutes=buffer_minutes,
            exclude_session_id=session_id,
        )

        if conflicting:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Table collision: another session '{conflicting.title}' "
                       f"is scheduled from {conflicting.scheduled_start} to {conflicting.scheduled_end}",
            )

        session.physical_table_id = table_id
        await self.db.flush()
        await self.db.refresh(session)

        return session
