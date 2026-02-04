"""
Exhibition service layer.

Contains business logic for exhibitions, zones, and physical tables.
Note: Time slots are now managed at zone level (Issue #105).
"""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exhibition.entity import Exhibition, TimeSlot, Zone, PhysicalTable, SafetyTool
from app.domain.exhibition.schemas import (
    ExhibitionCreate,
    ExhibitionDashboard,
    ZoneCreate,
    BatchTablesCreate,
    SessionStatusCount,
    SafetyToolCreate,
    SafetyToolBatchResponse,
)
from app.domain.game.entity import GameSession, Booking
from app.domain.organization.entity import Organization, UserGroup
from app.domain.user.entity import User, UserGroupMembership, UserExhibitionRole
from app.domain.shared.entity import (
    ExhibitionStatus,
    ExhibitionRole,
    GlobalRole,
    PhysicalTableStatus,
)


class ExhibitionService:
    """Service for exhibition-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Exhibition Operations
    # =========================================================================

    async def create_exhibition(
        self,
        data: ExhibitionCreate,
        current_user: User,
    ) -> Exhibition:
        """
        Create a new exhibition.

        Validates:
        - User belongs to the organization (or is SUPER_ADMIN/ADMIN)
        - Organization exists
        - Slug is unique
        - start_date < end_date (already validated in schema)

        Note: The creator will need to be assigned as ORGANIZER via UserExhibitionRole
        after the exhibition is created.
        """

        # Check organization exists
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == data.organization_id)
        )
        organization = org_result.scalar_one_or_none()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Check user belongs to organization (unless SUPER_ADMIN or ADMIN)
        if current_user.global_role not in [GlobalRole.SUPER_ADMIN, GlobalRole.ADMIN]:
            membership = await self.db.execute(
                select(UserGroupMembership)
                .join(UserGroupMembership.user_group)
                .where(
                    UserGroupMembership.user_id == current_user.id,
                    UserGroupMembership.user_group.has(
                        organization_id=data.organization_id
                    ),
                )
            )
            if not membership.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You must be a member of the organization to create exhibitions",
                )

        # Check slug uniqueness
        existing = await self.db.execute(
            select(Exhibition).where(Exhibition.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exhibition with slug '{data.slug}' already exists",
            )

        # Create exhibition with default settings
        default_settings = {
            "language": "en",
            "registration_open": False,
            "allow_waitlist": True,
        }

        exhibition = Exhibition(
            **data.model_dump(),
            created_by_id=current_user.id,  # Track creator (#99)
            settings=default_settings,
            status=ExhibitionStatus.DRAFT,
        )
        self.db.add(exhibition)
        await self.db.flush()

        # Automatically assign creator as ORGANIZER of this exhibition (#99)
        # Always assign, regardless of global_role (even admins get explicit role)
        organizer_role = UserExhibitionRole(
            user_id=current_user.id,
            exhibition_id=exhibition.id,
            role=ExhibitionRole.ORGANIZER,
        )
        self.db.add(organizer_role)
        await self.db.flush()

        await self.db.refresh(exhibition)

        return exhibition

    # =========================================================================
    # Zone Operations
    # =========================================================================

    async def create_zone(
        self,
        data: ZoneCreate,
        current_user: User,
    ) -> Zone:
        """
        Create a zone for an exhibition.

        Validates:
        - Exhibition exists
        - User can manage the exhibition
        - If delegated_to_group_id is set, the group exists and belongs to the org
        """
        # Get exhibition
        result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == data.exhibition_id)
        )
        exhibition = result.scalar_one_or_none()
        if not exhibition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )

        # Validate delegation group if provided
        if data.delegated_to_group_id:
            group_result = await self.db.execute(
                select(UserGroup).where(
                    UserGroup.id == data.delegated_to_group_id,
                    UserGroup.organization_id == exhibition.organization_id,
                )
            )
            if not group_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Delegated group must belong to the exhibition's organization",
                )

        zone = Zone(**data.model_dump())
        self.db.add(zone)
        await self.db.flush()
        await self.db.refresh(zone)

        return zone

    # =========================================================================
    # PhysicalTable Operations
    # =========================================================================

    async def batch_create_tables(
        self,
        zone_id: UUID,
        data: BatchTablesCreate,
    ) -> List[PhysicalTable]:
        """
        Batch create physical tables in a zone (Issue #93).

        Features:
        - Uses zone's table_prefix if no prefix provided
        - Auto-calculates starting_number from existing tables if not provided
        - fill_gaps option: fill gaps in existing numbering before continuing

        Validates:
        - Zone exists
        - Generated labels are unique within the zone
        """
        import re

        # Get zone
        result = await self.db.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        zone = result.scalar_one_or_none()
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zone not found",
            )

        # Determine prefix: request > zone > default
        prefix = data.prefix or zone.table_prefix or "Table "

        # Get existing labels in zone
        existing_labels = await self.db.execute(
            select(PhysicalTable.label).where(PhysicalTable.zone_id == zone_id)
        )
        existing_set = {row[0] for row in existing_labels.fetchall()}

        # Extract existing numbers for this prefix
        # Match labels like "JDR-1", "JDR-2", "Table 1", etc.
        prefix_pattern = re.escape(prefix)
        number_pattern = re.compile(rf"^{prefix_pattern}(\d+)$")
        existing_numbers = set()
        for label in existing_set:
            match = number_pattern.match(label)
            if match:
                existing_numbers.add(int(match.group(1)))

        # Determine numbers to use
        numbers_to_create = []

        if data.fill_gaps and existing_numbers:
            # Find gaps in the sequence
            max_existing = max(existing_numbers)
            all_possible = set(range(1, max_existing + 1))
            gaps = sorted(all_possible - existing_numbers)

            # Use gaps first
            numbers_to_create.extend(gaps[:data.count])

            # If we need more, continue from max + 1
            remaining = data.count - len(numbers_to_create)
            if remaining > 0:
                next_num = max_existing + 1
                for _ in range(remaining):
                    numbers_to_create.append(next_num)
                    next_num += 1
        else:
            # Sequential numbering
            if data.starting_number is not None:
                start = data.starting_number
            elif existing_numbers:
                start = max(existing_numbers) + 1
            else:
                start = 1

            numbers_to_create = list(range(start, start + data.count))

        # Generate new tables
        tables = []
        for num in numbers_to_create:
            label = f"{prefix}{num}"

            if label in existing_set:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Table with label '{label}' already exists in this zone",
                )

            table = PhysicalTable(
                zone_id=zone_id,
                label=label,
                capacity=data.capacity,
                status=PhysicalTableStatus.AVAILABLE,
            )
            self.db.add(table)
            tables.append(table)
            existing_set.add(label)

        await self.db.flush()
        for table in tables:
            await self.db.refresh(table)

        return tables

    # =========================================================================
    # Dashboard Operations
    # =========================================================================

    async def get_exhibition_dashboard(
        self,
        exhibition_id: UUID,
    ) -> ExhibitionDashboard:
        """
        Get dashboard statistics for an exhibition.

        Returns:
        - Zone and table counts
        - Table occupation rates
        - Session counts by status
        - Total bookings
        """
        # Get exhibition
        result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        exhibition = result.scalar_one_or_none()
        if not exhibition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )

        # Count zones
        zones_count = await self.db.execute(
            select(func.count(Zone.id)).where(Zone.exhibition_id == exhibition_id)
        )
        total_zones = zones_count.scalar() or 0

        # Count tables by status
        tables_query = await self.db.execute(
            select(
                PhysicalTable.status,
                func.count(PhysicalTable.id),
            )
            .join(Zone, PhysicalTable.zone_id == Zone.id)
            .where(Zone.exhibition_id == exhibition_id)
            .group_by(PhysicalTable.status)
        )
        tables_by_status = {row[0]: row[1] for row in tables_query.fetchall()}

        total_tables = sum(tables_by_status.values())
        tables_available = tables_by_status.get(PhysicalTableStatus.AVAILABLE, 0)
        tables_occupied = tables_by_status.get(PhysicalTableStatus.OCCUPIED, 0)
        occupation_rate = (tables_occupied / total_tables * 100) if total_tables > 0 else 0.0

        # Count sessions by status
        sessions_query = await self.db.execute(
            select(
                GameSession.status,
                func.count(GameSession.id),
            )
            .where(GameSession.exhibition_id == exhibition_id)
            .group_by(GameSession.status)
        )
        sessions_by_status = [
            SessionStatusCount(status=str(row[0]), count=row[1])
            for row in sessions_query.fetchall()
        ]
        total_sessions = sum(s.count for s in sessions_by_status)

        # Count bookings
        bookings_count = await self.db.execute(
            select(func.count(Booking.id))
            .join(GameSession, Booking.game_session_id == GameSession.id)
            .where(GameSession.exhibition_id == exhibition_id)
        )
        total_bookings = bookings_count.scalar() or 0

        return ExhibitionDashboard(
            exhibition_id=exhibition_id,
            total_zones=total_zones,
            total_tables=total_tables,
            tables_available=tables_available,
            tables_occupied=tables_occupied,
            occupation_rate=round(occupation_rate, 2),
            sessions_by_status=sessions_by_status,
            total_sessions=total_sessions,
            total_bookings=total_bookings,
        )

    # =========================================================================
    # SafetyTool Operations (JS.A5)
    # =========================================================================

    # Default safety tools to create
    DEFAULT_SAFETY_TOOLS = [
        {
            "name": "X-Card",
            "slug": "x-card",
            "description": "A card that can be tapped to skip uncomfortable content without explanation.",
            "url": "https://docs.google.com/document/d/1SB0jsx34bWHZWbnNIVVuMjhDkrdFGo1_hSC2BWPlI3A/",
            "display_order": 1,
        },
        {
            "name": "Lines & Veils",
            "slug": "lines-and-veils",
            "description": "Lines are hard limits (never in game), Veils are fade-to-black (implied but not detailed).",
            "url": "https://rpg.stackexchange.com/questions/30906/what-do-the-terms-lines-and-veils-mean",
            "display_order": 2,
        },
        {
            "name": "Script Change",
            "slug": "script-change",
            "description": "Rewind, fast-forward, or pause scenes like controlling a movie.",
            "url": "https://briebeau.com/thoughty/script-change/",
            "display_order": 3,
        },
        {
            "name": "Open Door Policy",
            "slug": "open-door",
            "description": "Players can leave the table at any time without needing to explain.",
            "display_order": 4,
        },
        {
            "name": "Stars & Wishes",
            "slug": "stars-and-wishes",
            "description": "End-of-session feedback: stars (what was great) and wishes (what to improve).",
            "display_order": 5,
        },
        {
            "name": "Session Zero",
            "slug": "session-zero",
            "description": "Pre-game session to discuss expectations, boundaries, and character creation.",
            "display_order": 6,
        },
    ]

    async def create_safety_tool(
        self,
        exhibition_id: UUID,
        data: SafetyToolCreate,
    ) -> SafetyTool:
        """
        Create a safety tool for an exhibition.

        Validates:
        - Exhibition exists
        - Slug is unique within the exhibition
        """
        # Get exhibition
        result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        exhibition = result.scalar_one_or_none()
        if not exhibition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )

        # Check slug uniqueness within exhibition
        existing = await self.db.execute(
            select(SafetyTool).where(
                SafetyTool.exhibition_id == exhibition_id,
                SafetyTool.slug == data.slug,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Safety tool with slug '{data.slug}' already exists for this exhibition",
            )

        tool = SafetyTool(
            exhibition_id=exhibition_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            url=data.url,
            is_required=data.is_required,
            display_order=data.display_order,
        )
        self.db.add(tool)
        await self.db.flush()
        await self.db.refresh(tool)

        return tool

    async def create_default_safety_tools(
        self,
        exhibition_id: UUID,
    ) -> SafetyToolBatchResponse:
        """
        Create default safety tools for an exhibition.

        Skips tools that already exist (by slug).
        """
        # Get exhibition
        result = await self.db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        exhibition = result.scalar_one_or_none()
        if not exhibition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )

        # Get existing slugs
        existing_slugs = await self.db.execute(
            select(SafetyTool.slug).where(SafetyTool.exhibition_id == exhibition_id)
        )
        existing_set = {row[0] for row in existing_slugs.fetchall()}

        # Create tools that don't exist
        tools = []
        for tool_data in self.DEFAULT_SAFETY_TOOLS:
            if tool_data["slug"] not in existing_set:
                tool = SafetyTool(
                    exhibition_id=exhibition_id,
                    **tool_data,
                )
                self.db.add(tool)
                tools.append(tool)

        await self.db.flush()
        for tool in tools:
            await self.db.refresh(tool)

        return SafetyToolBatchResponse(
            created_count=len(tools),
            tools=tools,
        )
