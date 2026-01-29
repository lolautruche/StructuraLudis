"""
Tests for internationalization (i18n) utilities.
"""
import pytest
from app.core.i18n import (
    resolve_translation,
    parse_accept_language,
    LocaleContext,
)


class TestResolveTranslation:
    """Tests for resolve_translation function."""

    def test_exact_locale_match(self):
        """Returns exact locale match when available."""
        i18n = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}
        result = resolve_translation(i18n, "Default", "fr")
        assert result == "Bonjour"

    def test_language_prefix_match(self):
        """Falls back to language prefix when exact match not found."""
        i18n = {"en": "Hello", "fr": "Bonjour"}
        result = resolve_translation(i18n, "Default", "fr-CA")
        assert result == "Bonjour"

    def test_fallback_locale(self):
        """Falls back to fallback locale when requested locale not found."""
        i18n = {"en": "Hello", "de": "Hallo"}
        result = resolve_translation(i18n, "Default", "fr", fallback_locale="en")
        assert result == "Hello"

    def test_default_value_fallback(self):
        """Falls back to default value when no translation found."""
        i18n = {"de": "Hallo"}
        result = resolve_translation(i18n, "Default", "fr", fallback_locale="en")
        assert result == "Default"

    def test_none_i18n_field(self):
        """Returns default when i18n field is None."""
        result = resolve_translation(None, "Default", "fr")
        assert result == "Default"

    def test_empty_i18n_field(self):
        """Returns default when i18n field is empty dict."""
        result = resolve_translation({}, "Default", "fr")
        assert result == "Default"

    def test_invalid_i18n_type(self):
        """Returns default when i18n field is not a dict."""
        result = resolve_translation("not a dict", "Default", "fr")
        assert result == "Default"

    def test_underscore_locale_format(self):
        """Handles underscore format (fr_FR) same as dash format."""
        i18n = {"en": "Hello", "fr": "Bonjour"}
        result = resolve_translation(i18n, "Default", "fr_FR")
        assert result == "Bonjour"


class TestParseAcceptLanguage:
    """Tests for parse_accept_language function."""

    def test_simple_language(self):
        """Parses simple language code."""
        result = parse_accept_language("fr")
        assert result == "fr"

    def test_language_with_region(self):
        """Extracts language from regional variant."""
        result = parse_accept_language("fr-FR")
        assert result == "fr"

    def test_quality_factors(self):
        """Takes first language, ignoring quality factors."""
        result = parse_accept_language("fr-FR,fr;q=0.9,en;q=0.8")
        assert result == "fr"

    def test_multiple_languages(self):
        """Takes first language from list."""
        result = parse_accept_language("de, en-US, en")
        assert result == "de"

    def test_none_header(self):
        """Returns 'en' for None header."""
        result = parse_accept_language(None)
        assert result == "en"

    def test_empty_header(self):
        """Returns 'en' for empty header."""
        result = parse_accept_language("")
        assert result == "en"

    def test_uppercase_to_lowercase(self):
        """Normalizes to lowercase."""
        result = parse_accept_language("FR-FR")
        assert result == "fr"


class TestLocaleContext:
    """Tests for LocaleContext class."""

    def test_resolve_with_context(self):
        """Resolves translation using context settings."""
        ctx = LocaleContext(locale="fr", fallback_locale="en")
        i18n = {"en": "Hello", "fr": "Bonjour"}
        result = ctx.resolve(i18n, "Default")
        assert result == "Bonjour"

    def test_context_fallback(self):
        """Uses context fallback locale."""
        ctx = LocaleContext(locale="de", fallback_locale="en")
        i18n = {"en": "Hello", "fr": "Bonjour"}
        result = ctx.resolve(i18n, "Default")
        assert result == "Hello"

    def test_context_default_fallback(self):
        """Uses default value when context fallback not found."""
        ctx = LocaleContext(locale="de", fallback_locale="es")
        i18n = {"en": "Hello", "fr": "Bonjour"}
        result = ctx.resolve(i18n, "Default")
        assert result == "Default"


class TestI18nIntegration:
    """Integration tests for i18n with API schemas."""

    def test_game_category_with_i18n(self):
        """GameCategory schema accepts i18n fields."""
        from app.domain.game.schemas import GameCategoryCreate

        category = GameCategoryCreate(
            name="Role-playing Game",
            slug="rpg",
            name_i18n={"fr": "Jeu de rôle", "de": "Rollenspiel"}
        )
        assert category.name == "Role-playing Game"
        assert category.name_i18n["fr"] == "Jeu de rôle"

    def test_exhibition_with_i18n(self):
        """Exhibition schema accepts i18n fields."""
        from datetime import datetime, timezone
        from uuid import uuid4
        from app.domain.exhibition.schemas import ExhibitionCreate

        exhibition = ExhibitionCreate(
            title="Paris Gaming Con 2026",
            slug="paris-gaming-2026",
            organization_id=uuid4(),
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 3, tzinfo=timezone.utc),
            title_i18n={"fr": "Convention de Jeux Paris 2026"},
            description_i18n={"fr": "La plus grande convention de jeux en France"}
        )
        assert exhibition.title == "Paris Gaming Con 2026"
        assert exhibition.title_i18n["fr"] == "Convention de Jeux Paris 2026"

    def test_safety_tool_with_i18n(self):
        """SafetyTool schema accepts i18n fields."""
        from uuid import uuid4
        from app.domain.exhibition.schemas import SafetyToolCreate

        tool = SafetyToolCreate(
            name="X-Card",
            slug="x-card",
            exhibition_id=uuid4(),
            description="A safety tool for tabletop games",
            name_i18n={"fr": "Carte X"},
            description_i18n={"fr": "Un outil de sécurité pour les jeux de table"}
        )
        assert tool.name == "X-Card"
        assert tool.name_i18n["fr"] == "Carte X"

    def test_zone_with_i18n(self):
        """Zone schema accepts i18n fields."""
        from uuid import uuid4
        from app.domain.exhibition.schemas import ZoneCreate

        zone = ZoneCreate(
            name="RPG Area",
            exhibition_id=uuid4(),
            name_i18n={"fr": "Espace JDR", "de": "Rollenspielbereich"},
            description_i18n={"fr": "Zone dédiée aux jeux de rôle"}
        )
        assert zone.name == "RPG Area"
        assert zone.name_i18n["fr"] == "Espace JDR"