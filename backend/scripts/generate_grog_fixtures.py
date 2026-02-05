"""
Generate GROG Fixtures from Curated Slugs

Issue #55 - External Game Database Sync.

This script reads a curated list of game slugs and fetches their details
from GROG to generate the fixtures JSON file.

Usage:
    # Generate fixtures from curated slugs
    python scripts/generate_grog_fixtures.py

    # Add a new game to the list and regenerate
    python scripts/generate_grog_fixtures.py --add nephilim

    # Regenerate only specific games (for testing)
    python scripts/generate_grog_fixtures.py --only appel-de-cthulhu,vampire-la-mascarade

    # Dry run (don't save)
    python scripts/generate_grog_fixtures.py --dry-run

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

from app.services.grog_client import GrogClient, GrogGame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SLUGS_FILE = Path(__file__).parent.parent / "fixtures" / "grog_curated_slugs.txt"
OUTPUT_FILE = Path(__file__).parent.parent / "fixtures" / "grog_top_100.json"


def load_slugs() -> list[str]:
    """Load slugs from the curated slugs file."""
    if not SLUGS_FILE.exists():
        logger.error(f"Slugs file not found: {SLUGS_FILE}")
        return []

    slugs = []
    with open(SLUGS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                slugs.append(line)

    # Remove duplicates while preserving order
    seen = set()
    unique_slugs = []
    for slug in slugs:
        if slug not in seen:
            seen.add(slug)
            unique_slugs.append(slug)

    return unique_slugs


def add_slug_to_file(slug: str) -> bool:
    """Add a new slug to the curated slugs file."""
    existing = load_slugs()
    if slug in existing:
        print(f"Slug '{slug}' already exists in the list.")
        return False

    with open(SLUGS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{slug}\n")

    print(f"Added '{slug}' to {SLUGS_FILE}")
    return True


def progress_callback(current: int, total: int, slug: str) -> None:
    """Print progress to console."""
    percent = (current / total) * 100 if total > 0 else 0
    print(f"\r[{percent:5.1f}%] ({current}/{total}) Fetching {slug:<40}", end="", flush=True)


async def generate_fixtures(
    slugs: list[str] | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """
    Fetch game details from GROG and generate fixtures.

    Args:
        slugs: List of slugs to fetch (default: load from file)
        dry_run: If True, don't save the output file

    Returns:
        List of game data dictionaries
    """
    if slugs is None:
        slugs = load_slugs()

    if not slugs:
        print("No slugs to process!")
        return []

    print("=" * 60)
    print("GROG Fixtures Generator")
    print("=" * 60)
    print(f"Slugs to fetch: {len(slugs)}")
    print(f"Estimated time: ~{len(slugs)} seconds ({len(slugs) // 60}min {len(slugs) % 60}s)")
    print("=" * 60)
    print()

    client = GrogClient()
    games: list[GrogGame] = []
    failed_slugs = []

    for i, slug in enumerate(slugs):
        progress_callback(i + 1, len(slugs), slug)

        try:
            game = await client.get_game_details(slug)
            if game:
                games.append(game)
            else:
                failed_slugs.append(slug)
                logger.warning(f"Game not found: {slug}")
        except Exception as e:
            failed_slugs.append(slug)
            logger.error(f"Failed to fetch {slug}: {e}")

    print()  # New line after progress
    print()
    print(f"Fetched: {len(games)} games")
    if failed_slugs:
        print(f"Failed: {len(failed_slugs)} - {failed_slugs}")

    # Sort by reviews_count (descending) for consistent ordering
    games.sort(key=lambda g: (-g.reviews_count, g.title.lower()))

    # Convert to serializable format
    fixtures_data = []
    for game in games:
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

    if dry_run:
        print("\n--- DRY RUN - Not saving ---")
        print(f"Would save {len(fixtures_data)} games to {OUTPUT_FILE}")
    else:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(fixtures_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(fixtures_data)} games to {OUTPUT_FILE}")

    # Print top 10
    print("\nTop 10 by popularity:")
    for i, game in enumerate(games[:10], 1):
        print(f"  {i:2}. {game.title} ({game.reviews_count} reviews)")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    return fixtures_data


def main():
    parser = argparse.ArgumentParser(
        description="Generate GROG fixtures from curated slugs"
    )
    parser.add_argument(
        "--add",
        type=str,
        metavar="SLUG",
        help="Add a new slug to the curated list and regenerate"
    )
    parser.add_argument(
        "--only",
        type=str,
        metavar="SLUGS",
        help="Only process specific slugs (comma-separated)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save the output file"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Just list current slugs without fetching"
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        slugs = load_slugs()
        print(f"Curated slugs ({len(slugs)}):")
        for slug in slugs:
            print(f"  - {slug}")
        return

    # Add mode
    if args.add:
        add_slug_to_file(args.add)
        # Continue to regenerate

    # Determine which slugs to process
    if args.only:
        slugs = [s.strip() for s in args.only.split(",")]
    else:
        slugs = None  # Will load from file

    asyncio.run(generate_fixtures(slugs=slugs, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
