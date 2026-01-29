"""
Internationalization dependencies.

Provides locale detection and context for API endpoints.
"""
from typing import Optional

from fastapi import Depends, Header

from app.api.deps.auth import get_current_user
from app.core.i18n import LocaleContext, parse_accept_language
from app.domain.user.entity import User


async def get_locale_context(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    current_user: Optional[User] = None,
) -> LocaleContext:
    """
    Get the locale context for the current request.

    Resolution order:
    1. User's preferred locale (if authenticated and set)
    2. Accept-Language header
    3. Default to "en"
    """
    # Start with Accept-Language header
    locale = parse_accept_language(accept_language)

    # Override with user's locale if authenticated and set
    if current_user and current_user.locale:
        locale = current_user.locale

    return LocaleContext(locale=locale, fallback_locale="en")


async def get_locale_context_with_user(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    current_user: User = Depends(get_current_user),
) -> LocaleContext:
    """
    Get the locale context for authenticated requests.

    Uses user's locale preference if set.
    """
    return await get_locale_context(
        accept_language=accept_language,
        current_user=current_user,
    )


async def get_locale_context_anonymous(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
) -> LocaleContext:
    """
    Get the locale context for anonymous/public requests.

    Uses Accept-Language header only.
    """
    return await get_locale_context(
        accept_language=accept_language,
        current_user=None,
    )