"""
GameSession service layer.

Contains business logic for game sessions, bookings, and workflow.
"""
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.game.entity import GameSession, Game, Booking
from app.domain.game.schemas import (
    GameSessionCreate,
    GameSessionUpdate,
    GameSessionModerate,
    BookingCreate,
)
from app.domain.exhibition.entity import Exhibition, TimeSlot, PhysicalTable
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
                detail=f"Cannot check in a {booking.status.value} booking",
            )

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = func.now()
        await self.db.flush()
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
