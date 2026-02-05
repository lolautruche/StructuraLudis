"""
GROG (Guide du Rôliste Galactique) scraping client.

Issue #55 - External Game Database Sync.

This client fetches game data from https://www.legrog.org to populate
the games database with RPG metadata (title, publisher, themes, cover).

Rate limiting: 1 request/second to respect the server.
"""
import asyncio
import logging
import re
import warnings
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suppress BeautifulSoup warning about XML/HTML parsing
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logger = logging.getLogger(__name__)


@dataclass
class GrogGame:
    """Data structure for a game scraped from GROG."""
    slug: str
    title: str
    url: str
    publisher: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    themes: list[str] = field(default_factory=list)
    reviews_count: int = 0  # Number of reviews (for popularity sorting)


class GrogClient:
    """
    Client for scraping game data from Le GROG.

    Usage:
        client = GrogClient()
        games = await client.list_games_by_letter("a")
        game = await client.get_game_details("appel-de-cthulhu")
    """

    BASE_URL = "https://www.legrog.org"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    REQUEST_TIMEOUT = 30.0  # seconds

    def __init__(self, rate_limit_delay: float = RATE_LIMIT_DELAY):
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    async def _rate_limit(self) -> None:
        """Ensure minimum delay between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch(self, url: str, retries: int = 3) -> Optional[str]:
        """
        Fetch URL content with rate limiting and retry logic.

        Args:
            url: URL to fetch
            retries: Number of retry attempts

        Returns:
            HTML content or None if failed
        """
        await self._rate_limit()

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.REQUEST_TIMEOUT,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPError as e:
                logger.warning(f"HTTP error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def list_games_by_letter(self, letter: str) -> list[str]:
        """
        Get list of game slugs for games starting with a given letter.

        Args:
            letter: Single letter (a-z) or "0" for numeric

        Returns:
            List of game slugs
        """
        url = f"{self.BASE_URL}/jeux?letter={letter.lower()}"
        html = await self._fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        slugs = []

        # Find game links in the list
        # GROG structure: <a href="/jeux/game-slug">Game Title</a>
        for link in soup.select("a[href^='/jeux/']"):
            href = link.get("href", "")
            # Extract slug from /jeux/slug
            match = re.match(r"^/jeux/([a-z0-9-]+)$", href)
            if match:
                slug = match.group(1)
                # Skip pagination and special links
                if slug not in ["?", ""] and not slug.startswith("?"):
                    slugs.append(slug)

        # Remove duplicates while preserving order
        seen = set()
        unique_slugs = []
        for slug in slugs:
            if slug not in seen:
                seen.add(slug)
                unique_slugs.append(slug)

        return unique_slugs

    async def get_game_details(self, slug: str) -> Optional[GrogGame]:
        """
        Fetch detailed information for a single game.

        Args:
            slug: Game slug (e.g., "appel-de-cthulhu")

        Returns:
            GrogGame with full details or None if not found
        """
        url = f"{self.BASE_URL}/jeux/{slug}"
        html = await self._fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")
        page_text = str(soup)

        # Extract title from <title> tag (GROG pattern: "Game Name / English Name")
        title_tag = soup.select_one("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Take the first part before " / " or " - " separator
            title = re.split(r"\s*/\s*|\s*-\s*Le GROG", title_text)[0].strip()
            # Remove " (L')" suffix common in French titles
            title = re.sub(r"\s*\([LlDd]'\)$", "", title)
        else:
            title = slug.replace("-", " ").title()

        game = GrogGame(
            slug=slug,
            title=title,
            url=url,
        )

        # Extract publisher from first edition in table or text
        # Look for links to /editeurs/
        publisher_links = soup.select("a[href*='/editeurs/']")
        if publisher_links:
            # Get unique publishers
            publishers = []
            for link in publisher_links[:3]:  # First 3 publishers max
                pub = link.get_text(strip=True)
                if pub and pub not in publishers:
                    publishers.append(pub)
            if publishers:
                game.publisher = " / ".join(publishers)

        # Extract description - look for description section or first substantial text
        # GROG often has description after "Description" heading
        desc_heading = soup.find(string=re.compile(r"Description", re.IGNORECASE))
        if desc_heading:
            parent = desc_heading.find_parent()
            if parent:
                # Get next sibling paragraphs
                next_p = parent.find_next("p")
                if next_p:
                    game.description = next_p.get_text(strip=True)[:2000]

        # Fallback: find any substantial paragraph
        if not game.description:
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 100:  # Substantial paragraph
                    game.description = text[:2000]
                    break

        # Extract cover image - GROG pattern: /visuels/gammes/{id}.jpg
        img_match = re.search(r'src=["\']?(/visuels/gammes/[^"\'>\s]+)', page_text)
        if img_match:
            game.cover_image_url = urljoin(self.BASE_URL, img_match.group(1))
        else:
            # Try finding any image with visuels in src
            img = soup.select_one("img[src*='visuels']")
            if img:
                game.cover_image_url = urljoin(self.BASE_URL, img.get("src", ""))

        # Extract themes - GROG pattern: "Thème(s) :" followed by links to /themes/
        themes = []
        # Skip navigation/index links
        skip_themes = {"Index thématique", "Index", "Thèmes"}
        theme_links = soup.select("a[href*='/themes/']")
        for link in theme_links:
            theme = link.get_text(strip=True)
            if theme and theme not in themes and theme not in skip_themes and len(theme) < 50:
                themes.append(theme)
        game.themes = themes[:10]  # Limit to 10 themes

        # Extract reviews count - GROG pattern: "Nombre de critiques :&nbsp;</strong>725"
        # Note: there may be HTML tags and &nbsp; between the colon and the number
        critique_match = re.search(
            r"Nombre de critiques[^<]*(?:<[^>]*>)*[^\d]*(\d+)",
            page_text,
            re.IGNORECASE
        )
        if critique_match:
            game.reviews_count = int(critique_match.group(1))

        return game

    async def list_all_letters(self) -> list[str]:
        """Get all letters that have games (a-z + 0)."""
        return list("abcdefghijklmnopqrstuvwxyz0")

    async def import_all_games(
        self,
        callback: Optional[Callable[[str, int, int], None]] = None,
        letters: Optional[list[str]] = None,
    ) -> list[GrogGame]:
        """
        Import all games from GROG.

        Args:
            callback: Optional callback(status_message, current, total) for progress
            letters: Optional list of letters to import (default: all)

        Returns:
            List of all imported GrogGame objects
        """
        if letters is None:
            letters = await self.list_all_letters()

        all_games: list[GrogGame] = []
        all_slugs: list[str] = []

        # Phase 1: Collect all slugs
        if callback:
            callback("Collecting game list...", 0, len(letters))

        for i, letter in enumerate(letters):
            slugs = await self.list_games_by_letter(letter)
            all_slugs.extend(slugs)
            if callback:
                callback(f"Collected {len(all_slugs)} games from letters {letters[:i+1]}", i + 1, len(letters))

        # Remove duplicates
        all_slugs = list(dict.fromkeys(all_slugs))
        logger.info(f"Found {len(all_slugs)} unique games to import")

        # Phase 2: Fetch details for each game
        if callback:
            callback(f"Fetching details for {len(all_slugs)} games...", 0, len(all_slugs))

        failed_slugs = []
        for i, slug in enumerate(all_slugs):
            try:
                game = await self.get_game_details(slug)
                if game:
                    all_games.append(game)
                else:
                    failed_slugs.append(slug)
            except Exception as e:
                logger.error(f"Failed to fetch {slug}: {e}")
                failed_slugs.append(slug)

            if callback and (i + 1) % 10 == 0:
                callback(
                    f"Fetched {len(all_games)}/{len(all_slugs)} games ({len(failed_slugs)} failed)",
                    i + 1,
                    len(all_slugs)
                )

        if failed_slugs:
            logger.warning(f"Failed to fetch {len(failed_slugs)} games: {failed_slugs[:10]}...")

        return all_games

    async def get_top_games(
        self,
        limit: int = 100,
        callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> list[GrogGame]:
        """
        Get top games sorted by popularity (review count).

        Args:
            limit: Number of top games to return
            callback: Optional progress callback

        Returns:
            List of top games sorted by review count
        """
        all_games = await self.import_all_games(callback=callback)

        # Sort by review count (descending) then by title (ascending)
        sorted_games = sorted(
            all_games,
            key=lambda g: (-g.reviews_count, g.title.lower())
        )

        return sorted_games[:limit]
