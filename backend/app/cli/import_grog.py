"""
GROG Game Import CLI

Issue #55 - External Game Database Sync.

Import RPG games from Le GROG (Guide du Rôliste Galactique) into the database.

Usage:
    python -m app.cli.import_grog [--force] [--letter=X] [--dry-run]

Options:
    --force     Re-import all games (update existing)
    --letter=X  Import only games starting with letter X (a-z or 0)
    --dry-run   Show what would be imported without saving
    --limit=N   Limit import to N games (for testing)

Examples:
    # Import all games
    python -m app.cli.import_grog

    # Import only games starting with 'a'
    python -m app.cli.import_grog --letter=a

    # Dry run to see what would be imported
    python -m app.cli.import_grog --dry-run --letter=a

    # Force update existing games
    python -m app.cli.import_grog --force
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
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


async def game_exists(session, slug: str) -> bool:
    """Check if a game with the given GROG slug already exists."""
    result = await session.execute(
        select(Game).filter_by(
            external_provider="grog",
            external_provider_id=slug
        )
    )
    return result.scalar_one_or_none() is not None


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


def update_game_from_grog(game: Game, grog_game: GrogGame) -> None:
    """Update an existing Game entity with fresh GROG data."""
    game.title = grog_game.title
    game.external_url = grog_game.url
    game.publisher = grog_game.publisher
    game.description = grog_game.description
    game.cover_image_url = grog_game.cover_image_url
    game.themes = grog_game.themes if grog_game.themes else None
    game.last_synced_at = datetime.now(timezone.utc)


def progress_callback(message: str, current: int, total: int) -> None:
    """Print progress to console."""
    if total > 0:
        percent = (current / total) * 100
        print(f"\r[{percent:5.1f}%] {message}", end="", flush=True)
    else:
        print(f"\r{message}", end="", flush=True)


async def import_games(
    force: bool = False,
    letters: list[str] | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """
    Import games from GROG.

    Args:
        force: Update existing games
        letters: Optional list of letters to import
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

    client = GrogClient()

    # Fetch games from GROG
    print("Fetching games from GROG...")
    grog_games = await client.import_all_games(
        callback=progress_callback,
        letters=letters,
    )
    print()  # New line after progress

    stats["total_fetched"] = len(grog_games)
    logger.info(f"Fetched {len(grog_games)} games from GROG")

    if limit:
        grog_games = grog_games[:limit]
        logger.info(f"Limited to {limit} games")

    if dry_run:
        print("\n--- DRY RUN MODE ---")
        for game in grog_games[:20]:  # Show first 20
            print(f"  - {game.title} ({game.slug})")
            if game.publisher:
                print(f"    Publisher: {game.publisher}")
            if game.themes:
                print(f"    Themes: {', '.join(game.themes)}")
        if len(grog_games) > 20:
            print(f"  ... and {len(grog_games) - 20} more")
        return stats

    # Import to database
    async with AsyncSessionLocal() as session:
        category = await get_or_create_rpg_category(session)

        print(f"\nImporting {len(grog_games)} games to database...")
        for i, grog_game in enumerate(grog_games):
            try:
                existing = await get_existing_game(session, grog_game.slug)

                if existing:
                    if force:
                        update_game_from_grog(existing, grog_game)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    game = create_game_from_grog(grog_game, category.id)
                    session.add(game)
                    stats["created"] += 1

                if (i + 1) % 50 == 0:
                    await session.commit()
                    print(f"  Progress: {i + 1}/{len(grog_games)}")

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
        "--letter",
        type=str,
        help="Import only games starting with this letter (a-z or 0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without saving"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit import to N games (for testing)"
    )

    args = parser.parse_args()

    letters = None
    if args.letter:
        letter = args.letter.lower()
        if letter not in "abcdefghijklmnopqrstuvwxyz0":
            print(f"Error: Invalid letter '{args.letter}'. Use a-z or 0.")
            sys.exit(1)
        letters = [letter]

    print("=" * 60)
    print("GROG Game Import")
    print("=" * 60)
    print(f"Options:")
    print(f"  Force update: {args.force}")
    print(f"  Letters: {letters or 'all'}")
    print(f"  Dry run: {args.dry_run}")
    if args.limit:
        print(f"  Limit: {args.limit}")
    print("=" * 60)

    stats = asyncio.run(import_games(
        force=args.force,
        letters=letters,
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
