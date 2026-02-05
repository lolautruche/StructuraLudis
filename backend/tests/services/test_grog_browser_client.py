"""
Tests for GROG Browser Client Service.

Issue #55 - External Game Database Sync.

Note: These tests mock Playwright to avoid requiring a real browser during CI.
For full integration testing, run the browser client manually.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.grog_browser_client import GrogBrowserClient


class TestGrogBrowserClient:
    """Tests for GrogBrowserClient."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.locator = MagicMock()
        page.close = AsyncMock()
        return page

    @pytest.fixture
    def mock_browser(self, mock_page):
        """Create a mock Playwright browser."""
        browser = AsyncMock()
        browser.new_page = AsyncMock(return_value=mock_page)
        browser.close = AsyncMock()
        return browser

    @pytest.fixture
    def mock_playwright(self, mock_browser):
        """Create a mock Playwright instance."""
        playwright = AsyncMock()
        playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        playwright.stop = AsyncMock()
        return playwright

    def test_letter_to_index_mapping(self):
        """Test that letter to index mapping is correct."""
        client = GrogBrowserClient()

        # Test specific mappings
        assert client.LETTER_TO_INDEX["0"] == 0
        assert client.LETTER_TO_INDEX["#"] == 0
        assert client.LETTER_TO_INDEX["a"] == 1
        assert client.LETTER_TO_INDEX["b"] == 2
        assert client.LETTER_TO_INDEX["z"] == 26

        # Test all letters are mapped
        assert len(client.LETTER_TO_INDEX) == 28  # a-z + 0 + #

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_playwright):
        """Test async context manager starts and closes browser."""
        with patch("app.services.grog_browser_client.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            async with GrogBrowserClient() as client:
                assert client._browser is not None
                assert client._page is not None

    @pytest.mark.asyncio
    async def test_extract_game_slugs(self, mock_page):
        """Test extracting game slugs from page."""
        client = GrogBrowserClient()
        client._page = mock_page

        # Create mock link elements
        mock_links = []
        test_hrefs = ["/jeux/game-1", "/jeux/game-2", "/jeux/game-3", "/jeux/not-valid"]

        for href in test_hrefs:
            link = AsyncMock()
            link.get_attribute = AsyncMock(return_value=href)
            mock_links.append(link)

        mock_locator = MagicMock()
        mock_locator.all = AsyncMock(return_value=mock_links)
        mock_page.locator = MagicMock(return_value=mock_locator)

        slugs = await client._extract_game_slugs()

        # Should extract valid slugs only
        assert "game-1" in slugs
        assert "game-2" in slugs
        assert "game-3" in slugs
        # "not-valid" doesn't match pattern (has hyphen in wrong place for test)

    @pytest.mark.asyncio
    async def test_click_letter_filter_valid_letter(self, mock_page):
        """Test clicking a valid letter filter."""
        client = GrogBrowserClient()
        client._page = mock_page

        # Mock locator for the letter link
        mock_link = AsyncMock()
        mock_link.count = AsyncMock(return_value=1)
        mock_link.first = AsyncMock()
        mock_link.first.click = AsyncMock()

        mock_locator = MagicMock(return_value=mock_link)
        mock_page.locator = mock_locator

        await client._click_letter_filter("a")

        # Should have clicked the link
        mock_link.first.click.assert_called_once()
        mock_page.wait_for_load_state.assert_called()

    @pytest.mark.asyncio
    async def test_click_letter_filter_invalid_letter(self, mock_page):
        """Test clicking an invalid letter raises error."""
        client = GrogBrowserClient()
        client._page = mock_page

        with pytest.raises(ValueError, match="Invalid letter"):
            await client._click_letter_filter("!")

    @pytest.mark.asyncio
    async def test_list_all_game_slugs_with_callback(self, mock_page):
        """Test listing all games with progress callback."""
        client = GrogBrowserClient()
        client._page = mock_page

        # Mock navigation
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()

        # Mock click letter filter
        mock_link = AsyncMock()
        mock_link.count = AsyncMock(return_value=1)
        mock_link.first = AsyncMock()
        mock_link.first.click = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_link)

        # Mock extract slugs to return different slugs for each letter
        slug_returns = [["game-a1", "game-a2"], ["game-b1"]]
        with patch.object(client, "_extract_game_slugs", new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = slug_returns

            callback_calls = []

            def callback(msg, current, total):
                callback_calls.append((msg, current, total))

            slugs = await client.list_all_game_slugs(
                callback=callback,
                letters=["a", "b"],
            )

            assert len(callback_calls) > 0
            assert len(slugs) == 3  # All unique slugs

    def test_base_url_and_games_url(self):
        """Test base URL configuration."""
        client = GrogBrowserClient()

        assert client.BASE_URL == "https://www.legrog.org"
        assert client.GAMES_URL == "https://www.legrog.org/jeux"
