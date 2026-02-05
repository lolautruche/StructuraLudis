"""
Generate GROG Top 100 Fixtures

Issue #55 - External Game Database Sync.

This script fetches the 100 most popular RPGs from GROG (based on review count)
and saves them as a JSON file for seeding.

It uses:
1. GrogBrowserClient (Playwright) to list all games by letter (JS filtering)
2. GrogClient (httpx) to fetch details for each game (with rate limiting)

This script should be run manually when you want to refresh the fixtures.
The generated file is committed to the repository for reproducible seeding.

Requirements:
    poetry add playwright
    playwright install chromium

Usage:
    python scripts/generate_grog_fixtures.py [--limit=N] [--letters=ABC]

Options:
    --limit=N       Limit to top N games (default: 100)
    --letters=ABC   Only scan specific letters (default: all)

Output:
    backend/fixtures/grog_top_100.json
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.grog_browser_client import GrogBrowserClient
from app.services.grog_client import GrogClient, GrogGame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def progress_callback(message: str, current: int, total: int) -> None:
    """Print progress to console."""
    if total > 0:
        percent = (current / total) * 100
        print(f"\r[{percent:5.1f}%] {message:<60}", end="", flush=True)
    else:
        print(f"\r{message:<60}", end="", flush=True)


async def generate_fixtures(limit: int = 100, letters: str | None = None):
    """Fetch top games from GROG and save to fixtures file."""
    print("=" * 60)
    print("GROG Top 100 Fixtures Generator")
    print("=" * 60)

    letter_list = list(letters.lower()) if letters else None

    # Phase 1: Get all game slugs using browser client
    print("\nPhase 1: Listing all games (using Playwright browser)...")

    all_slugs = []
    async with GrogBrowserClient(headless=True) as browser_client:
        all_slugs = await browser_client.list_all_game_slugs(
            callback=progress_callback,
            letters=letter_list,
        )

    print(f"\n\nFound {len(all_slugs)} unique games\n")

    if not all_slugs:
        print("No games found! Aborting.")
        return

    # Phase 2: Fetch details for each game
    print("Phase 2: Fetching game details (rate limited, 1 req/sec)...")
    print(f"This will take approximately {len(all_slugs)} seconds.\n")

    client = GrogClient()
    all_games: list[GrogGame] = []
    failed_slugs = []

    for i, slug in enumerate(all_slugs):
        progress_callback(f"Fetching {slug}...", i, len(all_slugs))

        try:
            game = await client.get_game_details(slug)
            if game:
                all_games.append(game)
            else:
                failed_slugs.append(slug)
        except Exception as e:
            logger.error(f"Failed to fetch {slug}: {e}")
            failed_slugs.append(slug)

    print(f"\n\nFetched {len(all_games)} games ({len(failed_slugs)} failed)\n")

    if failed_slugs:
        print(f"Failed slugs: {failed_slugs[:10]}{'...' if len(failed_slugs) > 10 else ''}")

    # Phase 3: Sort by popularity and take top N
    print(f"Phase 3: Sorting by popularity and selecting top {limit}...")

    sorted_games = sorted(
        all_games,
        key=lambda g: (-g.reviews_count, g.title.lower())
    )
    top_games = sorted_games[:limit]

    print(f"Selected top {len(top_games)} games\n")

    # Convert to serializable format
    fixtures_data = []
    for game in top_games:
        fixtures_data.append({
            "slug": game.slug,
            "title": game.title,
            "url": game.url,
            "publisher": game.publisher,
            "description": game.description,
            "cover_image_url": game.cover_image_url,
            "themes": game.themes,
            "reviews_count": game.reviews_count,
        })

    # Save to fixtures file
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "grog_top_100.json"
    fixtures_path.parent.mkdir(parents=True, exist_ok=True)

    with open(fixtures_path, "w", encoding="utf-8") as f:
        json.dump(fixtures_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(fixtures_data)} games to {fixtures_path}")

    # Print top 10 for verification
    print("\nTop 10 games by popularity:")
    for i, game in enumerate(top_games[:10], 1):
        print(f"  {i:2}. {game.title} ({game.reviews_count} reviews)")

    print("\n" + "=" * 60)
    print("Done! Fixtures saved to backend/fixtures/grog_top_100.json")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Generate GROG top 100 fixtures"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of top games to include (default: 100)"
    )
    parser.add_argument(
        "--letters",
        type=str,
        help="Only scan specific letters (e.g., 'ABC' for A, B, C)"
    )

    args = parser.parse_args()

    asyncio.run(generate_fixtures(limit=args.limit, letters=args.letters))


if __name__ == "__main__":
    main()
