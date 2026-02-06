"""
User API endpoints.

User profile and dashboard (JS.B6).
"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.database import get_db
from app.core.email import EmailMessage, get_email_backend
from app.core.templates import render_email_change, render_password_changed
from app.domain.user.entity import User
from app.core.security import verify_password, get_password_hash
from app.domain.user.schemas import (
    UserRead,
    UserProfileUpdate,
    MySessionSummary,
    MyBookingSummary,
    UserAgenda,
    SessionConflict,
    MyExhibitions,
)
from app.domain.game.entity import Game, GameSession, Booking
from app.domain.exhibition.entity import Exhibition, Zone, PhysicalTable, ExhibitionRegistration
from app.domain.exhibition.schemas import ExhibitionRead
from app.domain.user.entity import UserExhibitionRole
from app.domain.shared.entity import SessionStatus, BookingStatus, ExhibitionStatus, GlobalRole
from app.api.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def _parse_locale_from_header(accept_language: Optional[str]) -> str:
    """Extract locale from Accept-Language header, defaulting to 'en'."""
    if not accept_language:
        return "en"
    first_lang = accept_language.split(",")[0].split(";")[0].strip()
    base_lang = first_lang.split("-")[0].lower()
    if base_lang in ("fr", "en"):
        return base_lang
    return "en"


# =============================================================================
# User Profile
# =============================================================================

@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)

    return current_user


# =============================================================================
# Password Change
# =============================================================================


class PasswordChangeRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)


@router.put("/me/password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update to new password
    current_user.hashed_password = get_password_hash(data.new_password)
    await db.flush()

    # Send notification email
    if settings.EMAIL_ENABLED:
        locale = _parse_locale_from_header(accept_language)
        changed_at = datetime.now(timezone.utc)
        subject, html_body = render_password_changed(
            locale=locale,
            changed_at=changed_at,
            user_name=current_user.full_name,
        )

        email_backend = get_email_backend()
        message = EmailMessage(
            to_email=current_user.email,
            to_name=current_user.full_name,
            subject=subject,
            body_html=html_body,
        )
        await email_backend.send(message)

    return {"message": "Password changed successfully"}


# =============================================================================
# Email Change
# =============================================================================

# Token expiration: 7 days
EMAIL_CHANGE_TOKEN_EXPIRATION_DAYS = 7


class EmailChangeRequest(BaseModel):
    """Schema for requesting email change."""
    new_email: EmailStr
    password: str = Field(..., description="Current password for verification")


class EmailChangeResponse(BaseModel):
    """Response for email change request."""
    message: str


class EmailChangeConfirmResponse(BaseModel):
    """Response for email change confirmation."""
    success: bool
    message: str


@router.put("/me/email", response_model=EmailChangeResponse)
async def request_email_change(
    data: EmailChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Request to change email address.

    Sends a verification email to the new address.
    The change is not applied until the new email is verified.
    """
    # Verify current password
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        )

    # Check if new email is the same as current
    if data.new_email.lower() == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email must be different from current email",
        )

    # Check if new email is already in use
    existing_user = await db.execute(
        select(User).where(User.email == data.new_email.lower())
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already in use",
        )

    # Generate verification token
    token = secrets.token_urlsafe(48)[:64]
    now = datetime.now(timezone.utc)

    # Store pending email change
    current_user.pending_email = data.new_email.lower()
    current_user.pending_email_token = token
    current_user.pending_email_sent_at = now
    await db.flush()

    # Build verification URL
    locale = _parse_locale_from_header(accept_language)
    frontend_base_url = settings.FRONTEND_URL
    verification_url = f"{frontend_base_url}/{locale}/auth/verify-email-change?token={token}"

    # Render and send email to NEW address
    subject, html_body = render_email_change(
        locale=locale,
        verification_url=verification_url,
        user_name=current_user.full_name,
    )

    if settings.EMAIL_ENABLED:
        email_backend = get_email_backend()
        message = EmailMessage(
            to_email=data.new_email,
            to_name=current_user.full_name,
            subject=subject,
            body_html=html_body,
        )
        await email_backend.send(message)

    await db.commit()

    return EmailChangeResponse(
        message="Verification email sent to your new address. Please check your inbox."
    )


@router.get("/me/email/verify", response_model=EmailChangeConfirmResponse)
async def verify_email_change(
    token: str = Query(..., description="Email change verification token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify and apply email change.

    Called when user clicks the verification link in the email sent to the new address.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required",
        )

    # Find user by pending email token
    result = await db.execute(
        select(User).where(User.pending_email_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Check token expiration
    if user.pending_email_sent_at:
        expiration = user.pending_email_sent_at + timedelta(
            days=EMAIL_CHANGE_TOKEN_EXPIRATION_DAYS
        )
        if datetime.now(timezone.utc) > expiration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

    # Check that pending email still doesn't exist (race condition)
    existing_user = await db.execute(
        select(User).where(User.email == user.pending_email)
    )
    if existing_user.scalar_one_or_none():
        # Clear pending change
        user.pending_email = None
        user.pending_email_token = None
        user.pending_email_sent_at = None
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is now in use by another account",
        )

    # Apply the email change
    user.email = user.pending_email
    user.email_verified = True  # New email is verified by this action
    user.pending_email = None
    user.pending_email_token = None
    user.pending_email_sent_at = None
    await db.commit()

    return EmailChangeConfirmResponse(
        success=True,
        message="Email address changed successfully",
    )


# =============================================================================
# User Dashboard / Agenda (JS.B6)
# =============================================================================

@router.get("/me/sessions", response_model=List[MySessionSummary])
async def list_my_sessions(
    exhibition_id: UUID = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List sessions created by the current user (as GM).

    Optionally filter by exhibition.
    """
    query = (
        select(
            GameSession,
            Exhibition.title.label("exhibition_title"),
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
        )
        .join(Exhibition, GameSession.exhibition_id == Exhibition.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(GameSession.created_by_user_id == current_user.id)
        .order_by(GameSession.scheduled_start)
    )

    if exhibition_id:
        query = query.where(GameSession.exhibition_id == exhibition_id)

    result = await db.execute(query)
    rows = result.all()

    sessions = []
    for row in rows:
        session = row[0]
        exhibition_title = row[1]
        zone_name = row[2]
        table_label = row[3]

        # Count confirmed and waitlist bookings
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session.id)
            .group_by(Booking.status)
        )
        counts = {row[0]: row[1] for row in booking_counts.fetchall()}

        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        sessions.append(MySessionSummary(
            id=session.id,
            title=session.title,
            exhibition_id=session.exhibition_id,
            exhibition_title=exhibition_title,
            status=session.status,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            zone_name=zone_name,
            table_label=table_label,
            max_players_count=session.max_players_count,
            confirmed_players=confirmed,
            waitlist_count=waitlist,
        ))

    return sessions


@router.get("/me/bookings", response_model=List[MyBookingSummary])
async def list_my_bookings(
    exhibition_id: UUID = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List bookings for the current user (as player).

    Optionally filter by exhibition.
    """
    query = (
        select(
            Booking,
            GameSession.title.label("session_title"),
            GameSession.scheduled_start,
            GameSession.scheduled_end,
            GameSession.exhibition_id,
            Exhibition.title.label("exhibition_title"),
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            User.full_name.label("gm_name"),
            GameSession.max_players_count,
            GameSession.id.label("session_id"),
        )
        .join(GameSession, Booking.game_session_id == GameSession.id)
        .join(Exhibition, GameSession.exhibition_id == Exhibition.id)
        .join(User, GameSession.created_by_user_id == User.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .where(Booking.user_id == current_user.id)
        .order_by(GameSession.scheduled_start)
    )

    if exhibition_id:
        query = query.where(GameSession.exhibition_id == exhibition_id)

    result = await db.execute(query)
    rows = result.all()

    bookings = []
    for row in rows:
        booking = row[0]
        session_id = row[10]

        # Count confirmed and waitlist bookings for this session
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session_id)
            .group_by(Booking.status)
        )
        counts = {r[0]: r[1] for r in booking_counts.fetchall()}
        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        bookings.append(MyBookingSummary(
            id=booking.id,
            game_session_id=booking.game_session_id,
            session_title=row[1],
            exhibition_id=row[4],
            exhibition_title=row[5],
            status=booking.status,
            role=booking.role,
            scheduled_start=row[2],
            scheduled_end=row[3],
            zone_name=row[6],
            table_label=row[7],
            gm_name=row[8],
            max_players_count=row[9],
            confirmed_players=confirmed,
            waitlist_count=waitlist,
        ))

    return bookings


@router.get("/me/agenda/{exhibition_id}", response_model=UserAgenda)
async def get_my_agenda(
    exhibition_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get combined agenda for an exhibition (JS.B6).

    Returns all sessions (as GM) and bookings (as player) with
    conflict detection for overlapping schedules.
    """
    # Get exhibition
    exhibition_result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = exhibition_result.scalar_one_or_none()
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Get my sessions
    sessions_query = (
        select(
            GameSession,
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            Game.title.label("game_title"),
            Game.cover_image_url.label("game_cover_image_url"),
            Game.external_provider.label("game_external_provider"),
        )
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .outerjoin(Game, GameSession.game_id == Game.id)
        .where(
            GameSession.created_by_user_id == current_user.id,
            GameSession.exhibition_id == exhibition_id,
            GameSession.status.notin_([SessionStatus.CANCELLED, SessionStatus.REJECTED]),
        )
        .order_by(GameSession.scheduled_start)
    )
    sessions_result = await db.execute(sessions_query)
    session_rows = sessions_result.all()

    my_sessions = []
    session_times = []  # For conflict detection

    for row in session_rows:
        session = row[0]

        # Count bookings
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session.id)
            .group_by(Booking.status)
        )
        counts = {r[0]: r[1] for r in booking_counts.fetchall()}
        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        my_sessions.append(MySessionSummary(
            id=session.id,
            title=session.title,
            exhibition_id=session.exhibition_id,
            exhibition_title=exhibition.title,
            status=session.status,
            scheduled_start=session.scheduled_start,
            scheduled_end=session.scheduled_end,
            zone_name=row[1],
            table_label=row[2],
            language=session.language,
            max_players_count=session.max_players_count,
            confirmed_players=confirmed,
            waitlist_count=waitlist,
            game_title=row[3],
            game_cover_image_url=row[4],
            game_external_provider=row[5],
        ))

        session_times.append({
            "type": "gm",
            "title": session.title,
            "start": session.scheduled_start,
            "end": session.scheduled_end,
        })

    # Get my bookings
    bookings_query = (
        select(
            Booking,
            GameSession.title.label("session_title"),
            GameSession.scheduled_start,
            GameSession.scheduled_end,
            Zone.name.label("zone_name"),
            PhysicalTable.label.label("table_label"),
            User.full_name.label("gm_name"),
            GameSession.max_players_count,
            GameSession.id.label("session_id"),
            Game.title.label("game_title"),
            GameSession.language.label("session_language"),
            Game.cover_image_url.label("game_cover_image_url"),
            Game.external_provider.label("game_external_provider"),
        )
        .join(GameSession, Booking.game_session_id == GameSession.id)
        .join(User, GameSession.created_by_user_id == User.id)
        .outerjoin(PhysicalTable, GameSession.physical_table_id == PhysicalTable.id)
        .outerjoin(Zone, PhysicalTable.zone_id == Zone.id)
        .outerjoin(Game, GameSession.game_id == Game.id)
        .where(
            Booking.user_id == current_user.id,
            GameSession.exhibition_id == exhibition_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED,
                BookingStatus.CHECKED_IN,
                BookingStatus.WAITING_LIST,
            ]),
        )
        .order_by(GameSession.scheduled_start)
    )
    bookings_result = await db.execute(bookings_query)
    booking_rows = bookings_result.all()

    my_bookings = []
    for row in booking_rows:
        booking = row[0]
        session_id = row[8]

        # Count confirmed and waitlist bookings for this session
        booking_counts = await db.execute(
            select(
                Booking.status,
                func.count(Booking.id),
            )
            .where(Booking.game_session_id == session_id)
            .group_by(Booking.status)
        )
        counts = {r[0]: r[1] for r in booking_counts.fetchall()}
        confirmed = counts.get(BookingStatus.CONFIRMED, 0) + counts.get(BookingStatus.CHECKED_IN, 0)
        waitlist = counts.get(BookingStatus.WAITING_LIST, 0)

        my_bookings.append(MyBookingSummary(
            id=booking.id,
            game_session_id=booking.game_session_id,
            session_title=row[1],
            exhibition_id=exhibition_id,
            exhibition_title=exhibition.title,
            status=booking.status,
            role=booking.role,
            scheduled_start=row[2],
            scheduled_end=row[3],
            zone_name=row[4],
            table_label=row[5],
            gm_name=row[6],
            language=row[10] or "fr",
            max_players_count=row[7],
            confirmed_players=confirmed,
            waitlist_count=waitlist,
            game_title=row[9],
            game_cover_image_url=row[11],
            game_external_provider=row[12],
        ))

        session_times.append({
            "type": "player",
            "title": row[1],
            "start": row[2],
            "end": row[3],
        })

    # Detect conflicts
    conflicts = []
    for i, t1 in enumerate(session_times):
        for t2 in session_times[i + 1:]:
            # Check overlap
            if t1["start"] < t2["end"] and t1["end"] > t2["start"]:
                conflicts.append(SessionConflict(
                    session1_title=t1["title"],
                    session1_role=t1["type"],
                    session2_title=t2["title"],
                    session2_role=t2["type"],
                ))

    return UserAgenda(
        user_id=current_user.id,
        exhibition_id=exhibition_id,
        exhibition_title=exhibition.title,
        my_sessions=my_sessions,
        my_bookings=my_bookings,
        conflicts=conflicts,
    )


# =============================================================================
# My Exhibitions (Issue #96 - JS.C11)
# =============================================================================

@router.get("/me/exhibitions", response_model=MyExhibitions)
async def get_my_exhibitions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get exhibitions the user organizes and is registered to (JS.C11).

    Returns:
    - organized: exhibitions user can manage (organizer/partner role)
    - registered: exhibitions user is registered to (excluding organized ones)
    """
    # Get all published exhibitions
    result = await db.execute(
        select(Exhibition).where(Exhibition.status == ExhibitionStatus.PUBLISHED)
    )
    all_exhibitions = result.scalars().all()

    organized = []
    registered = []
    organized_ids = set()

    # Check user roles for each exhibition
    for exhibition in all_exhibitions:
        # Check if user has a role (organizer/partner)
        role_result = await db.execute(
            select(UserExhibitionRole).where(
                UserExhibitionRole.user_id == current_user.id,
                UserExhibitionRole.exhibition_id == exhibition.id,
            )
        )
        role = role_result.scalar_one_or_none()

        # Also check for super admin
        is_admin = current_user.global_role == GlobalRole.SUPER_ADMIN

        if role or is_admin:
            # User can manage this exhibition
            response = ExhibitionRead.model_validate(exhibition)
            response.can_manage = True
            response.user_exhibition_role = (
                "ORGANIZER" if is_admin else
                (role.role.value if hasattr(role.role, 'value') else str(role.role))
            )
            response.is_user_registered = True  # Organizers are implicitly "registered"
            organized.append(response)
            organized_ids.add(exhibition.id)

    # Get exhibitions user is registered to (excluding ones they organize)
    reg_result = await db.execute(
        select(ExhibitionRegistration).where(
            ExhibitionRegistration.user_id == current_user.id,
            ExhibitionRegistration.cancelled_at.is_(None),
        )
    )
    registrations = reg_result.scalars().all()

    for reg in registrations:
        if reg.exhibition_id not in organized_ids:
            # Get the exhibition
            exhibition_result = await db.execute(
                select(Exhibition).where(
                    Exhibition.id == reg.exhibition_id,
                    Exhibition.status == ExhibitionStatus.PUBLISHED,
                )
            )
            exhibition = exhibition_result.scalar_one_or_none()
            if exhibition:
                response = ExhibitionRead.model_validate(exhibition)
                response.can_manage = False
                response.is_user_registered = True
                registered.append(response)

    # Sort by start date (newest first)
    organized.sort(key=lambda e: e.start_date, reverse=True)
    registered.sort(key=lambda e: e.start_date, reverse=True)

    return MyExhibitions(organized=organized, registered=registered)
