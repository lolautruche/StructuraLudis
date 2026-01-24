"""
Exhibition API endpoints.

Similar to a Symfony Controller, but using FastAPI's router pattern.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.exhibition import Exhibition
from app.domain.exhibition.schemas import ExhibitionRead

router = APIRouter()


@router.get("/", response_model=List[ExhibitionRead])
async def list_exhibitions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all exhibitions.

    Similar to a Symfony controller action with Doctrine repository.
    """
    query = select(Exhibition).offset(skip).limit(limit)
    result = await db.execute(query)
    exhibitions = result.scalars().all()
    return exhibitions