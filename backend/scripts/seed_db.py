import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.infrastructure.models import User, Exhibition

async def seed():
    async with AsyncSessionLocal() as session:
        # 1. Vérifier si on a déjà un admin pour éviter les doublons
        result = await session.execute(select(User).filter_by(email="admin@structura-ludis.com"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping...")
            return

        # 2. Créer un utilisateur Admin
        admin = User(
            id=uuid4(),
            email="admin@structura-ludis.com",
            full_name="Admin Structura",
        )
        session.add(admin)

        # 3. Créer ta première Exhibition
        exhibition = Exhibition(
            id=uuid4(),
            title="Structura Ludis Festival 2026",
            slug="sl-fest-2026",
            start_date=datetime.now() + timedelta(days=30),
            end_date=datetime.now() + timedelta(days=32),
            location_name="Palais des Congrès, Lyon",
            settings={"max_tables": 50, "allow_guest_registration": True}
        )
        session.add(exhibition)

        await session.commit()
        print("Successfully seeded: 1 Admin, 1 Exhibition.")

if __name__ == "__main__":
    asyncio.run(seed())
