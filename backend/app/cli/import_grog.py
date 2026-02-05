"""
GROG Game Import CLI

Issue #55 - External Game Database Sync.

Import RPG games from Le GROG (Guide du Rôliste Galactique) into the database.

Usage:
    python -m app.cli.import_grog [--force] [--from-fixtures] [--from-curated] [--full] [--slugs=x,y,z] [--dry-run]

Options:
    --force          Re-import all games (update existing)
    --from-fixtures  Import games from fixtures/grog_top_100.json (default)
    --from-curated   Import games live from GROG using curated slugs list
    --full           Import ALL games from GROG (uses browser, ~15-20 min)
    --slugs=x,y,z    Import specific games by GROG slug (comma-separated)
    --dry-run        Show what would be imported without saving
    --limit=N        Limit import to N games (for testing)
    --letter=X       Only scan games starting with letter X (for --full mode)

Examples:
    # Import games from fixtures file (default, recommended for seeding)
    python -m app.cli.import_grog --from-fixtures

    # Import games live from GROG using curated slugs list (~2 min)
    python -m app.cli.import_grog --from-curated

    # Import ALL games from GROG website (~15-20 min, requires browser)
    python -m app.cli.import_grog --full

    # Import only games starting with 'a' (for testing --full mode)
    python -m app.cli.import_grog --full --letter=a

    # Import specific games by slug (fetches live from GROG)
    python -m app.cli.import_grog --slugs=appel-de-cthulhu,vampire-la-mascarade

    # Dry run to see what would be imported
    python -m app.cli.import_grog --from-fixtures --dry-run

    # Force update existing games from live GROG data
    python -m app.cli.import_grog --from-curated --force
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domain.game.entity import Game, GameCategory
from app.domain.shared.entity import GameComplexity
from app.services.grog_client import GrogClient, GrogGame
from app.services.grog_browser_client import GrogBrowserClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_or_create_rpg_category(session) -> GameCategory:
    """Get or create the RPG game category."""
    result = await session.execute(
        select(GameCategory).filter_by(slug="rpg")
    )
    category = result.scalar_one_or_none()

    if not category:
        category = GameCategory(
            id=uuid4(),
            name="Role-Playing Game",
            slug="rpg",
            name_i18n={"fr": "Jeu de rôle", "en": "Role-Playing Game"},
        )
        session.add(category)
        await session.flush()
        logger.info("Created RPG category")

    return category


async def get_existing_game(session, slug: str) -> Game | None:
    """Get existing game by GROG slug."""
    result = await session.execute(
        select(Game).filter_by(
            external_provider="grog",
            external_provider_id=slug
        )
    )
    return result.scalar_one_or_none()


def create_game_from_grog(
    grog_game: GrogGame,
    category_id,
) -> Game:
    """Create a Game entity from GROG data."""
    return Game(
        id=uuid4(),
        category_id=category_id,
        title=grog_game.title,
        external_provider="grog",
        external_provider_id=grog_game.slug,
        external_url=grog_game.url,
        publisher=grog_game.publisher,
        description=grog_game.description,
        cover_image_url=grog_game.cover_image_url,
        themes=grog_game.themes if grog_game.themes else None,
        complexity=GameComplexity.INTERMEDIATE,  # Default
        min_players=2,  # Default for RPGs
        max_players=6,  # Default for RPGs
        last_synced_at=datetime.now(timezone.utc),
    )


def create_game_from_fixture(
    fixture_data: dict,
    category_id,
) -> Game:
    """Create a Game entity from fixture data."""
    return Game(
        id=uuid4(),
        category_id=category_id,
        title=fixture_data["title"],
        external_provider="grog",
        external_provider_id=fixture_data["slug"],
        external_url=fixture_data.get("url"),
        publisher=fixture_data.get("publisher"),
        description=fixture_data.get("description"),
        cover_image_url=fixture_data.get("cover_image_url"),
        themes=fixture_data.get("themes"),
        complexity=GameComplexity.INTERMEDIATE,
        min_players=2,
        max_players=6,
        last_synced_at=datetime.now(timezone.utc),
    )


def update_game_from_grog(game: Game, grog_game: GrogGame) -> None:
    """Update an existing Game entity with fresh GROG data."""
    game.title = grog_game.title
    game.external_url = grog_game.url
    game.publisher = grog_game.publisher
    game.description = grog_game.description
    game.cover_image_url = grog_game.cover_image_url
    game.themes = grog_game.themes if grog_game.themes else None
    game.last_synced_at = datetime.now(timezone.utc)


def update_game_from_fixture(game: Game, fixture_data: dict) -> None:
    """Update an existing Game entity with fixture data."""
    game.title = fixture_data["title"]
    game.external_url = fixture_data.get("url")
    game.publisher = fixture_data.get("publisher")
    game.description = fixture_data.get("description")
    game.cover_image_url = fixture_data.get("cover_image_url")
    game.themes = fixture_data.get("themes")
    game.last_synced_at = datetime.now(timezone.utc)


def load_fixtures() -> list[dict]:
    """Load games from fixtures file."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures" / "grog_top_100.json"
    if not fixtures_path.exists():
        logger.error(f"Fixtures file not found: {fixtures_path}")
        return []

    with open(fixtures_path, encoding="utf-8") as f:
        return json.load(f)


def load_curated_slugs() -> list[str]:
    """Load game slugs from curated slugs file."""
    slugs_path = Path(__file__).parent.parent.parent / "fixtures" / "grog_curated_slugs.txt"
    if not slugs_path.exists():
        logger.error(f"Curated slugs file not found: {slugs_path}")
        return []

    slugs = []
    with open(slugs_path, encoding="utf-8") as f:
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


async def import_from_fixtures(
    force: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """
    Import games from fixtures file.

    Args:
        force: Update existing games
        dry_run: Don't save to database
        limit: Limit number of games to import

    Returns:
        Dict with import statistics
    """
    stats = {
        "total_fetched": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    fixtures = load_fixtures()
    if not fixtures:
        print("No fixtures found!")
        return stats

    if limit:
        fixtures = fixtures[:limit]

    stats["total_fetched"] = len(fixtures)
    print(f"Loaded {len(fixtures)} games from fixtures")

    if dry_run:
        print("\n--- DRY RUN MODE ---")
        for game in fixtures[:20]:
            print(f"  - {game['title']} ({game['slug']})")
            if game.get("publisher"):
                print(f"    Publisher: {game['publisher']}")
            if game.get("themes"):
                print(f"    Themes: {', '.join(game['themes'])}")
        if len(fixtures) > 20:
            print(f"  ... and {len(fixtures) - 20} more")
        return stats

    # Import to database
    async with AsyncSessionLocal() as session:
        category = await get_or_create_rpg_category(session)

        print(f"\nImporting {len(fixtures)} games to database...")
        for i, fixture_data in enumerate(fixtures):
            try:
                existing = await get_existing_game(session, fixture_data["slug"])

                if existing:
                    if force:
                        update_game_from_fixture(existing, fixture_data)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    game = create_game_from_fixture(fixture_data, category.id)
                    session.add(game)
                    stats["created"] += 1

                if (i + 1) % 50 == 0:
                    await session.commit()
                    print(f"  Progress: {i + 1}/{len(fixtures)}")

            except Exception as e:
                logger.error(f"Failed to import {fixture_data.get('slug')}: {e}")
                stats["failed"] += 1

        await session.commit()

    return stats


async def import_from_slugs(
    slugs: list[str],
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Import specific games by slug from GROG website.

    Args:
        slugs: List of GROG slugs to import
        force: Update existing games
        dry_run: Don't save to database

    Returns:
        Dict with import statistics
    """
    stats = {
        "total_fetched": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    client = GrogClient()
    grog_games: list[GrogGame] = []

    print(f"Fetching {len(slugs)} games from GROG...")
    for slug in slugs:
        try:
            game = await client.get_game_details(slug)
            if game:
                grog_games.append(game)
                print(f"  ✓ {game.title}")
            else:
                print(f"  ✗ {slug} - not found")
                stats["failed"] += 1
        except Exception as e:
            print(f"  ✗ {slug} - error: {e}")
            stats["failed"] += 1

    stats["total_fetched"] = len(grog_games)

    if dry_run:
        print("\n--- DRY RUN MODE ---")
        for game in grog_games:
            print(f"  - {game.title} ({game.slug})")
            print(f"    Publisher: {game.publisher}")
            print(f"    Themes: {game.themes}")
            print(f"    Reviews: {game.reviews_count}")
        return stats

    # Import to database
    async with AsyncSessionLocal() as session:
        category = await get_or_create_rpg_category(session)

        print(f"\nImporting {len(grog_games)} games to database...")
        for grog_game in grog_games:
            try:
                existing = await get_existing_game(session, grog_game.slug)

                if existing:
                    if force:
                        update_game_from_grog(existing, grog_game)
                        stats["updated"] += 1
                        print(f"  Updated: {grog_game.title}")
                    else:
                        stats["skipped"] += 1
                        print(f"  Skipped (exists): {grog_game.title}")
                else:
                    game = create_game_from_grog(grog_game, category.id)
                    session.add(game)
                    stats["created"] += 1
                    print(f"  Created: {grog_game.title}")

            except Exception as e:
                logger.error(f"Failed to import {grog_game.slug}: {e}")
                stats["failed"] += 1

        await session.commit()

    return stats


async def import_full(
    force: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
    letter: str | None = None,
) -> dict:
    """
    Import ALL games from GROG using browser client.

    Args:
        force: Update existing games
        dry_run: Don't save to database
        limit: Limit number of games to import
        letter: Only scan games starting with this letter

    Returns:
        Dict with import statistics
    """
    stats = {
        "total_fetched": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    # Determine which letters to scan
    if letter:
        letters = [letter.lower()]
    else:
        letters = list("abcdefghijklmnopqrstuvwxyz0")

    print(f"\nStep 1: Scanning GROG for game slugs (letters: {', '.join(letters)})...")
    print("This requires a headless browser and may take several minutes.\n")

    slugs = []

    def progress_callback(msg: str, current: int, total: int):
        print(f"  [{current}/{total}] {msg}")

    try:
        async with GrogBrowserClient(headless=True) as browser:
            slugs = await browser.list_all_game_slugs(
                callback=progress_callback,
                letters=letters,
            )
    except Exception as e:
        print(f"\nERROR: Browser client failed: {e}")
        print("Make sure Playwright browsers are installed: playwright install chromium")
        return stats

    print(f"\nFound {len(slugs)} unique game slugs")

    if limit:
        slugs = slugs[:limit]
        print(f"Limited to {len(slugs)} games")

    if dry_run:
        print("\n--- DRY RUN MODE ---")
        print(f"Would import {len(slugs)} games:")
        for slug in slugs[:30]:
            print(f"  - {slug}")
        if len(slugs) > 30:
            print(f"  ... and {len(slugs) - 30} more")
        stats["total_fetched"] = len(slugs)
        return stats

    print(f"\nStep 2: Fetching game details from GROG...")
    print(f"This will take approximately {len(slugs)} seconds ({len(slugs) // 60}min {len(slugs) % 60}s)\n")

    # Now import using the slugs
    return await import_from_slugs(
        slugs=slugs,
        force=force,
        dry_run=False,  # Already handled above
    )


def main():
    parser = argparse.ArgumentParser(
        description="Import RPG games from GROG database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update existing games"
    )
    parser.add_argument(
        "--from-fixtures",
        action="store_true",
        help="Import from fixtures/grog_top_100.json (default if no --slugs)"
    )
    parser.add_argument(
        "--from-curated",
        action="store_true",
        help="Import live from GROG using curated slugs list (fixtures/grog_curated_slugs.txt)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Import ALL games from GROG (uses browser, ~15-20 min)"
    )
    parser.add_argument(
        "--slugs",
        type=str,
        help="Comma-separated list of GROG slugs to import (fetches live)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without saving"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit import to N games"
    )
    parser.add_argument(
        "--letter",
        type=str,
        help="Only scan games starting with this letter (for --full mode)"
    )

    args = parser.parse_args()

    # Determine mode
    slugs = []
    if args.slugs:
        mode = "slugs"
        slugs = [s.strip() for s in args.slugs.split(",")]
    elif args.from_curated:
        mode = "curated"
        slugs = load_curated_slugs()
        if not slugs:
            print("ERROR: No curated slugs found!")
            sys.exit(1)
    elif args.full:
        mode = "full"
        # Slugs will be fetched via browser
    else:
        mode = "fixtures"

    print("=" * 60)
    print("GROG Game Import")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Force update: {args.force}")
    print(f"Dry run: {args.dry_run}")
    if args.limit:
        print(f"Limit: {args.limit}")
    if args.letter and mode == "full":
        print(f"Letter filter: {args.letter}")
    if mode == "slugs":
        print(f"Slugs: {slugs}")
    if mode == "curated":
        print(f"Curated slugs: {len(slugs)} games")
    if mode == "full":
        print("Will scan GROG website for all games (requires browser)")
    print("=" * 60)

    if mode == "slugs":
        stats = asyncio.run(import_from_slugs(
            slugs=slugs,
            force=args.force,
            dry_run=args.dry_run,
        ))
    elif mode == "curated":
        if args.limit:
            slugs = slugs[:args.limit]
        stats = asyncio.run(import_from_slugs(
            slugs=slugs,
            force=args.force,
            dry_run=args.dry_run,
        ))
    elif mode == "full":
        stats = asyncio.run(import_full(
            force=args.force,
            dry_run=args.dry_run,
            limit=args.limit,
            letter=args.letter,
        ))
    else:
        stats = asyncio.run(import_from_fixtures(
            force=args.force,
            dry_run=args.dry_run,
            limit=args.limit,
        ))

    print("\n" + "=" * 60)
    print("Import Statistics:")
    print(f"  Total fetched: {stats['total_fetched']}")
    print(f"  Created: {stats['created']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
