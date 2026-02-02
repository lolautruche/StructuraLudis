"""
Internationalized error messages.

Provides translated error messages for API responses.
"""
from typing import Optional


# Error message translations: {message_key: {locale: message}}
MESSAGES = {
    # Auth errors
    "invalid_credentials": {
        "en": "Invalid email or password",
        "fr": "Email ou mot de passe invalide",
    },
    "account_deactivated": {
        "en": "Your account has been deactivated. Contact the administrator.",
        "fr": "Votre compte a été désactivé. Contactez l'administrateur.",
    },
    "email_not_verified": {
        "en": "Email not verified. Please check your inbox.",
        "fr": "Email non vérifié. Veuillez vérifier votre boîte de réception.",
    },
    "invalid_token": {
        "en": "Invalid or expired token",
        "fr": "Token invalide ou expiré",
    },
    "token_expired": {
        "en": "Token has expired",
        "fr": "Le token a expiré",
    },
    "email_already_exists": {
        "en": "This email address is already registered",
        "fr": "Cette adresse email est déjà utilisée",
    },
    "password_too_short": {
        "en": "Password must be at least 8 characters",
        "fr": "Le mot de passe doit contenir au moins 8 caractères",
    },
    "wrong_password": {
        "en": "Current password is incorrect",
        "fr": "Le mot de passe actuel est incorrect",
    },

    # Permission errors
    "not_authenticated": {
        "en": "Not authenticated",
        "fr": "Non authentifié",
    },
    "forbidden": {
        "en": "Access denied",
        "fr": "Accès refusé",
    },
    "only_organizers": {
        "en": "Only organizers can perform this action",
        "fr": "Seuls les organisateurs peuvent effectuer cette action",
    },
    "only_organizers_or_zone_managers": {
        "en": "Only organizers or zone managers can perform this action",
        "fr": "Seuls les organisateurs ou gestionnaires de zone peuvent effectuer cette action",
    },
    "no_zone_access": {
        "en": "You do not have access to zone '{zone_name}'",
        "fr": "Vous n'avez pas accès à la zone « {zone_name} »",
    },

    # Session errors
    "session_not_found": {
        "en": "Game session not found",
        "fr": "Session de jeu introuvable",
    },
    "cannot_moderate_status": {
        "en": "Cannot moderate a {status} session",
        "fr": "Impossible de modérer une session {status}",
    },
    "cannot_delete_non_draft": {
        "en": "Only draft sessions can be deleted",
        "fr": "Seules les sessions brouillon peuvent être supprimées",
    },
    "session_conflict": {
        "en": "You are already running session '{title}' ({start} - {end})",
        "fr": "Vous animez déjà la session « {title} » ({start} - {end})",
    },
    "booking_conflict": {
        "en": "You are registered as a player for session '{title}' ({start} - {end})",
        "fr": "Vous êtes inscrit comme joueur à la session « {title} » ({start} - {end})",
    },
    "session_exceeds_slot": {
        "en": "Session cannot end after time slot",
        "fr": "La session ne peut pas dépasser la fin du créneau",
    },
    "session_before_slot": {
        "en": "Session cannot start before time slot",
        "fr": "La session ne peut pas commencer avant le début du créneau",
    },
    "session_duration_exceeds": {
        "en": "Session duration exceeds time slot. Max duration: {max_minutes} minutes",
        "fr": "La durée de la session dépasse le créneau. Durée max : {max_minutes} minutes",
    },
    "session_duration_max_exceeded": {
        "en": "Session duration ({duration} min) exceeds maximum allowed ({max_minutes} min)",
        "fr": "La durée de la session ({duration} min) dépasse le maximum autorisé ({max_minutes} min)",
    },
    "slot_not_in_exhibition": {
        "en": "Time slot does not belong to this exhibition",
        "fr": "Le créneau horaire n'appartient pas à cet événement",
    },

    # Table errors
    "table_not_found": {
        "en": "Physical table not found",
        "fr": "Table introuvable",
    },
    "table_collision": {
        "en": "Table collision: another session '{title}' is scheduled from {start} to {end}",
        "fr": "Conflit de table : la session « {title} » est déjà prévue de {start} à {end}",
    },
    "table_already_booked": {
        "en": "Table '{table_label}' is already booked for '{title}' at this time",
        "fr": "La table « {table_label} » est déjà réservée pour « {title} » à cet horaire",
    },

    # Time slot errors
    "time_slot_not_found": {
        "en": "Time slot not found or doesn't belong to this exhibition",
        "fr": "Créneau horaire introuvable ou n'appartient pas à cet événement",
    },
    "session_would_exceed_slot": {
        "en": "Session would exceed slot '{slot_name}' end time, skipped",
        "fr": "La session dépasserait la fin du créneau « {slot_name} », ignorée",
    },

    # Zone errors
    "zone_not_found": {
        "en": "Zone not found",
        "fr": "Zone introuvable",
    },

    # Exhibition errors
    "exhibition_not_found": {
        "en": "Exhibition not found",
        "fr": "Événement introuvable",
    },

    # Game errors
    "game_not_found": {
        "en": "Game not found",
        "fr": "Jeu introuvable",
    },
    "category_slug_exists": {
        "en": "Category with this slug already exists",
        "fr": "Une catégorie avec ce slug existe déjà",
    },

    # Booking errors
    "booking_not_found": {
        "en": "Booking not found",
        "fr": "Réservation introuvable",
    },
    "session_full": {
        "en": "This session is full",
        "fr": "Cette session est complète",
    },
    "already_booked": {
        "en": "You have already booked this session",
        "fr": "Vous avez déjà réservé cette session",
    },
    "age_restriction": {
        "en": "This session requires a minimum age of {age}",
        "fr": "Cette session nécessite un âge minimum de {age} ans",
    },

    # User errors
    "user_not_found": {
        "en": "User not found",
        "fr": "Utilisateur introuvable",
    },

    # Generic errors
    "not_found": {
        "en": "Not found",
        "fr": "Introuvable",
    },
    "bad_request": {
        "en": "Bad request",
        "fr": "Requête invalide",
    },
    "conflict": {
        "en": "Conflict",
        "fr": "Conflit",
    },

    # Warnings (for batch operations)
    "warning_slot_exceeded": {
        "en": "Session would exceed slot '{slot_name}' end time, skipped",
        "fr": "La session dépasserait la fin du créneau « {slot_name} », ignorée",
    },
    "warning_table_conflict": {
        "en": "Table '{table_label}' has conflict at slot '{slot_name}', skipped",
        "fr": "La table « {table_label} » a un conflit sur le créneau « {slot_name} », ignorée",
    },
}


def get_message(
    key: str,
    locale: str = "en",
    fallback_locale: str = "en",
    **kwargs,
) -> str:
    """
    Get a translated error message.

    Args:
        key: Message key (e.g., "session_not_found")
        locale: Target locale (e.g., "fr")
        fallback_locale: Fallback locale if target not found
        **kwargs: Format parameters for the message

    Returns:
        Translated message with parameters interpolated
    """
    messages = MESSAGES.get(key, {})

    # Try exact locale
    message = messages.get(locale)

    # Try language prefix
    if not message:
        lang_prefix = locale.split("-")[0].split("_")[0]
        if lang_prefix != locale:
            message = messages.get(lang_prefix)

    # Try fallback
    if not message:
        message = messages.get(fallback_locale)

    # Final fallback to key itself
    if not message:
        message = key

    # Interpolate parameters
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # If format key missing, return message as-is

    return message
