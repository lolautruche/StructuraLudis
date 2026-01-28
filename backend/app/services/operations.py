"""
Operations service layer.

Contains business logic for real-time operations: available tables, auto-cancellation.
"""
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exhibition.entity import Exhibition, PhysicalTable, Zone
from app.domain.game.entity import GameSession
from app.domain.shared.entity import SessionStatus, PhysicalTableStatus


class OperationsService:
    """Service for real-time operations during an exhibition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_tables(
        self,
        exhibition_id: UUID,
        at_time: datetime = None,
    ) -> List[PhysicalTable]:
        """
        Get tables available for immediate use (pop-up games).

        A table is available if:
        - It belongs to the exhibition
        - Its status is AVAILABLE
        - No validated/in-progress session is using it at the given time
        """
        if at_time is None:
            at_time = datetime.now(timezone.utc)

        # Get all tables in the exhibition's zones
        tables_query = (
            select(PhysicalTable)
            .join(Zone, PhysicalTable.zone_id == Zone.id)
            .where(
                Zone.exhibition_id == exhibition_id,
                PhysicalTable.status == PhysicalTableStatus.AVAILABLE,
            )
        )
        tables_result = await self.db.execute(tables_query)
        all_tables = tables_result.scalars().all()

        # Get tables currently occupied by sessions
        occupied_query = (
            select(GameSession.physical_table_id)
            .where(
                GameSession.exhibition_id == exhibition_id,
                GameSession.physical_table_id.isnot(None),
                GameSession.status.in_([
                    SessionStatus.VALIDATED,
                    SessionStatus.IN_PROGRESS,
                ]),
                GameSession.scheduled_start <= at_time,
                GameSession.scheduled_end > at_time,
            )
        )
        occupied_result = await self.db.execute(occupied_query)
        occupied_table_ids = {row[0] for row in occupied_result.fetchall()}

        # Filter out occupied tables
        available_tables = [
            table for table in all_tables
            if table.id not in occupied_table_ids
        ]

        return available_tables

    async def get_sessions_to_cancel(
        self,
        exhibition_id: UUID,
        current_time: datetime = None,
    ) -> List[GameSession]:
        """
        Get sessions that should be auto-cancelled due to GM no-show.

        A session should be cancelled if:
        - Status is VALIDATED (not started yet)
        - scheduled_start + grace_period has passed
        - GM has not checked in (gm_checked_in_at is null)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Get exhibition's grace period
        exhibition_result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        exhibition = exhibition_result.scalar_one_or_none()

        if not exhibition:
            return []

        grace_period = timedelta(minutes=exhibition.grace_period_minutes)
        cutoff_time = current_time - grace_period

        # Find sessions past grace period without GM check-in
        query = select(GameSession).where(
            GameSession.exhibition_id == exhibition_id,
            GameSession.status == SessionStatus.VALIDATED,
            GameSession.scheduled_start <= cutoff_time,
            GameSession.gm_checked_in_at.is_(None),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def auto_cancel_sessions(
        self,
        exhibition_id: UUID,
        current_time: datetime = None,
    ) -> List[GameSession]:
        """
        Auto-cancel sessions where GM hasn't checked in after grace period.

        Returns list of cancelled sessions.
        """
        sessions = await self.get_sessions_to_cancel(exhibition_id, current_time)

        for session in sessions:
            session.status = SessionStatus.CANCELLED

        if sessions:
            await self.db.flush()
            for session in sessions:
                await self.db.refresh(session)

        return sessions

    async def gm_check_in(
        self,
        session_id: UUID,
        current_time: datetime = None,
    ) -> GameSession:
        """
        Check in the GM for a session.

        Transitions session to IN_PROGRESS status.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.gm_checked_in_at = current_time
        session.status = SessionStatus.IN_PROGRESS
        session.actual_start = current_time

        await self.db.flush()
        await self.db.refresh(session)

        return session