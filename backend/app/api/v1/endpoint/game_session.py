"""
GameSession API endpoints.

Session management, workflow, and bookings.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.i18n import parse_accept_language
from app.domain.game.entity import GameSession, Booking
from app.domain.game.schemas import (
    GameSessionCreate,
    GameSessionRead,
    GameSessionUpdate,
    GameSessionModerate,
    BookingCreate,
    BookingCreateBody,
    BookingRead,
    SessionFilters,
    SessionSearchResult,
    SessionCancelRequest,
    SessionCancellationResult,
    SessionCopyRequest,
    ModerationCommentCreate,
    ModerationCommentRead,
    SessionEndReport,
)
from app.domain.user.entity import User
from app.domain.exhibition.entity import Exhibition
from app.api.deps import get_current_active_user, get_current_verified_user
from app.services.game_session import GameSessionService
from app.services.notification import (
    NotificationService,
    NotificationRecipient,
    SessionNotificationContext,
)

router = APIRouter()


# =============================================================================
# GameSession CRUD
# =============================================================================

@router.get("/", response_model=List[GameSessionRead])
async def list_sessions(
    exhibition_id: UUID,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List game sessions for an exhibition.

    Optional filters:
    - status: filter by session status (DRAFT, PENDING_MODERATION, VALIDATED, etc.)
    """
    query = select(GameSession).where(GameSession.exhibition_id == exhibition_id)

    if status:
        query = query.where(GameSession.status == status)

    query = query.order_by(GameSession.scheduled_start)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search", response_model=List[SessionSearchResult])
async def search_sessions(
    exhibition_id: UUID,
    category_id: Optional[UUID] = Query(None, description="Filter by game category"),
    language: Optional[str] = Query(None, description="Filter by language (en, fr)"),
    is_accessible_disability: Optional[bool] = Query(None, description="Accessibility filter"),
    max_age_requirement: Optional[int] = Query(None, ge=0, le=99, description="Max age requirement"),
    has_available_seats: Optional[bool] = Query(None, description="Only sessions with seats"),
    zone_id: Optional[UUID] = Query(None, description="Filter by zone"),
    time_slot_id: Optional[UUID] = Query(None, description="Filter by time slot"),
    starts_after: Optional[datetime] = Query(None, description="Sessions starting after"),
    starts_before: Optional[datetime] = Query(None, description="Sessions starting before"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search sessions with advanced filters for player discovery (JS.C1, JS.C6).

    Returns validated sessions with availability info.

    Filters:
    - category_id: Game type (RPG, Board Game, etc.)
    - language: Session language (en, fr, etc.)
    - is_accessible_disability: Accessibility for people with disabilities
    - max_age_requirement: Show sessions accessible to this age
    - has_available_seats: Only sessions with available spots
    - zone_id: Physical zone location
    - time_slot_id: Time slot
    - starts_after/starts_before: Time range
    """
    filters = SessionFilters(
        category_id=category_id,
        language=language,
        is_accessible_disability=is_accessible_disability,
        max_age_requirement=max_age_requirement,
        has_available_seats=has_available_seats,
        zone_id=zone_id,
        time_slot_id=time_slot_id,
        starts_after=starts_after,
        starts_before=starts_before,
    )

    service = GameSessionService(db)
    return await service.search_sessions(exhibition_id, filters)


@router.post("/", response_model=GameSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: GameSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Create a new game session.

    The session is created in DRAFT status.
    Submit for moderation using POST /{id}/submit.
    """
    locale = parse_accept_language(accept_language)
    if current_user.locale:
        locale = current_user.locale
    service = GameSessionService(db)
    return await service.create_session(session_in, current_user, locale)


@router.get("/{session_id}", response_model=SessionSearchResult)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single game session by ID with computed fields."""
    from sqlalchemy import func
    from app.domain.organization.entity import UserGroup
    from app.domain.exhibition.entity import PhysicalTable, Zone
    from app.domain.game.entity import Game, GameCategory
    from app.domain.user.entity import User
    from app.domain.shared.entity import BookingStatus

    result = await db.execute(
        select(
            GameSession,
            UserGroup.name.label("group_name"),
            Game.title.label("game_title"),
            GameCategory.slug.label("category_slug"),
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            User.full_name.label("gm_name"),
            Game.cover_image_url.label("game_cover_image_url"),
            Game.external_url.label("game_external_url"),
            Game.external_provider.label("game_external_provider"),
            Game.themes.label("game_themes"),
        )
        .outerjoin(UserGroup, GameSession.provided_by_group_id == UserGroup.id)
        .outerjoin(Game, GameSession.game_id == Game.id)
        .outerjoin(GameCategory, Game.category_id == GameCategory.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .outerjoin(User, GameSession.created_by_user_id == User.id)
        .where(GameSession.id == session_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    session = row[0]
    group_name = row[1]
    game_title = row[2]
    category_slug = row[3]
    zone_name = row[4]
    table_label = row[5]
    gm_name = row[6]
    game_cover_image_url = row[7]
    game_external_url = row[8]
    game_external_provider = row[9]
    game_themes = row[10]

    # Count confirmed bookings
    confirmed_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.game_session_id == session.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
        )
    )
    confirmed_count = confirmed_result.scalar() or 0

    # Count waitlist
    waitlist_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.game_session_id == session.id,
            Booking.status == BookingStatus.WAITING_LIST,
        )
    )
    waitlist_count = waitlist_result.scalar() or 0

    available_seats = max(0, session.max_players_count - confirmed_count)

    return SessionSearchResult(
        id=session.id,
        exhibition_id=session.exhibition_id,
        time_slot_id=session.time_slot_id,
        game_id=session.game_id,
        physical_table_id=session.physical_table_id,
        provided_by_group_id=session.provided_by_group_id,
        provided_by_group_name=group_name,
        created_by_user_id=session.created_by_user_id,
        title=session.title,
        description=session.description,
        language=session.language,
        min_age=session.min_age,
        max_players_count=session.max_players_count,
        safety_tools=session.safety_tools,
        is_accessible_disability=session.is_accessible_disability,
        status=session.status,
        rejection_reason=session.rejection_reason,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        gm_checked_in_at=session.gm_checked_in_at,
        actual_start=session.actual_start,
        actual_end=session.actual_end,
        created_at=session.created_at,
        updated_at=session.updated_at,
        # Computed fields
        available_seats=available_seats,
        confirmed_players_count=confirmed_count,
        waitlist_count=waitlist_count,
        has_available_seats=available_seats > 0,
        category_slug=category_slug,
        zone_name=zone_name,
        table_label=table_label,
        game_title=game_title,
        gm_name=gm_name,
        game_cover_image_url=game_cover_image_url,
        game_external_url=game_external_url,
        game_external_provider=game_external_provider,
        game_themes=game_themes,
    )


@router.put("/{session_id}", response_model=GameSessionRead)
async def update_session(
    session_id: UUID,
    session_in: GameSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a game session.

    Only draft sessions can be fully edited.
    Validated sessions have limited editable fields.
    """
    service = GameSessionService(db)
    return await service.update_session(session_id, session_in, current_user)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a game session.

    Only draft sessions can be deleted.
    """
    service = GameSessionService(db)
    await service.delete_session(session_id, current_user)


# =============================================================================
# Table Assignment
# =============================================================================

@router.post("/{session_id}/assign-table", response_model=GameSessionRead)
async def assign_table(
    session_id: UUID,
    table_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Assign a physical table to a session.

    Validates:
    - No collision with other sessions on the same table
    - Respects buffer time between sessions

    Requires: Organizer or SUPER_ADMIN.
    """
    locale = parse_accept_language(accept_language)
    if current_user.locale:
        locale = current_user.locale
    service = GameSessionService(db)
    return await service.assign_table(session_id, table_id, current_user, locale)


# =============================================================================
# Workflow Endpoints
# =============================================================================

@router.post("/{session_id}/submit", response_model=GameSessionRead)
async def submit_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a session for moderation.

    Transitions: DRAFT -> PENDING_MODERATION
    """
    service = GameSessionService(db)
    return await service.submit_for_moderation(session_id, current_user)


@router.post("/{session_id}/moderate", response_model=GameSessionRead)
async def moderate_session(
    session_id: UUID,
    moderation: GameSessionModerate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Approve, reject, or request changes on a session (#30).

    Actions:
    - approve: Validate the session
    - reject: Reject with reason
    - request_changes: Ask proposer to modify (adds comment to dialogue)

    Body examples:
    - { "action": "approve" }
    - { "action": "reject", "rejection_reason": "..." }
    - { "action": "request_changes", "comment": "Please add safety tools" }

    Requires: Organizer, SUPER_ADMIN, or zone manager.
    """
    locale = parse_accept_language(accept_language)
    if current_user.locale:
        locale = current_user.locale
    service = GameSessionService(db)
    return await service.moderate_session(session_id, moderation, current_user, locale)


# =============================================================================
# Moderation Comments (#30)
# =============================================================================

@router.get("/{session_id}/comments", response_model=List[ModerationCommentRead])
async def list_moderation_comments(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List moderation comments for a session (#30).

    Returns the dialogue thread between proposer and moderators.

    Can be viewed by: session creator, organizers, or zone managers.
    """
    service = GameSessionService(db)
    return await service.list_moderation_comments(session_id, current_user)


@router.post("/{session_id}/comments", response_model=ModerationCommentRead, status_code=status.HTTP_201_CREATED)
async def create_moderation_comment(
    session_id: UUID,
    comment: ModerationCommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a comment to the moderation dialogue (#30).

    Enables two-way communication during the moderation process.
    Only allowed on sessions in PENDING_MODERATION or CHANGES_REQUESTED status.

    Can be posted by: session creator, organizers, or zone managers.
    """
    service = GameSessionService(db)
    return await service.create_moderation_comment(session_id, comment, current_user)


@router.post("/{session_id}/cancel", response_model=SessionCancellationResult)
async def cancel_session(
    session_id: UUID,
    cancel_request: SessionCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a session and notify registered players (JS.B4).

    Cancels the session and all associated bookings.
    Sends notifications to all affected users.

    Can be done by: session creator (GM), organizers, or super admin.

    Body: { "reason": "Reason for cancellation" }
    """
    service = GameSessionService(db)
    session, affected_users = await service.cancel_session(
        session_id, cancel_request.reason, current_user
    )

    # Get exhibition info for notification
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == session.exhibition_id)
    )
    exhibition = exhibition_result.scalar_one()

    # Send notifications
    notifications_sent = 0
    if affected_users:
        notification_service = NotificationService(db)
        recipients = [
            NotificationRecipient(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                locale=user.locale or "en",
            )
            for user in affected_users
        ]
        context = SessionNotificationContext(
            session_id=session.id,
            session_title=session.title,
            exhibition_id=exhibition.id,
            exhibition_title=exhibition.title,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            cancellation_reason=cancel_request.reason,
        )
        notifications_sent = await notification_service.notify_session_cancelled(
            recipients, context
        )

    return SessionCancellationResult(
        session=session,
        affected_users=affected_users,
        notifications_sent=notifications_sent,
    )


@router.post("/{session_id}/copy", response_model=GameSessionRead, status_code=status.HTTP_201_CREATED)
async def copy_session(
    session_id: UUID,
    copy_request: SessionCopyRequest = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Copy/duplicate an existing session (#33).

    Creates a new session in DRAFT status with the same properties as the original.
    Useful for recurring sessions or creating similar events.

    Optional parameters:
    - time_slot_id: Target a different time slot (same exhibition)
    - scheduled_start/end: New schedule (required if time_slot_id changes)
    - title: Custom title (defaults to "Copy of [original]")

    Can be done by: session creator (GM), organizers, or super admin.
    """
    if copy_request is None:
        copy_request = SessionCopyRequest()

    service = GameSessionService(db)
    return await service.copy_session(
        session_id=session_id,
        time_slot_id=copy_request.time_slot_id,
        scheduled_start=copy_request.scheduled_start,
        scheduled_end=copy_request.scheduled_end,
        title=copy_request.title,
        current_user=current_user,
    )


# =============================================================================
# Session Reporting (#35 - JS.B8)
# =============================================================================

@router.post("/{session_id}/start", response_model=GameSessionRead)
async def start_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a session as started (#35).

    Sets actual_start timestamp and transitions to IN_PROGRESS if not already.
    Also sets gm_checked_in_at if not already set.

    Can be done by: session creator (GM), organizers, or super admin.
    """
    service = GameSessionService(db)
    return await service.start_session(session_id, current_user)


@router.post("/{session_id}/end", response_model=GameSessionRead)
async def end_session(
    session_id: UUID,
    report: SessionEndReport = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a session as ended with a report (#35).

    Sets actual_end timestamp, records report data, transitions to FINISHED.

    Optional report fields:
    - actual_player_count: How many players actually attended
    - table_condition: CLEAN, NEEDS_CLEANING, or DAMAGED
    - notes: Any additional notes about the session

    Can be done by: session creator (GM), organizers, or super admin.
    """
    if report is None:
        report = SessionEndReport()

    service = GameSessionService(db)
    return await service.end_session(session_id, report, current_user)


# =============================================================================
# Booking Endpoints
# =============================================================================

@router.get("/{session_id}/bookings", response_model=List[BookingRead])
async def list_bookings(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all bookings for a session with user info."""
    # Check session exists
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    # Fetch bookings with user info
    from sqlalchemy.orm import selectinload
    bookings_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.user))
        .where(Booking.game_session_id == session_id)
        .order_by(Booking.registered_at)
    )
    bookings = bookings_result.scalars().all()

    # Build response with user info
    return [
        BookingRead(
            id=b.id,
            game_session_id=b.game_session_id,
            user_id=b.user_id,
            role=b.role,
            status=b.status,
            registered_at=b.registered_at,
            checked_in_at=b.checked_in_at,
            updated_at=b.updated_at,
            user_name=b.user.full_name if b.user else None,
            user_email=b.user.email if b.user else None,
        )
        for b in bookings
    ]


@router.post("/{session_id}/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    session_id: UUID,
    booking_in: BookingCreateBody,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register for a game session.

    Requires email verification.
    If session is full, booking goes to waitlist.
    """
    from sqlalchemy import func
    from app.domain.shared.entity import BookingStatus

    # Build full BookingCreate from path + body
    booking_data = BookingCreate(
        game_session_id=session_id,
        role=booking_in.role,
    )
    service = GameSessionService(db)
    booking = await service.create_booking(booking_data, current_user)

    # Send notifications for both confirmed and waitlisted bookings
    # Notifications are non-blocking - if they fail, the booking still succeeds
    if booking.status in (BookingStatus.CONFIRMED, BookingStatus.WAITING_LIST):
        try:
            # Get session and exhibition info
            session_result = await db.execute(
                select(GameSession).where(GameSession.id == session_id)
            )
            session = session_result.scalar_one()

            exhibition_result = await db.execute(
                select(Exhibition).where(Exhibition.id == session.exhibition_id)
            )
            exhibition = exhibition_result.scalar_one()

            # Get GM info
            gm_result = await db.execute(
                select(User).where(User.id == session.created_by_user_id)
            )
            gm = gm_result.scalar_one()

            notification_service = NotificationService(db)

            # Build base context
            context = SessionNotificationContext(
                session_id=session.id,
                session_title=session.title,
                exhibition_id=exhibition.id,
                exhibition_title=exhibition.title,
                scheduled_start=session.scheduled_start,
                scheduled_end=session.scheduled_end,
                gm_name=gm.full_name,
                player_name=current_user.full_name or current_user.email,
            )

            # Set up recipients
            player_recipient = NotificationRecipient(
                user_id=current_user.id,
                email=current_user.email,
                full_name=current_user.full_name,
                locale=current_user.locale or "en",
            )
            gm_recipient = NotificationRecipient(
                user_id=gm.id,
                email=gm.email,
                full_name=gm.full_name,
                locale=gm.locale or "en",
            )

            if booking.status == BookingStatus.CONFIRMED:
                # Count current confirmed bookings
                confirmed_result = await db.execute(
                    select(func.count(Booking.id)).where(
                        Booking.game_session_id == session_id,
                        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
                    )
                )
                confirmed_count = confirmed_result.scalar() or 0
                context.players_registered = confirmed_count
                context.max_players = session.max_players_count

                # Notify player of confirmed booking
                await notification_service.notify_booking_confirmed(player_recipient, context)
                # Notify GM of new confirmed player
                await notification_service.notify_gm_new_player(gm_recipient, context)

            else:  # WAITING_LIST
                # Count waitlist position
                waitlist_result = await db.execute(
                    select(func.count(Booking.id)).where(
                        Booking.game_session_id == session_id,
                        Booking.status == BookingStatus.WAITING_LIST,
                        Booking.registered_at <= booking.registered_at,
                    )
                )
                waitlist_position = waitlist_result.scalar() or 1

                # Count total waitlist
                total_waitlist_result = await db.execute(
                    select(func.count(Booking.id)).where(
                        Booking.game_session_id == session_id,
                        Booking.status == BookingStatus.WAITING_LIST,
                    )
                )
                total_waitlist = total_waitlist_result.scalar() or 1

                # Notify player they joined waitlist
                await notification_service.notify_waitlist_joined(
                    player_recipient, context, waitlist_position
                )
                # Notify GM of new waitlist player
                await notification_service.notify_gm_new_waitlist_player(
                    gm_recipient, context, total_waitlist
                )

        except Exception as e:
            # Log error but don't fail the booking
            import logging
            logging.getLogger(__name__).error(f"Failed to send booking notifications: {e}")

    return booking


@router.delete("/bookings/{booking_id}", response_model=BookingRead)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a booking.

    May promote someone from waitlist.
    """
    from sqlalchemy import func
    from app.domain.shared.entity import BookingStatus

    # Get booking info before cancellation
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking_before = booking_result.scalar_one_or_none()
    if not booking_before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    was_confirmed = booking_before.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    session_id = booking_before.game_session_id

    # Get session and exhibition info
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one()

    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == session.exhibition_id)
    )
    exhibition = exhibition_result.scalar_one()

    # Get player and GM info
    player_result = await db.execute(
        select(User).where(User.id == booking_before.user_id)
    )
    player = player_result.scalar_one()

    gm_result = await db.execute(
        select(User).where(User.id == session.created_by_user_id)
    )
    gm = gm_result.scalar_one()

    # Perform the cancellation
    service = GameSessionService(db)
    booking, promoted_booking = await service.cancel_booking(booking_id, current_user)

    # Send notifications - different email for confirmed vs waitlisted
    # Notifications are non-blocking - if they fail, the cancellation still succeeds
    try:
        notification_service = NotificationService(db)

        # Build location string for notifications
        location_parts = []
        if session.physical_table_id:
            from app.domain.exhibition.entity import Zone, PhysicalTable
            table_result = await db.execute(
                select(PhysicalTable.label, Zone.name)
                .join(Zone, PhysicalTable.zone_id == Zone.id)
                .where(PhysicalTable.id == session.physical_table_id)
            )
            table_row = table_result.one_or_none()
            if table_row:
                location_parts = [table_row[1], table_row[0]]

        # Build context
        context = SessionNotificationContext(
            session_id=session.id,
            session_title=session.title,
            exhibition_id=exhibition.id,
            exhibition_title=exhibition.title,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            gm_name=gm.full_name,
            player_name=player.full_name or player.email,
            max_players=session.max_players_count,
            location=" - ".join(filter(None, location_parts)) or None,
        )

        # Notify player
        player_recipient = NotificationRecipient(
            user_id=player.id,
            email=player.email,
            full_name=player.full_name,
            locale=player.locale or "en",
        )

        if was_confirmed:
            # Count remaining confirmed bookings (for GM notification)
            confirmed_result = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.game_session_id == session_id,
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
                )
            )
            context.players_registered = confirmed_result.scalar() or 0

            # Send booking cancelled email to player
            await notification_service.notify_booking_cancelled_to_player(player_recipient, context)

            # Notify GM about player cancellation
            gm_recipient = NotificationRecipient(
                user_id=gm.id,
                email=gm.email,
                full_name=gm.full_name,
                locale=gm.locale or "en",
            )
            await notification_service.notify_gm_player_cancelled(gm_recipient, context)

            # Notify promoted user from waitlist
            if promoted_booking:
                promoted_user_result = await db.execute(
                    select(User).where(User.id == promoted_booking.user_id)
                )
                promoted_user = promoted_user_result.scalar_one()
                promoted_recipient = NotificationRecipient(
                    user_id=promoted_user.id,
                    email=promoted_user.email,
                    full_name=promoted_user.full_name,
                    locale=promoted_user.locale or "en",
                )
                await notification_service.notify_waitlist_promoted(
                    promoted_recipient, context,
                    action_url=f"/sessions/{session.id}",
                )
                # Notify GM about waitlist promotion
                promoted_context = SessionNotificationContext(
                    session_id=session.id,
                    session_title=session.title,
                    exhibition_id=exhibition.id,
                    exhibition_title=exhibition.title,
                    scheduled_start=session.scheduled_start,
                    scheduled_end=session.scheduled_end,
                    gm_name=gm.full_name,
                    player_name=promoted_user.full_name or promoted_user.email,
                    players_registered=context.players_registered,
                    max_players=session.max_players_count,
                    location=context.location,
                )
                await notification_service.notify_gm_waitlist_promoted(
                    gm_recipient, promoted_context,
                    action_url=f"/sessions/{session.id}",
                )
        else:
            # Send waitlist cancelled email to player (no GM notification for waitlist)
            await notification_service.notify_waitlist_cancelled_to_player(player_recipient, context)
    except Exception as e:
        # Log error but don't fail the cancellation
        import logging
        logging.getLogger(__name__).error(f"Failed to send cancellation notifications: {e}")

    return booking


@router.post("/bookings/{booking_id}/check-in", response_model=BookingRead)
async def check_in_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check in a booking.

    Can be done by: booking owner, session creator, or organizer.
    """
    service = GameSessionService(db)
    return await service.check_in_booking(booking_id, current_user)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingRead)
async def mark_no_show(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a booking as no-show.

    Frees up a spot and may promote someone from waitlist.

    Can be done by: session creator (GM) or organizer.
    """
    service = GameSessionService(db)
    booking, promoted_booking = await service.mark_no_show(booking_id, current_user)

    # Send notification to promoted user
    if promoted_booking:
        try:
            # Load session, exhibition, GM and promoted user info
            session_result = await db.execute(
                select(GameSession).where(GameSession.id == booking.game_session_id)
            )
            session = session_result.scalar_one()

            exhibition_result = await db.execute(
                select(Exhibition).where(Exhibition.id == session.exhibition_id)
            )
            exhibition = exhibition_result.scalar_one()

            gm_result = await db.execute(
                select(User).where(User.id == session.created_by_user_id)
            )
            gm = gm_result.scalar_one()

            promoted_user_result = await db.execute(
                select(User).where(User.id == promoted_booking.user_id)
            )
            promoted_user = promoted_user_result.scalar_one()

            # Build location
            location = None
            if session.physical_table_id:
                from app.domain.exhibition.entity import Zone, PhysicalTable
                table_result = await db.execute(
                    select(PhysicalTable.label, Zone.name)
                    .join(Zone, PhysicalTable.zone_id == Zone.id)
                    .where(PhysicalTable.id == session.physical_table_id)
                )
                table_row = table_result.one_or_none()
                if table_row:
                    location = " - ".join(filter(None, [table_row[1], table_row[0]]))

            context = SessionNotificationContext(
                session_id=session.id,
                session_title=session.title,
                exhibition_id=exhibition.id,
                exhibition_title=exhibition.title,
                scheduled_start=session.scheduled_start,
                scheduled_end=session.scheduled_end,
                gm_name=gm.full_name,
                player_name=promoted_user.full_name or promoted_user.email,
                max_players=session.max_players_count,
                location=location,
            )

            promoted_recipient = NotificationRecipient(
                user_id=promoted_user.id,
                email=promoted_user.email,
                full_name=promoted_user.full_name,
                locale=promoted_user.locale or "en",
            )

            notification_service = NotificationService(db)
            await notification_service.notify_waitlist_promoted(
                promoted_recipient, context,
                action_url=f"/sessions/{session.id}",
            )

            # Notify GM about waitlist promotion
            from sqlalchemy import func
            from app.domain.shared.entity import BookingStatus as BS
            confirmed_result = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.game_session_id == session.id,
                    Booking.status.in_([BS.CONFIRMED, BS.CHECKED_IN]),
                )
            )
            context.players_registered = confirmed_result.scalar() or 0

            gm_recipient = NotificationRecipient(
                user_id=gm.id,
                email=gm.email,
                full_name=gm.full_name,
                locale=gm.locale or "en",
            )
            await notification_service.notify_gm_waitlist_promoted(
                gm_recipient, context,
                action_url=f"/sessions/{session.id}",
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send waitlist promotion notification: {e}")

    return booking


@router.get("/{session_id}/my-booking", response_model=Optional[BookingRead])
async def get_my_booking(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's booking for a session, if any.

    Returns the booking if the user has registered for this session,
    or null if they haven't.
    """
    from app.domain.shared.entity import BookingStatus

    result = await db.execute(
        select(Booking)
        .where(Booking.game_session_id == session_id)
        .where(Booking.user_id == current_user.id)
        .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.WAITING_LIST]))
    )
    return result.scalar_one_or_none()
