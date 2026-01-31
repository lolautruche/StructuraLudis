"""
Email template rendering with i18n support.

Uses Jinja2 for templating and provides localized strings for email content.
"""
import os
from datetime import datetime
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings


# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

# Jinja2 environment
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


# Localized strings for email templates
EMAIL_STRINGS = {
    "en": {
        # Common
        "app_name": "Structura Ludis",
        "footer_text": "This email was sent by Structura Ludis. Please do not reply to this email.",
        "session_label": "Session",
        "event_label": "Event",
        "date_label": "Date",
        "time_label": "Time",
        "location_label": "Location",
        "table_label": "Table",
        "gm_label": "Game Master",
        "reason_label": "Reason",

        # Booking confirmed
        "booking_confirmed_subject": "Booking confirmed: {session_title}",
        "booking_confirmed_greeting": "Your booking is confirmed!",
        "booking_confirmed_intro": "Great news! Your registration for the following session has been confirmed.",
        "booking_confirmed_reminder": "Please remember to check in at least 15 minutes before the session starts.",
        "booking_confirmed_action": "View My Agenda",
        "booking_confirmed_closing": "We look forward to seeing you there!",

        # Session cancelled
        "session_cancelled_subject": "Session cancelled: {session_title}",
        "session_cancelled_greeting": "Session Cancellation Notice",
        "session_cancelled_alert": "A session you were registered for has been cancelled.",
        "session_cancelled_intro": "We regret to inform you that the following session has been cancelled.",
        "session_cancelled_apology": "We apologize for any inconvenience. Please feel free to browse other available sessions.",
        "session_cancelled_action": "Find Other Sessions",

        # Waitlist promoted
        "waitlist_promoted_subject": "You're in! {session_title}",
        "waitlist_promoted_greeting": "Great news!",
        "waitlist_promoted_success": "A spot has opened up and you've been moved from the waitlist!",
        "waitlist_promoted_intro": "You've been promoted from the waitlist for the following session.",
        "waitlist_promoted_action_required": "Your spot is now confirmed. Please make sure to check in on time.",
        "waitlist_promoted_action": "View My Booking",
        "waitlist_promoted_closing": "See you at the session!",

        # Session reminder
        "session_reminder_subject": "Reminder: {session_title} starts soon",
        "session_reminder_greeting": "Session Starting Soon!",
        "session_reminder_intro": "This is a friendly reminder that your session is starting soon.",
        "session_reminder_checkin": "Please arrive early and check in at least 15 minutes before the session begins.",
        "session_reminder_action": "View Session Details",
        "session_reminder_closing": "See you soon!",

        # Email verification
        "email_verification_subject": "Verify your email address",
        "email_verification_greeting": "Welcome to Structura Ludis!",
        "email_verification_hello": "Hello",
        "email_verification_intro": "Thank you for signing up. Please verify your email address by clicking the button below.",
        "email_verification_action": "Verify my email",
        "email_verification_important": "Important",
        "email_verification_expiration": "This link will expire in 7 days. If you did not create an account, you can safely ignore this email.",
        "email_verification_link_instruction": "If the button doesn't work, copy and paste this link into your browser:",
        "email_verification_closing": "Thank you for joining us!",
    },
    "fr": {
        # Common
        "app_name": "Structura Ludis",
        "footer_text": "Cet email a été envoyé par Structura Ludis. Merci de ne pas répondre à cet email.",
        "session_label": "Session",
        "event_label": "Événement",
        "date_label": "Date",
        "time_label": "Heure",
        "location_label": "Lieu",
        "table_label": "Table",
        "gm_label": "Meneur de jeu",
        "reason_label": "Raison",

        # Booking confirmed
        "booking_confirmed_subject": "Réservation confirmée : {session_title}",
        "booking_confirmed_greeting": "Votre réservation est confirmée !",
        "booking_confirmed_intro": "Bonne nouvelle ! Votre inscription à la session suivante a été confirmée.",
        "booking_confirmed_reminder": "N'oubliez pas de vous présenter au moins 15 minutes avant le début de la session.",
        "booking_confirmed_action": "Voir mon agenda",
        "booking_confirmed_closing": "Nous avons hâte de vous y voir !",

        # Session cancelled
        "session_cancelled_subject": "Session annulée : {session_title}",
        "session_cancelled_greeting": "Avis d'annulation de session",
        "session_cancelled_alert": "Une session à laquelle vous étiez inscrit(e) a été annulée.",
        "session_cancelled_intro": "Nous avons le regret de vous informer que la session suivante a été annulée.",
        "session_cancelled_apology": "Nous nous excusons pour la gêne occasionnée. N'hésitez pas à consulter les autres sessions disponibles.",
        "session_cancelled_action": "Trouver d'autres sessions",

        # Waitlist promoted
        "waitlist_promoted_subject": "C'est bon ! {session_title}",
        "waitlist_promoted_greeting": "Bonne nouvelle !",
        "waitlist_promoted_success": "Une place s'est libérée et vous avez été promu(e) de la liste d'attente !",
        "waitlist_promoted_intro": "Vous avez été promu(e) de la liste d'attente pour la session suivante.",
        "waitlist_promoted_action_required": "Votre place est maintenant confirmée. Assurez-vous d'arriver à l'heure.",
        "waitlist_promoted_action": "Voir ma réservation",
        "waitlist_promoted_closing": "À bientôt !",

        # Session reminder
        "session_reminder_subject": "Rappel : {session_title} commence bientôt",
        "session_reminder_greeting": "Session imminente !",
        "session_reminder_intro": "Ceci est un rappel amical : votre session commence bientôt.",
        "session_reminder_checkin": "Merci d'arriver en avance et de vous présenter au moins 15 minutes avant le début.",
        "session_reminder_action": "Voir les détails",
        "session_reminder_closing": "À très vite !",

        # Email verification
        "email_verification_subject": "Vérifiez votre adresse email",
        "email_verification_greeting": "Bienvenue sur Structura Ludis !",
        "email_verification_hello": "Bonjour",
        "email_verification_intro": "Merci de vous être inscrit(e). Veuillez vérifier votre adresse email en cliquant sur le bouton ci-dessous.",
        "email_verification_action": "Vérifier mon email",
        "email_verification_important": "Important",
        "email_verification_expiration": "Ce lien expirera dans 7 jours. Si vous n'avez pas créé de compte, vous pouvez ignorer cet email.",
        "email_verification_link_instruction": "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :",
        "email_verification_closing": "Merci de nous avoir rejoints !",
    },
}


def get_string(key: str, locale: str = "en", **kwargs) -> str:
    """
    Get a localized string.

    Args:
        key: The string key
        locale: The locale (en, fr, etc.)
        **kwargs: Format arguments for the string

    Returns:
        The localized and formatted string
    """
    strings = EMAIL_STRINGS.get(locale, EMAIL_STRINGS["en"])
    value = strings.get(key, EMAIL_STRINGS["en"].get(key, key))

    if kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
    return value


def format_datetime(dt: datetime, locale: str = "en") -> tuple[str, str]:
    """
    Format a datetime for display in emails.

    Returns:
        Tuple of (date_string, time_string)
    """
    if locale == "fr":
        date_str = dt.strftime("%d/%m/%Y")
        time_str = dt.strftime("%H:%M")
    else:
        date_str = dt.strftime("%B %d, %Y")
        time_str = dt.strftime("%I:%M %p")

    return date_str, time_str


def render_email_template(
    template_name: str,
    locale: str = "en",
    **context: Any,
) -> tuple[str, str]:
    """
    Render an email template with localized strings.

    Args:
        template_name: Template file name (e.g., "booking_confirmed")
        locale: Locale for translations
        **context: Template context variables

    Returns:
        Tuple of (subject, html_body)
    """
    template = _env.get_template(f"email/{template_name}.html")

    # Add common localized strings
    full_context = {
        "locale": locale,
        "app_name": get_string("app_name", locale),
        "footer_text": get_string("footer_text", locale),
        "session_label": get_string("session_label", locale),
        "event_label": get_string("event_label", locale),
        "date_label": get_string("date_label", locale),
        "time_label": get_string("time_label", locale),
        "location_label": get_string("location_label", locale),
        "table_label": get_string("table_label", locale),
        "gm_label": get_string("gm_label", locale),
        "reason_label": get_string("reason_label", locale),
        **context,
    }

    html = template.render(**full_context)

    # Get subject from context or generate from template name
    subject = context.get("subject", get_string(f"{template_name}_subject", locale, **context))

    return subject, html


def render_booking_confirmed(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    gm_name: Optional[str] = None,
    location: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render booking confirmation email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "booking_confirmed",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        gm_name=gm_name,
        location=location,
        action_url=action_url,
        greeting=get_string("booking_confirmed_greeting", locale),
        intro_text=get_string("booking_confirmed_intro", locale),
        reminder_text=get_string("booking_confirmed_reminder", locale),
        action_button_text=get_string("booking_confirmed_action", locale),
        closing_text=get_string("booking_confirmed_closing", locale),
    )


def render_session_cancelled(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    cancellation_reason: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render session cancellation email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "session_cancelled",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        cancellation_reason=cancellation_reason,
        action_url=action_url,
        greeting=get_string("session_cancelled_greeting", locale),
        alert_text=get_string("session_cancelled_alert", locale),
        intro_text=get_string("session_cancelled_intro", locale),
        apology_text=get_string("session_cancelled_apology", locale),
        action_button_text=get_string("session_cancelled_action", locale),
    )


def render_waitlist_promoted(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    location: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render waitlist promotion email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "waitlist_promoted",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        location=location,
        action_url=action_url,
        greeting=get_string("waitlist_promoted_greeting", locale),
        success_text=get_string("waitlist_promoted_success", locale),
        intro_text=get_string("waitlist_promoted_intro", locale),
        action_required_text=get_string("waitlist_promoted_action_required", locale),
        action_button_text=get_string("waitlist_promoted_action", locale),
        closing_text=get_string("waitlist_promoted_closing", locale),
    )


def render_session_reminder(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    location: Optional[str] = None,
    table_number: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render session reminder email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "session_reminder",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        location=location,
        table_number=table_number,
        action_url=action_url,
        greeting=get_string("session_reminder_greeting", locale),
        intro_text=get_string("session_reminder_intro", locale),
        checkin_reminder_text=get_string("session_reminder_checkin", locale),
        action_button_text=get_string("session_reminder_action", locale),
        closing_text=get_string("session_reminder_closing", locale),
    )


def render_email_verification(
    locale: str,
    verification_url: str,
    user_name: Optional[str] = None,
) -> tuple[str, str]:
    """Render email verification email."""
    return render_email_template(
        "email_verification",
        locale=locale,
        verification_url=verification_url,
        user_name=user_name,
        greeting=get_string("email_verification_greeting", locale),
        hello_text=get_string("email_verification_hello", locale),
        intro_text=get_string("email_verification_intro", locale),
        action_button_text=get_string("email_verification_action", locale),
        important_label=get_string("email_verification_important", locale),
        expiration_text=get_string("email_verification_expiration", locale),
        link_instruction=get_string("email_verification_link_instruction", locale),
        closing_text=get_string("email_verification_closing", locale),
    )