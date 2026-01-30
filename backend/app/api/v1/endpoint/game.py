"""
Game API endpoints.

List, search, and create games and categories.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.game.entity import Game, GameCategory
from app.domain.game.schemas import (
    GameCategoryCreate,
    GameCategoryRead,
    GameCreate,
    GameRead,
)
from app.domain.user.entity import User
from app.api.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# Game Category Endpoints
# =============================================================================

@router.get("/categories", response_model=List[GameCategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    List all game categories.

    Returns categories sorted by name.
    """
    result = await db.execute(
        select(GameCategory).order_by(GameCategory.name)
    )
    return result.scalars().all()


@router.get("/categories/{category_id}", response_model=GameCategoryRead)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single category by ID."""
    result = await db.execute(
        select(GameCategory).where(GameCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.post("/categories", response_model=GameCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: GameCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new game category.

    Requires: ORGANIZER or SUPER_ADMIN role.
    """
    # Check for duplicate slug
    existing = await db.execute(
        select(GameCategory).where(GameCategory.slug == category_in.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists",
        )

    category = GameCategory(
        name=category_in.name,
        slug=category_in.slug,
        name_i18n=category_in.name_i18n,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)

    return category


# =============================================================================
# Game Endpoints
# =============================================================================

@router.get("/", response_model=List[GameRead])
async def list_games(
    q: Optional[str] = Query(None, min_length=1, description="Search query (title, publisher)"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Results offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    List/search games.

    Filters:
    - q: Search by title or publisher (case-insensitive)
    - category_id: Filter by game category

    Returns games sorted by title.
    """
    query = select(Game)

    # Apply search filter
    if q:
        search_pattern = f"%{q}%"
        query = query.where(
            or_(
                Game.title.ilike(search_pattern),
                Game.publisher.ilike(search_pattern),
            )
        )

    # Apply category filter
    if category_id:
        query = query.where(Game.category_id == category_id)

    # Order and paginate
    query = query.order_by(Game.title).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{game_id}", response_model=GameRead)
async def get_game(
    game_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single game by ID."""
    result = await db.execute(
        select(Game).where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    return game


@router.post("/", response_model=GameRead, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_in: GameCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new game.

    Requires authentication.
    Any authenticated user can create games (for inline creation in session form).
    """
    # Verify category exists
    category_result = await db.execute(
        select(GameCategory).where(GameCategory.id == game_in.category_id)
    )
    if not category_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )

    game = Game(
        category_id=game_in.category_id,
        title=game_in.title,
        external_provider_id=game_in.external_provider_id,
        publisher=game_in.publisher,
        description=game_in.description,
        complexity=game_in.complexity,
        min_players=game_in.min_players,
        max_players=game_in.max_players,
    )
    db.add(game)
    await db.flush()
    await db.refresh(game)

    return game
