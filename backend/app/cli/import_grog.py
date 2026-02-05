"""
GROG Game Import CLI

Issue #55 - External Game Database Sync.

Import RPG games from Le GROG (Guide du Rôliste Galactique) into the database.

Usage:
    python -m app.cli.import_grog [--force] [--from-fixtures] [--slugs=x,y,z] [--dry-run]

Options:
    --force         Re-import all games (update existing)
    --from-fixtures Import games from fixtures/grog_top_100.json (default)
    --slugs=x,y,z   Import specific games by GROG slug (comma-separated)
    --dry-run       Show what would be imported without saving
    --limit=N       Limit import to N games (for testing)

Examples:
    # Import games from fixtures file (default, recommended)
    python -m app.cli.import_grog --from-fixtures

    # Import specific games by slug (fetches live from GROG)
    python -m app.cli.import_grog --slugs=appel-de-cthulhu,vampire-la-mascarade

    # Dry run to see what would be imported
    python -m app.cli.import_grog --from-fixtures --dry-run

    # Force update existing games
    python -m app.cli.import_grog --from-fixtures --force

Note: Full site scraping is not supported as GROG uses JavaScript filtering.
      Use --from-fixtures for bulk import or --slugs for specific games.
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
        help="Limit import to N games (for --from-fixtures only)"
    )

    args = parser.parse_args()

    # Determine mode
    if args.slugs:
        mode = "slugs"
        slugs = [s.strip() for s in args.slugs.split(",")]
    else:
        mode = "fixtures"

    print("=" * 60)
    print("GROG Game Import")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Force update: {args.force}")
    print(f"Dry run: {args.dry_run}")
    if args.limit and mode == "fixtures":
        print(f"Limit: {args.limit}")
    if mode == "slugs":
        print(f"Slugs: {slugs}")
    print("=" * 60)

    if mode == "slugs":
        stats = asyncio.run(import_from_slugs(
            slugs=slugs,
            force=args.force,
            dry_run=args.dry_run,
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
