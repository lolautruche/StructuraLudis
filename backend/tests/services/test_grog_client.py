"""
Tests for GROG Client Service.

Issue #55 - External Game Database Sync.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.grog_client import GrogClient, GrogGame


class TestGrogGame:
    """Tests for GrogGame dataclass."""

    def test_grog_game_creation(self):
        """Test creating a GrogGame with required fields."""
        game = GrogGame(
            slug="appel-de-cthulhu",
            title="L'Appel de Cthulhu",
            url="https://www.legrog.org/jeux/appel-de-cthulhu",
        )
        assert game.slug == "appel-de-cthulhu"
        assert game.title == "L'Appel de Cthulhu"
        assert game.url == "https://www.legrog.org/jeux/appel-de-cthulhu"
        assert game.publisher is None
        assert game.themes == []
        assert game.reviews_count == 0

    def test_grog_game_with_all_fields(self):
        """Test creating a GrogGame with all fields."""
        game = GrogGame(
            slug="vampire-la-mascarade",
            title="Vampire : La Mascarade",
            url="https://www.legrog.org/jeux/vampire-la-mascarade",
            publisher="White Wolf",
            description="Incarnez un vampire...",
            cover_image_url="https://www.legrog.org/visuels/gammes/51.jpg",
            themes=["Horreur", "Vampires"],
            reviews_count=167,
        )
        assert game.publisher == "White Wolf"
        assert game.description == "Incarnez un vampire..."
        assert game.cover_image_url == "https://www.legrog.org/visuels/gammes/51.jpg"
        assert game.themes == ["Horreur", "Vampires"]
        assert game.reviews_count == 167


class TestGrogClient:
    """Tests for GrogClient."""

    @pytest.fixture
    def client(self):
        """Create a GrogClient with no rate limiting for tests."""
        return GrogClient(rate_limit_delay=0)

    @pytest.fixture
    def mock_html_list_page(self):
        """Sample HTML for a game list page."""
        return """
        <html>
        <body>
            <div class="game-list">
                <a href="/jeux/appel-de-cthulhu">L'Appel de Cthulhu</a>
                <a href="/jeux/ars-magica">Ars Magica</a>
                <a href="/jeux/alien-rpg">Alien RPG</a>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def mock_html_game_page(self):
        """Sample HTML for a game detail page (matches real GROG structure)."""
        return """
        <html>
        <head>
            <title>L'Appel de Cthulhu - Le GROG</title>
        </head>
        <body>
            <h1 class="page-title">L'Appel de Cthulhu</h1>
            <a href="/editeurs/chaosium">Chaosium</a>
            <a href="/editeurs/edge">Edge</a>
            <div class="game-description">
                Jeu d'horreur cosmique dans l'univers de H.P. Lovecraft.
            </div>
            <img class="game-cover" src="/visuels/gammes/286.jpg">
            <div class="themes">
                <a href="/themes/horreur">Horreur</a>
                <a href="/themes/lovecraft">Lovecraft</a>
            </div>
            <strong>Nombre de critiques :</strong>245
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_list_games_by_letter(self, client, mock_html_list_page):
        """Test fetching game slugs by letter."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html_list_page

            slugs = await client.list_games_by_letter("a")

            assert "appel-de-cthulhu" in slugs
            assert "ars-magica" in slugs
            assert "alien-rpg" in slugs
            mock_fetch.assert_called_once_with("https://www.legrog.org/jeux?letter=a")

    @pytest.mark.asyncio
    async def test_list_games_by_letter_empty(self, client):
        """Test fetching games when page is empty or fails."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            slugs = await client.list_games_by_letter("z")

            assert slugs == []

    @pytest.mark.asyncio
    async def test_list_games_removes_duplicates(self, client):
        """Test that duplicate slugs are removed."""
        html = """
        <html>
        <body>
            <a href="/jeux/appel-de-cthulhu">L'Appel de Cthulhu</a>
            <a href="/jeux/appel-de-cthulhu">L'Appel de Cthulhu (duplicate)</a>
            <a href="/jeux/ars-magica">Ars Magica</a>
        </body>
        </html>
        """
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html

            slugs = await client.list_games_by_letter("a")

            assert slugs.count("appel-de-cthulhu") == 1
            assert len(slugs) == 2

    @pytest.mark.asyncio
    async def test_get_game_details(self, client, mock_html_game_page):
        """Test fetching game details."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html_game_page

            game = await client.get_game_details("appel-de-cthulhu")

            assert game is not None
            assert game.slug == "appel-de-cthulhu"
            assert game.title == "L'Appel de Cthulhu"
            assert game.url == "https://www.legrog.org/jeux/appel-de-cthulhu"
            assert game.publisher == "Chaosium / Edge"
            assert "Horreur" in game.themes
            assert game.reviews_count == 245

    @pytest.mark.asyncio
    async def test_get_game_details_not_found(self, client):
        """Test fetching non-existent game."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            game = await client.get_game_details("non-existent-game")

            assert game is None

    @pytest.mark.asyncio
    async def test_get_game_details_minimal_html(self, client):
        """Test fetching game with minimal HTML structure (fallback to slug-based title)."""
        html = """
        <html>
        <body>
            <h1>Some Content</h1>
        </body>
        </html>
        """
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html

            game = await client.get_game_details("simple-game")

            assert game is not None
            assert game.slug == "simple-game"
            # Without <title> tag, falls back to slug-based title
            assert game.title == "Simple Game"
            assert game.publisher is None
            assert game.themes == []

    @pytest.mark.asyncio
    async def test_list_all_letters(self, client):
        """Test getting all available letters."""
        letters = await client.list_all_letters()

        assert len(letters) == 27  # a-z + 0
        assert "a" in letters
        assert "z" in letters
        assert "0" in letters

    @pytest.mark.asyncio
    async def test_import_all_games_with_callback(self, client):
        """Test importing games with progress callback."""
        callback_calls = []

        def callback(message, current, total):
            callback_calls.append((message, current, total))

        # Mock the methods
        with patch.object(client, 'list_games_by_letter', new_callable=AsyncMock) as mock_list:
            with patch.object(client, 'get_game_details', new_callable=AsyncMock) as mock_details:
                mock_list.return_value = ["game-1", "game-2"]
                mock_details.side_effect = [
                    GrogGame(slug="game-1", title="Game 1", url="http://test/game-1"),
                    GrogGame(slug="game-2", title="Game 2", url="http://test/game-2"),
                ]

                games = await client.import_all_games(
                    callback=callback,
                    letters=["a"],
                )

                assert len(games) == 2
                assert len(callback_calls) > 0

    @pytest.mark.asyncio
    async def test_get_top_games(self, client):
        """Test getting top games sorted by popularity."""
        with patch.object(client, 'import_all_games', new_callable=AsyncMock) as mock_import:
            mock_import.return_value = [
                GrogGame(slug="game-1", title="Game 1", url="http://test/1", reviews_count=10),
                GrogGame(slug="game-2", title="Game 2", url="http://test/2", reviews_count=100),
                GrogGame(slug="game-3", title="Game 3", url="http://test/3", reviews_count=50),
            ]

            top_games = await client.get_top_games(limit=2)

            assert len(top_games) == 2
            assert top_games[0].reviews_count == 100  # Highest first
            assert top_games[1].reviews_count == 50


class TestGrogClientRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_rate_limit_applies(self):
        """Test that rate limiting is applied between requests."""
        import asyncio
        import time

        client = GrogClient(rate_limit_delay=0.1)  # 100ms delay

        # Track timing
        start_time = time.time()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = "<html></html>"
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Make two requests
            await client._fetch("http://test.com/1")
            await client._fetch("http://test.com/2")

        elapsed = time.time() - start_time
        # Should have waited at least 100ms between requests
        assert elapsed >= 0.1
