"""
Exhibition API endpoints.

Similar to a Symfony Controller, but using FastAPI's router pattern.

CRUD operations:
- GET    /                  → list_exhibitions (index)
- POST   /                  → create_exhibition (store)
- GET    /{exhibition_id}   → get_exhibition (show)
- PUT    /{exhibition_id}   → update_exhibition (update)
- DELETE /{exhibition_id}   → delete_exhibition (destroy)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition import Exhibition
from app.domain.exhibition.schemas import (
    ExhibitionCreate,
    ExhibitionRead,
    ExhibitionUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[ExhibitionRead])
async def list_exhibitions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all exhibitions with pagination.

    Similar to: ExhibitionController::index() in Symfony.
    """
    query = select(Exhibition).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ExhibitionRead, status_code=status.HTTP_201_CREATED)
async def create_exhibition(
    exhibition_in: ExhibitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new exhibition.

    Similar to: ExhibitionController::store() in Symfony.
    The request body is validated by Pydantic (like Symfony Forms).
    """
    # Check if slug already exists (unique constraint)
    existing = await db.execute(
        select(Exhibition).where(Exhibition.slug == exhibition_in.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Exhibition with slug '{exhibition_in.slug}' already exists",
        )

    # Create entity from validated data
    # model_dump() is like $form->getData() in Symfony
    exhibition = Exhibition(**exhibition_in.model_dump())
    db.add(exhibition)
    await db.flush()  # Get the ID without committing (commit is done by get_db)
    await db.refresh(exhibition)  # Reload to get server defaults (created_at, etc.)

    return exhibition


@router.get("/{exhibition_id}", response_model=ExhibitionRead)
async def get_exhibition(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single exhibition by ID.

    Similar to: ExhibitionController::show() with ParamConverter in Symfony.
    """
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    return exhibition


@router.put("/{exhibition_id}", response_model=ExhibitionRead)
async def update_exhibition(
    exhibition_id: UUID,
    exhibition_in: ExhibitionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing exhibition.

    Similar to: ExhibitionController::update() in Symfony.
    Only provided fields are updated (PATCH-like behavior).
    """
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    # Update only provided fields (exclude_unset=True)
    # Similar to $form->submit($data, false) in Symfony
    update_data = exhibition_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exhibition, field, value)

    await db.flush()
    await db.refresh(exhibition)

    return exhibition


@router.delete("/{exhibition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exhibition(
    exhibition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an exhibition.

    Similar to: ExhibitionController::destroy() in Symfony.
    Returns 204 No Content on success.
    """
    result = await db.execute(
        select(Exhibition).where(Exhibition.id == exhibition_id)
    )
    exhibition = result.scalar_one_or_none()

    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exhibition not found",
        )

    await db.delete(exhibition)
    # No return for 204
