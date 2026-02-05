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

        # New player registration (GM notification)
        "new_player_registration_subject": "New player registered: {session_title}",
        "new_player_registration_greeting": "New Player Registration",
        "new_player_registration_intro": "A new player has registered for your session.",
        "new_player_registration_action": "View Session",
        "new_player_registration_closing": "Good luck with your session!",
        "player_label": "Player",
        "players_registered_label": "Players registered",

        # Booking cancelled (player notification)
        "booking_cancelled_subject": "Booking cancelled: {session_title}",
        "booking_cancelled_greeting": "Booking Cancelled",
        "booking_cancelled_intro": "Your booking has been cancelled.",
        "booking_cancelled_action": "Find Other Sessions",
        "booking_cancelled_closing": "We hope to see you at another session!",

        # Booking cancelled (GM notification)
        "player_cancelled_subject": "Player cancelled: {session_title}",
        "player_cancelled_greeting": "Player Cancellation",
        "player_cancelled_intro": "A player has cancelled their registration for your session.",
        "player_cancelled_action": "View Session",
        "player_cancelled_closing": "The spot may be filled by someone on the waitlist.",

        # Waitlist cancelled (player notification)
        "waitlist_cancelled_subject": "Waitlist cancelled: {session_title}",
        "waitlist_cancelled_greeting": "Waitlist Cancellation",
        "waitlist_cancelled_intro": "You have been removed from the waitlist for the following session.",
        "waitlist_cancelled_action": "Find Other Sessions",
        "waitlist_cancelled_closing": "We hope to see you at another session!",

        # Waitlist joined (player notification)
        "waitlist_joined_subject": "You're on the waitlist: {session_title}",
        "waitlist_joined_greeting": "You're on the Waitlist!",
        "waitlist_joined_intro": "This session is currently full, but you've been added to the waitlist.",
        "waitlist_joined_position": "Your position",
        "waitlist_joined_info": "We'll notify you immediately if a spot opens up. Keep an eye on your inbox!",
        "waitlist_joined_action": "View My Bookings",
        "waitlist_joined_closing": "Fingers crossed!",

        # New waitlist player (GM notification)
        "new_waitlist_player_subject": "New player on waitlist: {session_title}",
        "new_waitlist_player_greeting": "New Waitlist Entry",
        "new_waitlist_player_intro": "A player has joined the waitlist for your session.",
        "new_waitlist_player_action": "View Session",
        "new_waitlist_player_closing": "Your session is popular!",
        "waitlist_count_label": "Waitlist count",

        # Email change verification
        "email_change_subject": "Confirm your new email address",
        "email_change_greeting": "Email Change Request",
        "email_change_hello": "Hello",
        "email_change_intro": "You requested to change your email address to this one. Please confirm by clicking the button below.",
        "email_change_action": "Confirm new email",
        "email_change_important": "Important",
        "email_change_expiration": "This link will expire in 7 days. If you did not request this change, you can safely ignore this email.",
        "email_change_link_instruction": "If the button doesn't work, copy and paste this link into your browser:",
        "email_change_closing": "Thank you!",

        # Password changed notification
        "password_changed_subject": "Your password has been changed",
        "password_changed_greeting": "Password Changed",
        "password_changed_hello": "Hello",
        "password_changed_intro": "Your password was successfully changed.",
        "password_changed_warning": "If you did not make this change, please contact support immediately and secure your account.",
        "password_changed_when": "Changed at",
        "password_changed_closing": "The Structura Ludis Team",

        # Password reset request
        "password_reset_subject": "Reset your password",
        "password_reset_greeting": "Password Reset Request",
        "password_reset_hello": "Hello",
        "password_reset_intro": "We received a request to reset your password. Click the button below to create a new password.",
        "password_reset_action": "Reset my password",
        "password_reset_important": "Important",
        "password_reset_expiration": "This link will expire in 1 hour. If you did not request a password reset, you can safely ignore this email.",
        "password_reset_link_instruction": "If the button doesn't work, copy and paste this link into your browser:",
        "password_reset_closing": "The Structura Ludis Team",

        # Session approved (proposer notification)
        "session_approved_subject": "Session approved: {session_title}",
        "session_approved_greeting": "Your session has been approved!",
        "session_approved_intro": "Great news! Your session has been validated and is now visible to players.",
        "session_approved_action": "View Session",
        "session_approved_closing": "Good luck with your session!",

        # Session rejected (proposer notification)
        "session_rejected_subject": "Session not approved: {session_title}",
        "session_rejected_greeting": "Session Review Result",
        "session_rejected_intro": "Unfortunately, your session has not been approved.",
        "session_rejected_action": "View Details",
        "session_rejected_closing": "If you have questions, please contact the organizers.",

        # Changes requested (proposer notification)
        "changes_requested_subject": "Changes requested: {session_title}",
        "changes_requested_greeting": "Modifications Required",
        "changes_requested_intro": "The moderators have requested some changes to your session before it can be approved.",
        "changes_requested_action": "Edit Session",
        "changes_requested_closing": "Once you've made the changes, please resubmit your session for review.",
        "comment_label": "Requested changes",

        # Exhibition unregistration (Issue #77)
        "exhibition_unregistered_subject": "Unregistration confirmed: {exhibition_title}",
        "exhibition_unregistered_greeting": "Unregistration Confirmed",
        "exhibition_unregistered_intro": "Your registration for the following event has been cancelled.",
        "exhibition_unregistered_bookings_cancelled": "Your {booking_count} active booking(s) have also been cancelled.",
        "exhibition_unregistered_action": "Browse Events",
        "exhibition_unregistered_closing": "We hope to see you at another event!",

        # Event request notifications (Issue #92)
        "event_request_approved_subject": "Your event has been approved: {event_title}",
        "event_request_approved_greeting": "Congratulations!",
        "event_request_approved_intro": "Your event request has been approved. Your organization and event have been created on the platform.",
        "event_request_approved_action": "Manage Your Event",
        "event_request_approved_closing": "You can now start configuring your event: add zones, time slots, and more.",

        "event_request_rejected_subject": "Event request not approved: {event_title}",
        "event_request_rejected_greeting": "Event Request Update",
        "event_request_rejected_intro": "Unfortunately, your event request has not been approved.",
        "event_request_rejected_action": "Contact Support",
        "event_request_rejected_closing": "If you have questions, please contact the platform administrators.",

        "event_request_changes_subject": "Changes requested for your event: {event_title}",
        "event_request_changes_greeting": "Action Required",
        "event_request_changes_intro": "The administrators have requested some changes to your event request before it can be approved.",
        "event_request_changes_action": "Edit Your Request",
        "event_request_changes_closing": "Please review the feedback and resubmit your request.",

        "event_request_submitted_subject": "New event request submitted",
        "event_request_submitted_greeting": "New Event Request",
        "event_request_submitted_intro": "A new event request has been submitted and is awaiting review.",
        "event_request_submitted_action": "Review Request",
        "event_request_submitted_closing": "Please review the request and take appropriate action.",
        "event_request_resubmitted_subject": "Event request resubmitted after changes",
        "event_request_resubmitted_greeting": "Event Request Updated",
        "event_request_resubmitted_intro": "An event request has been resubmitted after making requested changes.",
        "requester_label": "Requester",
        "event_title_label": "Event",
        "organization_label": "Organization",

        # Event request confirmation (to requester)
        "event_request_confirmation_subject": "Your event request has been submitted: {event_title}",
        "event_request_confirmation_greeting": "Request Submitted",
        "event_request_confirmation_intro": "Thank you for submitting your event request. Our team will review it and get back to you.",
        "event_request_confirmation_action": "View My Requests",
        "event_request_confirmation_closing": "You will receive an email once your request has been reviewed.",
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

        # New player registration (GM notification)
        "new_player_registration_subject": "Nouveau joueur inscrit : {session_title}",
        "new_player_registration_greeting": "Nouvelle inscription",
        "new_player_registration_intro": "Un nouveau joueur s'est inscrit à votre session.",
        "new_player_registration_action": "Voir la session",
        "new_player_registration_closing": "Bonne partie !",
        "player_label": "Joueur",
        "players_registered_label": "Joueurs inscrits",

        # Booking cancelled (player notification)
        "booking_cancelled_subject": "Réservation annulée : {session_title}",
        "booking_cancelled_greeting": "Réservation annulée",
        "booking_cancelled_intro": "Votre réservation a été annulée.",
        "booking_cancelled_action": "Trouver d'autres sessions",
        "booking_cancelled_closing": "Nous espérons vous revoir à une autre session !",

        # Booking cancelled (GM notification)
        "player_cancelled_subject": "Joueur désisté : {session_title}",
        "player_cancelled_greeting": "Désistement d'un joueur",
        "player_cancelled_intro": "Un joueur a annulé son inscription à votre session.",
        "player_cancelled_action": "Voir la session",
        "player_cancelled_closing": "La place pourra être attribuée à une personne en liste d'attente.",

        # Waitlist cancelled (player notification)
        "waitlist_cancelled_subject": "Liste d'attente annulée : {session_title}",
        "waitlist_cancelled_greeting": "Retrait de la liste d'attente",
        "waitlist_cancelled_intro": "Vous avez été retiré(e) de la liste d'attente pour la session suivante.",
        "waitlist_cancelled_action": "Trouver d'autres sessions",
        "waitlist_cancelled_closing": "Nous espérons vous revoir à une autre session !",

        # Waitlist joined (player notification)
        "waitlist_joined_subject": "Vous êtes sur liste d'attente : {session_title}",
        "waitlist_joined_greeting": "Vous êtes sur la liste d'attente !",
        "waitlist_joined_intro": "Cette session est actuellement complète, mais vous avez été ajouté(e) à la liste d'attente.",
        "waitlist_joined_position": "Votre position",
        "waitlist_joined_info": "Nous vous notifierons immédiatement si une place se libère. Gardez un œil sur votre boîte mail !",
        "waitlist_joined_action": "Voir mes réservations",
        "waitlist_joined_closing": "Croisons les doigts !",

        # New waitlist player (GM notification)
        "new_waitlist_player_subject": "Nouveau joueur en liste d'attente : {session_title}",
        "new_waitlist_player_greeting": "Nouvelle inscription en liste d'attente",
        "new_waitlist_player_intro": "Un joueur a rejoint la liste d'attente de votre session.",
        "new_waitlist_player_action": "Voir la session",
        "new_waitlist_player_closing": "Votre session est populaire !",
        "waitlist_count_label": "Nombre en liste d'attente",

        # Email change verification
        "email_change_subject": "Confirmez votre nouvelle adresse email",
        "email_change_greeting": "Demande de changement d'email",
        "email_change_hello": "Bonjour",
        "email_change_intro": "Vous avez demandé à changer votre adresse email pour celle-ci. Veuillez confirmer en cliquant sur le bouton ci-dessous.",
        "email_change_action": "Confirmer le nouvel email",
        "email_change_important": "Important",
        "email_change_expiration": "Ce lien expirera dans 7 jours. Si vous n'avez pas demandé ce changement, vous pouvez ignorer cet email.",
        "email_change_link_instruction": "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :",
        "email_change_closing": "Merci !",

        # Password changed notification
        "password_changed_subject": "Votre mot de passe a été modifié",
        "password_changed_greeting": "Mot de passe modifié",
        "password_changed_hello": "Bonjour",
        "password_changed_intro": "Votre mot de passe a été modifié avec succès.",
        "password_changed_warning": "Si vous n'êtes pas à l'origine de ce changement, veuillez contacter le support immédiatement et sécuriser votre compte.",
        "password_changed_when": "Modifié le",
        "password_changed_closing": "L'équipe Structura Ludis",

        # Password reset request
        "password_reset_subject": "Réinitialisation de votre mot de passe",
        "password_reset_greeting": "Demande de réinitialisation",
        "password_reset_hello": "Bonjour",
        "password_reset_intro": "Nous avons reçu une demande de réinitialisation de votre mot de passe. Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe.",
        "password_reset_action": "Réinitialiser mon mot de passe",
        "password_reset_important": "Important",
        "password_reset_expiration": "Ce lien expirera dans 1 heure. Si vous n'avez pas demandé de réinitialisation, vous pouvez ignorer cet email.",
        "password_reset_link_instruction": "Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :",
        "password_reset_closing": "L'équipe Structura Ludis",

        # Session approved (proposer notification)
        "session_approved_subject": "Session approuvée : {session_title}",
        "session_approved_greeting": "Votre session a été approuvée !",
        "session_approved_intro": "Bonne nouvelle ! Votre session a été validée et est maintenant visible par les joueurs.",
        "session_approved_action": "Voir la session",
        "session_approved_closing": "Bonne partie !",

        # Session rejected (proposer notification)
        "session_rejected_subject": "Session non approuvée : {session_title}",
        "session_rejected_greeting": "Résultat de la modération",
        "session_rejected_intro": "Malheureusement, votre session n'a pas été approuvée.",
        "session_rejected_action": "Voir les détails",
        "session_rejected_closing": "Si vous avez des questions, veuillez contacter les organisateurs.",

        # Changes requested (proposer notification)
        "changes_requested_subject": "Modifications demandées : {session_title}",
        "changes_requested_greeting": "Modifications requises",
        "changes_requested_intro": "Les modérateurs ont demandé des modifications à votre session avant qu'elle puisse être approuvée.",
        "changes_requested_action": "Modifier la session",
        "changes_requested_closing": "Une fois les modifications effectuées, veuillez resoumettre votre session pour examen.",
        "comment_label": "Modifications demandées",

        # Exhibition unregistration (Issue #77)
        "exhibition_unregistered_subject": "Désinscription confirmée : {exhibition_title}",
        "exhibition_unregistered_greeting": "Désinscription confirmée",
        "exhibition_unregistered_intro": "Votre inscription à l'événement suivant a été annulée.",
        "exhibition_unregistered_bookings_cancelled": "Vos {booking_count} réservation(s) active(s) ont également été annulées.",
        "exhibition_unregistered_action": "Parcourir les événements",
        "exhibition_unregistered_closing": "Nous espérons vous revoir à un autre événement !",

        # Event request notifications (Issue #92)
        "event_request_approved_subject": "Votre événement a été approuvé : {event_title}",
        "event_request_approved_greeting": "Félicitations !",
        "event_request_approved_intro": "Votre demande d'événement a été approuvée. Votre organisation et votre événement ont été créés sur la plateforme.",
        "event_request_approved_action": "Gérer votre événement",
        "event_request_approved_closing": "Vous pouvez maintenant configurer votre événement : ajouter des zones, des créneaux horaires, et plus encore.",

        "event_request_rejected_subject": "Demande d'événement non approuvée : {event_title}",
        "event_request_rejected_greeting": "Mise à jour de votre demande",
        "event_request_rejected_intro": "Malheureusement, votre demande d'événement n'a pas été approuvée.",
        "event_request_rejected_action": "Contacter le support",
        "event_request_rejected_closing": "Si vous avez des questions, veuillez contacter les administrateurs de la plateforme.",

        "event_request_changes_subject": "Modifications demandées pour votre événement : {event_title}",
        "event_request_changes_greeting": "Action requise",
        "event_request_changes_intro": "Les administrateurs ont demandé des modifications à votre demande d'événement avant qu'elle puisse être approuvée.",
        "event_request_changes_action": "Modifier votre demande",
        "event_request_changes_closing": "Veuillez consulter les commentaires et resoumettre votre demande.",

        "event_request_submitted_subject": "Nouvelle demande d'événement soumise",
        "event_request_submitted_greeting": "Nouvelle demande d'événement",
        "event_request_submitted_intro": "Une nouvelle demande d'événement a été soumise et attend examen.",
        "event_request_submitted_action": "Examiner la demande",
        "event_request_submitted_closing": "Veuillez examiner la demande et prendre les mesures appropriées.",
        "event_request_resubmitted_subject": "Demande d'événement resoumise après modifications",
        "event_request_resubmitted_greeting": "Demande d'événement mise à jour",
        "event_request_resubmitted_intro": "Une demande d'événement a été resoumise après les modifications demandées.",
        "requester_label": "Demandeur",
        "event_title_label": "Événement",
        "organization_label": "Organisation",

        # Event request confirmation (to requester)
        "event_request_confirmation_subject": "Votre demande d'événement a été soumise : {event_title}",
        "event_request_confirmation_greeting": "Demande soumise",
        "event_request_confirmation_intro": "Merci d'avoir soumis votre demande d'événement. Notre équipe va l'examiner et vous recontactera.",
        "event_request_confirmation_action": "Voir mes demandes",
        "event_request_confirmation_closing": "Vous recevrez un email une fois votre demande examinée.",
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


def render_new_player_registration(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    player_name: str,
    players_registered: int,
    max_players: int,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render new player registration email for GM."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "new_player_registration",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        player_name=player_name,
        players_registered=players_registered,
        max_players=max_players,
        action_url=action_url,
        greeting=get_string("new_player_registration_greeting", locale),
        intro_text=get_string("new_player_registration_intro", locale),
        action_button_text=get_string("new_player_registration_action", locale),
        closing_text=get_string("new_player_registration_closing", locale),
        player_label=get_string("player_label", locale),
        players_registered_label=get_string("players_registered_label", locale),
    )


def render_booking_cancelled(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render booking cancelled email for player."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "booking_cancelled",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        action_url=action_url,
        greeting=get_string("booking_cancelled_greeting", locale),
        intro_text=get_string("booking_cancelled_intro", locale),
        action_button_text=get_string("booking_cancelled_action", locale),
        closing_text=get_string("booking_cancelled_closing", locale),
    )


def render_player_cancelled(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    player_name: str,
    players_registered: int,
    max_players: int,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render player cancelled email for GM."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    # Get subject explicitly since we're using a different template name
    subject = get_string("player_cancelled_subject", locale, session_title=session_title)

    return render_email_template(
        "booking_cancelled",
        locale=locale,
        subject=subject,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        player_name=player_name,
        players_registered=players_registered,
        max_players=max_players,
        action_url=action_url,
        greeting=get_string("player_cancelled_greeting", locale),
        intro_text=get_string("player_cancelled_intro", locale),
        action_button_text=get_string("player_cancelled_action", locale),
        closing_text=get_string("player_cancelled_closing", locale),
        player_label=get_string("player_label", locale),
        players_registered_label=get_string("players_registered_label", locale),
    )


def render_waitlist_cancelled(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render waitlist cancellation email for player."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    # Get subject explicitly since we're reusing booking_cancelled template
    subject = get_string("waitlist_cancelled_subject", locale, session_title=session_title)

    return render_email_template(
        "booking_cancelled",
        locale=locale,
        subject=subject,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        action_url=action_url,
        greeting=get_string("waitlist_cancelled_greeting", locale),
        intro_text=get_string("waitlist_cancelled_intro", locale),
        action_button_text=get_string("waitlist_cancelled_action", locale),
        closing_text=get_string("waitlist_cancelled_closing", locale),
    )


def render_waitlist_joined(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    waitlist_position: int,
    gm_name: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render waitlist joined confirmation email for player."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "waitlist_joined",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        waitlist_position=waitlist_position,
        gm_name=gm_name,
        action_url=action_url,
        greeting=get_string("waitlist_joined_greeting", locale),
        intro_text=get_string("waitlist_joined_intro", locale),
        position_label=get_string("waitlist_joined_position", locale),
        info_text=get_string("waitlist_joined_info", locale),
        action_button_text=get_string("waitlist_joined_action", locale),
        closing_text=get_string("waitlist_joined_closing", locale),
    )


def render_new_waitlist_player(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    player_name: str,
    waitlist_count: int,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render new waitlist player notification email for GM."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    return render_email_template(
        "new_waitlist_player",
        locale=locale,
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        player_name=player_name,
        waitlist_count=waitlist_count,
        action_url=action_url,
        greeting=get_string("new_waitlist_player_greeting", locale),
        intro_text=get_string("new_waitlist_player_intro", locale),
        action_button_text=get_string("new_waitlist_player_action", locale),
        closing_text=get_string("new_waitlist_player_closing", locale),
        player_label=get_string("player_label", locale),
        waitlist_count_label=get_string("waitlist_count_label", locale),
    )


def render_email_change(
    locale: str,
    verification_url: str,
    user_name: Optional[str] = None,
) -> tuple[str, str]:
    """Render email change verification email."""
    # Reuse the email_verification template with different strings
    return render_email_template(
        "email_verification",
        locale=locale,
        verification_url=verification_url,
        user_name=user_name,
        subject=get_string("email_change_subject", locale),
        greeting=get_string("email_change_greeting", locale),
        hello_text=get_string("email_change_hello", locale),
        intro_text=get_string("email_change_intro", locale),
        action_button_text=get_string("email_change_action", locale),
        important_label=get_string("email_change_important", locale),
        expiration_text=get_string("email_change_expiration", locale),
        link_instruction=get_string("email_change_link_instruction", locale),
        closing_text=get_string("email_change_closing", locale),
    )


def render_password_changed(
    locale: str,
    changed_at: datetime,
    user_name: Optional[str] = None,
) -> tuple[str, str]:
    """Render password changed notification email."""
    # Format the datetime
    date_str, time_str = format_datetime(changed_at, locale)
    changed_at_str = f"{date_str} {time_str}"

    return render_email_template(
        "password_changed",
        locale=locale,
        user_name=user_name,
        changed_at=changed_at_str,
        subject=get_string("password_changed_subject", locale),
        greeting=get_string("password_changed_greeting", locale),
        hello_text=get_string("password_changed_hello", locale),
        intro_text=get_string("password_changed_intro", locale),
        warning_text=get_string("password_changed_warning", locale),
        when_label=get_string("password_changed_when", locale),
        closing_text=get_string("password_changed_closing", locale),
    )


def render_password_reset(
    locale: str,
    reset_url: str,
    user_name: Optional[str] = None,
) -> tuple[str, str]:
    """Render password reset request email."""
    # Reuse the email_verification template with different strings
    return render_email_template(
        "email_verification",
        locale=locale,
        verification_url=reset_url,
        user_name=user_name,
        subject=get_string("password_reset_subject", locale),
        greeting=get_string("password_reset_greeting", locale),
        hello_text=get_string("password_reset_hello", locale),
        intro_text=get_string("password_reset_intro", locale),
        action_button_text=get_string("password_reset_action", locale),
        important_label=get_string("password_reset_important", locale),
        expiration_text=get_string("password_reset_expiration", locale),
        link_instruction=get_string("password_reset_link_instruction", locale),
        closing_text=get_string("password_reset_closing", locale),
    )


def render_session_approved(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render session approved notification email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    # Reuse booking_confirmed template structure
    return render_email_template(
        "booking_confirmed",
        locale=locale,
        subject=get_string("session_approved_subject", locale, session_title=session_title),
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        action_url=action_url,
        greeting=get_string("session_approved_greeting", locale),
        intro_text=get_string("session_approved_intro", locale),
        reminder_text="",
        action_button_text=get_string("session_approved_action", locale),
        closing_text=get_string("session_approved_closing", locale),
    )


def render_session_rejected(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    rejection_reason: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render session rejected notification email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    # Reuse session_cancelled template structure
    return render_email_template(
        "session_cancelled",
        locale=locale,
        subject=get_string("session_rejected_subject", locale, session_title=session_title),
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        cancellation_reason=rejection_reason,
        action_url=action_url,
        greeting=get_string("session_rejected_greeting", locale),
        alert_text="",
        intro_text=get_string("session_rejected_intro", locale),
        apology_text=get_string("session_rejected_closing", locale),
        action_button_text=get_string("session_rejected_action", locale),
    )


def render_changes_requested(
    locale: str,
    session_title: str,
    exhibition_title: str,
    scheduled_start: datetime,
    comment: Optional[str] = None,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render changes requested notification email."""
    date_str, time_str = format_datetime(scheduled_start, locale)

    # Reuse session_cancelled template structure
    return render_email_template(
        "session_cancelled",
        locale=locale,
        subject=get_string("changes_requested_subject", locale, session_title=session_title),
        session_title=session_title,
        exhibition_title=exhibition_title,
        scheduled_date=date_str,
        scheduled_time=time_str,
        cancellation_reason=comment,
        action_url=action_url,
        greeting=get_string("changes_requested_greeting", locale),
        alert_text="",
        intro_text=get_string("changes_requested_intro", locale),
        apology_text=get_string("changes_requested_closing", locale),
        action_button_text=get_string("changes_requested_action", locale),
        reason_label=get_string("comment_label", locale),
    )


def render_exhibition_unregistered(
    locale: str,
    exhibition_title: str,
    booking_count: int = 0,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render exhibition unregistration confirmation email (Issue #77)."""
    bookings_cancelled_text = ""
    if booking_count > 0:
        bookings_cancelled_text = get_string(
            "exhibition_unregistered_bookings_cancelled",
            locale,
            booking_count=booking_count,
        )

    return render_email_template(
        "exhibition_unregistered",
        locale=locale,
        subject=get_string("exhibition_unregistered_subject", locale, exhibition_title=exhibition_title),
        exhibition_title=exhibition_title,
        booking_count=booking_count,
        bookings_cancelled_text=bookings_cancelled_text,
        action_url=action_url,
        greeting=get_string("exhibition_unregistered_greeting", locale),
        intro_text=get_string("exhibition_unregistered_intro", locale),
        action_button_text=get_string("exhibition_unregistered_action", locale),
        closing_text=get_string("exhibition_unregistered_closing", locale),
    )


# =============================================================================
# Event Request Notifications (Issue #92)
# =============================================================================

def render_event_request_approved(
    locale: str,
    event_title: str,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render event request approved notification email."""
    return render_email_template(
        "event_request_notification",
        locale=locale,
        subject=get_string("event_request_approved_subject", locale, event_title=event_title),
        event_title=event_title,
        action_url=action_url,
        greeting=get_string("event_request_approved_greeting", locale),
        intro_text=get_string("event_request_approved_intro", locale),
        action_button_text=get_string("event_request_approved_action", locale),
        closing_text=get_string("event_request_approved_closing", locale),
    )


def render_event_request_rejected(
    locale: str,
    event_title: str,
    admin_comment: str,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render event request rejected notification email."""
    return render_email_template(
        "event_request_notification",
        locale=locale,
        subject=get_string("event_request_rejected_subject", locale, event_title=event_title),
        event_title=event_title,
        admin_comment=admin_comment,
        action_url=action_url,
        greeting=get_string("event_request_rejected_greeting", locale),
        intro_text=get_string("event_request_rejected_intro", locale),
        action_button_text=get_string("event_request_rejected_action", locale),
        closing_text=get_string("event_request_rejected_closing", locale),
        reason_label=get_string("reason_label", locale),
    )


def render_event_request_changes(
    locale: str,
    event_title: str,
    admin_comment: str,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render event request changes requested notification email."""
    return render_email_template(
        "event_request_notification",
        locale=locale,
        subject=get_string("event_request_changes_subject", locale, event_title=event_title),
        event_title=event_title,
        admin_comment=admin_comment,
        action_url=action_url,
        greeting=get_string("event_request_changes_greeting", locale),
        intro_text=get_string("event_request_changes_intro", locale),
        action_button_text=get_string("event_request_changes_action", locale),
        closing_text=get_string("event_request_changes_closing", locale),
        reason_label=get_string("comment_label", locale),
    )


def render_event_request_submitted(
    locale: str,
    event_title: str,
    organization_name: str,
    requester_name: str,
    requester_email: str,
    action_url: Optional[str] = None,
    is_resubmission: bool = False,
) -> tuple[str, str]:
    """Render event request submitted notification email (for admins)."""
    # Use different strings for resubmission vs new submission
    prefix = "event_request_resubmitted" if is_resubmission else "event_request_submitted"

    return render_email_template(
        "event_request_submitted",
        locale=locale,
        subject=get_string(f"{prefix}_subject", locale),
        event_title=event_title,
        organization_name=organization_name,
        requester_name=requester_name,
        requester_email=requester_email,
        action_url=action_url,
        greeting=get_string(f"{prefix}_greeting", locale),
        intro_text=get_string(f"{prefix}_intro", locale),
        action_button_text=get_string("event_request_submitted_action", locale),
        closing_text=get_string("event_request_submitted_closing", locale),
        requester_label=get_string("requester_label", locale),
        event_title_label=get_string("event_title_label", locale),
        organization_label=get_string("organization_label", locale),
    )


def render_event_request_confirmation(
    locale: str,
    event_title: str,
    organization_name: str,
    action_url: Optional[str] = None,
) -> tuple[str, str]:
    """Render event request confirmation email (for requester)."""
    return render_email_template(
        "event_request_notification",
        locale=locale,
        subject=get_string("event_request_confirmation_subject", locale, event_title=event_title),
        event_title=event_title,
        organization_name=organization_name,
        action_url=action_url,
        greeting=get_string("event_request_confirmation_greeting", locale),
        intro_text=get_string("event_request_confirmation_intro", locale),
        action_button_text=get_string("event_request_confirmation_action", locale),
        closing_text=get_string("event_request_confirmation_closing", locale),
        event_title_label=get_string("event_title_label", locale),
        organization_label=get_string("organization_label", locale),
    )