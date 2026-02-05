"""
Generate GROG Top 100 Fixtures

Issue #55 - External Game Database Sync.

This script fetches the 100 most popular RPGs from GROG (based on review count)
and saves them as a JSON file for seeding.

This script should be run manually when you want to refresh the fixtures.
The generated file is committed to the repository for reproducible seeding.

Usage:
    python scripts/generate_grog_fixtures.py

Output:
    backend/fixtures/grog_top_100.json
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.grog_client import GrogClient


def progress_callback(message: str, current: int, total: int) -> None:
    """Print progress to console."""
    if total > 0:
        percent = (current / total) * 100
        print(f"\r[{percent:5.1f}%] {message}", end="", flush=True)
    else:
        print(f"\r{message}", end="", flush=True)


async def generate_fixtures():
    """Fetch top 100 games from GROG and save to fixtures file."""
    print("=" * 60)
    print("GROG Top 100 Fixtures Generator")
    print("=" * 60)

    client = GrogClient()

    print("\nFetching games from GROG (this may take 10-15 minutes)...")
    print("Rate limiting: 1 request/second to respect the server.\n")

    top_games = await client.get_top_games(limit=100, callback=progress_callback)

    print(f"\n\nFetched {len(top_games)} top games by popularity\n")

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


if __name__ == "__main__":
    asyncio.run(generate_fixtures())
