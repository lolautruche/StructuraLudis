from app.api.deps.auth import get_current_user, get_current_user_optional, get_current_active_user, get_current_verified_user
from app.api.deps.permissions import (
    require_roles,
    has_exhibition_role,
    get_user_exhibition_role,
    can_manage_exhibition,
    can_manage_zone,
    require_exhibition_organizer,
    require_zone_manager,
)
from app.api.deps.i18n import (
    get_locale_context,
    get_locale_context_with_user,
    get_locale_context_anonymous,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_verified_user",
    "require_roles",
    "has_exhibition_role",
    "get_user_exhibition_role",
    "can_manage_exhibition",
    "can_manage_zone",
    "require_exhibition_organizer",
    "require_zone_manager",
    "get_locale_context",
    "get_locale_context_with_user",
    "get_locale_context_anonymous",
]
