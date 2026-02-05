"""
GROG Browser Client using Playwright.

Issue #55 - External Game Database Sync.

This client uses a headless browser to scrape game listings from GROG,
which uses JSF/RichFaces with AJAX filtering that can't be replicated
with simple HTTP requests.

Usage:
    async with GrogBrowserClient() as client:
        slugs = await client.list_games_by_letter("a")
        all_slugs = await client.list_all_game_slugs()
"""
import asyncio
import logging
import re
from typing import Callable, Optional

from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


class GrogBrowserClient:
    """
    Browser-based client for scraping GROG game listings.

    Uses Playwright to handle JSF/AJAX filtering that requires JavaScript execution.
    """

    BASE_URL = "https://www.legrog.org"
    GAMES_URL = f"{BASE_URL}/jeux"

    # Alphabet index mapping (0-indexed in GROG's JSF)
    # Index 0 = "0-9", Index 1 = "A", Index 2 = "B", etc.
    LETTER_TO_INDEX = {
        "0": 0, "#": 0,
        "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7,
        "h": 8, "i": 9, "j": 10, "k": 11, "l": 12, "m": 13, "n": 14,
        "o": 15, "p": 16, "q": 17, "r": 18, "s": 19, "t": 20, "u": 21,
        "v": 22, "w": 23, "x": 24, "y": 25, "z": 26,
    }

    def __init__(self, headless: bool = True):
        """
        Initialize the browser client.

        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        """Start the browser."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the browser."""
        await self.close()

    async def start(self) -> None:
        """Launch the browser and create a page."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        logger.info("Browser started")

    async def close(self) -> None:
        """Close the browser."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def _navigate_to_games(self) -> None:
        """Navigate to the games listing page and wait for it to load."""
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self._page.goto(self.GAMES_URL)
        # Wait for the games table to be visible
        await self._page.wait_for_selector("table", timeout=10000)
        logger.debug("Navigated to games page")

    async def _click_letter_filter(self, letter: str) -> None:
        """
        Click on an alphabet letter to filter games.

        Args:
            letter: Single letter (a-z) or "0" for numeric
        """
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")

        letter = letter.lower()
        if letter not in self.LETTER_TO_INDEX:
            raise ValueError(f"Invalid letter: {letter}")

        index = self.LETTER_TO_INDEX[letter]
        display_letter = letter.upper() if letter != "0" else "0-9"

        # GROG uses JSF/A4J with onclick handlers like:
        # onclick="A4J.AJAX.Submit(...'j_id108:N:j_id110'...)"
        # where N is the letter index (1=A, 2=B, etc., 0=0-9)
        selector = f"a[onclick*='j_id108:{index}:']:has-text('{display_letter}')"

        try:
            link = self._page.locator(selector)
            count = await link.count()

            if count > 0:
                await link.first.click()
                # Wait for AJAX response and DOM update
                await self._page.wait_for_load_state("networkidle", timeout=10000)
                await asyncio.sleep(0.5)  # Extra wait for JSF to update DOM
                logger.debug(f"Clicked letter filter: {letter} (index {index})")
            else:
                logger.warning(f"Could not find letter filter for: {letter}")
        except Exception as e:
            logger.error(f"Error clicking letter filter '{letter}': {e}")

    async def _extract_game_slugs(self) -> list[str]:
        """
        Extract game slugs from the current page.

        Returns:
            List of game slugs
        """
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")

        slugs = []

        # Find all game links (pattern: /jeux/slug)
        links = await self._page.locator("a[href^='/jeux/']").all()

        for link in links:
            href = await link.get_attribute("href")
            if href:
                # Extract slug from /jeux/slug
                match = re.match(r"^/jeux/([a-z0-9-]+)$", href)
                if match:
                    slug = match.group(1)
                    if slug and slug not in slugs:
                        slugs.append(slug)

        return slugs

    async def list_games_by_letter(self, letter: str) -> list[str]:
        """
        Get list of game slugs for games starting with a given letter.

        Args:
            letter: Single letter (a-z) or "0" for numeric

        Returns:
            List of game slugs
        """
        await self._navigate_to_games()
        await self._click_letter_filter(letter)
        slugs = await self._extract_game_slugs()
        logger.info(f"Found {len(slugs)} games for letter '{letter}'")
        return slugs

    async def list_all_game_slugs(
        self,
        callback: Optional[Callable[[str, int, int], None]] = None,
        letters: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Get all game slugs from all letters.

        Args:
            callback: Optional callback(message, current, total) for progress
            letters: Optional list of letters to scan (default: a-z + 0)

        Returns:
            List of all unique game slugs
        """
        if letters is None:
            letters = list("abcdefghijklmnopqrstuvwxyz0")

        all_slugs = []
        total = len(letters)

        await self._navigate_to_games()

        for i, letter in enumerate(letters):
            if callback:
                callback(f"Scanning letter '{letter.upper()}'...", i, total)

            try:
                await self._click_letter_filter(letter)
                slugs = await self._extract_game_slugs()

                # Add new slugs
                for slug in slugs:
                    if slug not in all_slugs:
                        all_slugs.append(slug)

                logger.info(f"Letter '{letter}': {len(slugs)} games (total: {len(all_slugs)})")

            except Exception as e:
                logger.error(f"Error scanning letter '{letter}': {e}")

        if callback:
            callback(f"Found {len(all_slugs)} unique games", total, total)

        return all_slugs


async def main():
    """Test the browser client."""
    logging.basicConfig(level=logging.INFO)

    async with GrogBrowserClient(headless=False) as client:
        # Test single letter
        slugs = await client.list_games_by_letter("a")
        print(f"\nGames starting with 'A': {len(slugs)}")
        for slug in slugs[:10]:
            print(f"  - {slug}")
        if len(slugs) > 10:
            print(f"  ... and {len(slugs) - 10} more")


if __name__ == "__main__":
    asyncio.run(main())
