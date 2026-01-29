"""
Internationalization (i18n) utilities.

Provides helpers for resolving translated content from JSONB fields
based on user locale with appropriate fallbacks.
"""
from typing import Any, Optional


def resolve_translation(
    i18n_field: Optional[dict],
    default_value: str,
    locale: str,
    fallback_locale: str = "en",
) -> str:
    """
    Resolve a translated value from an i18n JSONB field.

    Resolution order:
    1. Exact locale match (e.g., "fr")
    2. Language prefix match (e.g., "fr" from "fr-FR")
    3. Fallback locale (default: "en")
    4. Default field value

    Args:
        i18n_field: JSONB dict with locale keys (e.g., {"en": "Hello", "fr": "Bonjour"})
        default_value: The default field value to use as final fallback
        locale: The requested locale (e.g., "fr", "fr-FR")
        fallback_locale: The fallback locale if requested isn't available

    Returns:
        The resolved translated string
    """
    if not i18n_field or not isinstance(i18n_field, dict):
        return default_value

    # Try exact match
    if locale in i18n_field:
        return i18n_field[locale]

    # Try language prefix (e.g., "fr" from "fr-FR")
    lang_prefix = locale.split("-")[0].split("_")[0]
    if lang_prefix != locale and lang_prefix in i18n_field:
        return i18n_field[lang_prefix]

    # Try fallback locale
    if fallback_locale in i18n_field:
        return i18n_field[fallback_locale]

    # Final fallback to default value
    return default_value


def parse_accept_language(header: Optional[str]) -> str:
    """
    Parse the Accept-Language header and return the preferred locale.

    Simplified parsing that returns the first language tag.
    For complex needs, use a library like `accept-language-parser`.

    Args:
        header: The Accept-Language header value (e.g., "fr-FR,fr;q=0.9,en;q=0.8")

    Returns:
        The preferred locale code (e.g., "fr") or "en" as default
    """
    if not header:
        return "en"

    # Split by comma and get first preference
    parts = header.split(",")
    if not parts:
        return "en"

    # Get the first language tag (before any quality factor)
    first_lang = parts[0].split(";")[0].strip()

    # Normalize: convert "fr-FR" to "fr" for simplicity
    # Keep full tag if needed later
    if first_lang:
        return first_lang.split("-")[0].split("_")[0].lower()

    return "en"


class LocaleContext:
    """
    Context holder for the current request's locale.

    Used to pass locale information through the request lifecycle
    without threading it through every function call.
    """

    def __init__(
        self,
        locale: str = "en",
        fallback_locale: str = "en",
    ):
        self.locale = locale
        self.fallback_locale = fallback_locale

    def resolve(
        self,
        i18n_field: Optional[dict],
        default_value: str,
    ) -> str:
        """Resolve translation using this context's locale settings."""
        return resolve_translation(
            i18n_field=i18n_field,
            default_value=default_value,
            locale=self.locale,
            fallback_locale=self.fallback_locale,
        )