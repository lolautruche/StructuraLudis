"""
Development fixtures for Structura Ludis.

Creates a complete dataset for development and testing:
- Users: super admin, organizers, partner staff, GMs, players
- Organizations: main org + partner exhibitors
- User groups with memberships
- Game Categories and Games (RPGs from GROG + board games)
- Exhibition with zones, tables, time slots
- Game Sessions in various states with realistic player counts
- Bookings (confirmed, waitlist, checked-in)

Usage:
    # First time seeding
    docker compose exec sl-api python -m scripts.seed_db

    # Force reseed (drops and recreates data)
    docker compose exec sl-api python -m scripts.seed_db --force

    # Reset database completely and reseed
    docker compose exec sl-api alembic downgrade base
    docker compose exec sl-api alembic upgrade head
    docker compose exec sl-api python -m scripts.seed_db

Test accounts (password: password123):
    Super Admin:  admin@structura-ludis.dev
    Organizer:    organizer@fdj-lyon.com
    Partner:      contact@les12singes.com, contact@arkhane.com
    GMs:          gm1@example.com, gm2@example.com, gm3@example.com
    Players:      player1@example.com ... player12@example.com
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.domain.models import (
    User,
    Organization,
    UserGroup,
    Exhibition,
    TimeSlot,
    Zone,
    PhysicalTable,
    GameCategory,
    Game,
    GameSession,
    Booking,
)
from app.domain.user.entity import UserGroupMembership
from app.domain.shared.entity import (
    GlobalRole,
    UserGroupType,
    GroupRole,
    ExhibitionStatus,
    ZoneType,
    PhysicalTableStatus,
    GameComplexity,
    SessionStatus,
    ParticipantRole,
    BookingStatus,
)
from app.domain.exhibition.entity import SafetyTool as SafetyToolEntity


async def clear_data(session):
    """Clear all seeded data for fresh start."""
    print("Clearing existing data...")
    # Delete in reverse order of dependencies
    await session.execute(delete(Booking))
    await session.execute(delete(GameSession))
    await session.execute(delete(SafetyToolEntity))
    await session.execute(delete(TimeSlot))
    await session.execute(delete(PhysicalTable))
    await session.execute(delete(Zone))
    await session.execute(delete(Exhibition))
    await session.execute(delete(Game))
    await session.execute(delete(GameCategory))
    await session.execute(delete(UserGroupMembership))
    await session.execute(delete(UserGroup))
    await session.execute(delete(Organization))
    await session.execute(delete(User))
    await session.commit()


async def seed(force: bool = False):
    """Main seed function."""
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(
            select(User).filter_by(email="admin@structura-ludis.dev")
        )
        existing = result.scalar_one_or_none()

        if existing and not force:
            print("Database already seeded. Use --force to reseed.")
            return

        if existing and force:
            await clear_data(session)

        print("Seeding database...")

        # =====================================================================
        # 1. USERS
        # =====================================================================
        password_hash = get_password_hash("password123")

        # Super Admin
        admin = User(
            id=uuid4(),
            email="admin@structura-ludis.dev",
            hashed_password=password_hash,
            full_name="Admin Structura",
            global_role=GlobalRole.SUPER_ADMIN,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        # Main Organizer
        organizer = User(
            id=uuid4(),
            email="organizer@fdj-lyon.com",
            hashed_password=password_hash,
            full_name="Marie Dupont",
            global_role=GlobalRole.ORGANIZER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        # Partner staff (exhibitors)
        partner_12singes = User(
            id=uuid4(),
            email="contact@les12singes.com",
            hashed_password=password_hash,
            full_name="Laurent Bernasconi",
            global_role=GlobalRole.PARTNER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        partner_arkhane = User(
            id=uuid4(),
            email="contact@arkhane.com",
            hashed_password=password_hash,
            full_name="Julien Collas",
            global_role=GlobalRole.PARTNER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        # GMs (some affiliated with partners, some independent)
        gm1 = User(
            id=uuid4(),
            email="gm1@example.com",
            hashed_password=password_hash,
            full_name="Jean-Pierre Martin",
            global_role=GlobalRole.USER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        gm2 = User(
            id=uuid4(),
            email="gm2@example.com",
            hashed_password=password_hash,
            full_name="Sophie Leclerc",
            global_role=GlobalRole.USER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        gm3 = User(
            id=uuid4(),
            email="gm3@example.com",
            hashed_password=password_hash,
            full_name="Nicolas Flamel",
            global_role=GlobalRole.USER,
            locale="fr",
            privacy_accepted_at=datetime.now(timezone.utc),
        )

        # Players (12 players for realistic session filling)
        player_names = [
            "Alice Moreau", "Bob Petit", "Claire Dubois",
            "David Bernard", "Emma Leroy", "François Thomas",
            "Géraldine Roux", "Hugo Martinez", "Isabelle Chen",
            "Julien Nguyen", "Karine Schmitt", "Lucas Weber"
        ]
        players = [
            User(
                id=uuid4(),
                email=f"player{i}@example.com",
                hashed_password=password_hash,
                full_name=name,
                global_role=GlobalRole.USER,
                locale="fr",
                privacy_accepted_at=datetime.now(timezone.utc),
            )
            for i, name in enumerate(player_names, 1)
        ]

        all_users = [admin, organizer, partner_12singes, partner_arkhane, gm1, gm2, gm3] + players
        session.add_all(all_users)

        # =====================================================================
        # 2. ORGANIZATIONS & GROUPS
        # =====================================================================
        # Main festival organization
        org_fdj = Organization(
            id=uuid4(),
            name="Festival du Jeu Lyon",
            slug="fdj-lyon",
        )

        # Partner exhibitor organizations
        org_12singes = Organization(
            id=uuid4(),
            name="Les XII Singes",
            slug="les-12-singes",
        )

        org_arkhane = Organization(
            id=uuid4(),
            name="Arkhane Asylum Publishing",
            slug="arkhane-asylum",
        )

        session.add_all([org_fdj, org_12singes, org_arkhane])

        # User groups
        staff_fdj = UserGroup(
            id=uuid4(),
            organization_id=org_fdj.id,
            name="Staff FdJ",
            type=UserGroupType.STAFF,
        )

        club_jdr_lyon = UserGroup(
            id=uuid4(),
            organization_id=org_fdj.id,
            name="Club JDR Lyon",
            type=UserGroupType.ASSOCIATION,
        )

        team_12singes = UserGroup(
            id=uuid4(),
            organization_id=org_12singes.id,
            name="Équipe XII Singes",
            type=UserGroupType.EXHIBITOR,
        )

        team_arkhane = UserGroup(
            id=uuid4(),
            organization_id=org_arkhane.id,
            name="Équipe Arkhane",
            type=UserGroupType.EXHIBITOR,
        )

        session.add_all([staff_fdj, club_jdr_lyon, team_12singes, team_arkhane])

        # User group memberships
        memberships = [
            # Organizer is owner of staff group
            UserGroupMembership(
                id=uuid4(),
                user_id=organizer.id,
                user_group_id=staff_fdj.id,
                group_role=GroupRole.OWNER,
            ),
            # Partner 12 Singes owns their team
            UserGroupMembership(
                id=uuid4(),
                user_id=partner_12singes.id,
                user_group_id=team_12singes.id,
                group_role=GroupRole.OWNER,
            ),
            # Partner Arkhane owns their team
            UserGroupMembership(
                id=uuid4(),
                user_id=partner_arkhane.id,
                user_group_id=team_arkhane.id,
                group_role=GroupRole.OWNER,
            ),
            # GM1 and GM2 are members of Club JDR Lyon
            UserGroupMembership(
                id=uuid4(),
                user_id=gm1.id,
                user_group_id=club_jdr_lyon.id,
                group_role=GroupRole.MEMBER,
            ),
            UserGroupMembership(
                id=uuid4(),
                user_id=gm2.id,
                user_group_id=club_jdr_lyon.id,
                group_role=GroupRole.MEMBER,
            ),
            # GM3 is member of 12 Singes team (demo GM for publisher)
            UserGroupMembership(
                id=uuid4(),
                user_id=gm3.id,
                user_group_id=team_12singes.id,
                group_role=GroupRole.MEMBER,
            ),
        ]
        session.add_all(memberships)

        # =====================================================================
        # 3. GAME CATEGORIES
        # =====================================================================
        cat_rpg = GameCategory(
            id=uuid4(),
            name="Role-Playing Game",
            slug="rpg",
            name_i18n={"fr": "Jeu de rôle", "en": "Role-Playing Game"},
        )

        cat_board = GameCategory(
            id=uuid4(),
            name="Board Game",
            slug="board-game",
            name_i18n={"fr": "Jeu de plateau", "en": "Board Game"},
        )

        cat_card = GameCategory(
            id=uuid4(),
            name="Card Game",
            slug="card-game",
            name_i18n={"fr": "Jeu de cartes", "en": "Card Game"},
        )

        session.add_all([cat_rpg, cat_board, cat_card])

        # =====================================================================
        # 4. GAMES (RPGs from GROG + board games)
        # =====================================================================
        games = [
            # Classic RPGs
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="L'Appel de Cthulhu",
                external_provider_id="grog-4",
                publisher="Chaosium / Edge",
                description="Jeu d'horreur cosmique dans l'univers de H.P. Lovecraft",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=2,
                max_players=6,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Donjons et Dragons 5e",
                external_provider_id="grog-5",
                publisher="Wizards of the Coast / Gale Force 9",
                description="Le plus célèbre des jeux de rôle heroic fantasy",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=3,
                max_players=7,
            ),
            # French classics
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Pénombre",
                external_provider_id="grog-penombre",
                publisher="Les Vagabonds du Rêve",
                description="Enquêtes dans la France de l'entre-deux-guerres",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=2,
                max_players=5,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Maléfices",
                external_provider_id="grog-malefices",
                publisher="Arkhane Asylum Publishing",
                description="Horreur et fantastique dans la France de la Belle Époque",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=2,
                max_players=6,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Kult: Divinité Perdue",
                external_provider_id="grog-kult",
                publisher="Arkhane Asylum Publishing",
                description="Horreur gnostique contemporaine",
                complexity=GameComplexity.EXPERT,
                min_players=2,
                max_players=5,
            ),
            # Sci-Fi / Space Opera
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Star Wars : Aux Confins de l'Empire",
                external_provider_id="grog-sw-edge",
                publisher="Edge / Fantasy Flight Games",
                description="Aventures dans la galaxie Star Wars, côté contrebandiers",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=2,
                max_players=6,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Fading Suns",
                external_provider_id="grog-fadingsuns",
                publisher="Ulisses Spiele",
                description="Space opera mystique et politique dans un univers en déclin",
                complexity=GameComplexity.EXPERT,
                min_players=2,
                max_players=6,
            ),
            # 12 Singes games
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Cats ! La Mascarade",
                external_provider_id="grog-cats",
                publisher="Les XII Singes",
                description="Jouez des chats dans un monde de mystères félidés",
                complexity=GameComplexity.BEGINNER,
                min_players=2,
                max_players=6,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Wastburg",
                external_provider_id="grog-wastburg",
                publisher="Les XII Singes",
                description="Intrigues et enquêtes dans une cité médiévale fantastique",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=2,
                max_players=5,
            ),
            # Other RPGs
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Alien RPG",
                external_provider_id="grog-alien",
                publisher="Free League",
                description="Survival horror dans l'univers d'Alien",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=3,
                max_players=5,
            ),
            Game(
                id=uuid4(),
                category_id=cat_rpg.id,
                title="Chroniques Oubliées Fantasy",
                external_provider_id="grog-cof",
                publisher="Black Book Editions",
                description="JDR med-fan français accessible",
                complexity=GameComplexity.BEGINNER,
                min_players=2,
                max_players=6,
            ),
            # Board Games
            Game(
                id=uuid4(),
                category_id=cat_board.id,
                title="Wingspan",
                publisher="Stonemaier Games",
                description="Jeu de collection d'oiseaux",
                complexity=GameComplexity.INTERMEDIATE,
                min_players=1,
                max_players=5,
            ),
            Game(
                id=uuid4(),
                category_id=cat_board.id,
                title="Catan",
                publisher="Kosmos",
                description="Le classique des jeux de gestion",
                complexity=GameComplexity.BEGINNER,
                min_players=3,
                max_players=4,
            ),
        ]
        session.add_all(games)
        (cthulhu, dnd, penombre, malefices, kult, starwars, fadingsuns,
         cats, wastburg, alien, cof, wingspan, catan) = games

        # =====================================================================
        # 5. EXHIBITION
        # =====================================================================
        event_start = datetime.now(timezone.utc).replace(
            hour=9, minute=0, second=0, microsecond=0
        ) + timedelta(days=14)

        exhibition = Exhibition(
            id=uuid4(),
            organization_id=org_fdj.id,
            title="Festival du Jeu Lyon 2026",
            slug="fdj-lyon-2026",
            description="Le plus grand festival de jeux de la région lyonnaise",
            title_i18n={"fr": "Festival du Jeu Lyon 2026", "en": "Lyon Game Festival 2026"},
            start_date=event_start,
            end_date=event_start + timedelta(days=3),
            location_name="Eurexpo Lyon",
            city="Lyon",
            country_code="FR",
            timezone="Europe/Paris",
            grace_period_minutes=15,
            is_registration_open=True,
            primary_language="fr",
            secondary_languages=["en"],
            status=ExhibitionStatus.PUBLISHED,
        )
        session.add(exhibition)

        # =====================================================================
        # 6. SAFETY TOOLS
        # =====================================================================
        safety_tools = [
            SafetyToolEntity(
                id=uuid4(),
                exhibition_id=exhibition.id,
                name="X-Card",
                slug="x-card",
                description="Permet de signaler un malaise sans explication",
                is_required=False,
                display_order=1,
            ),
            SafetyToolEntity(
                id=uuid4(),
                exhibition_id=exhibition.id,
                name="Lines & Veils",
                slug="lines-veils",
                description="Définir les limites et ce qu'on suggère seulement",
                is_required=False,
                display_order=2,
            ),
            SafetyToolEntity(
                id=uuid4(),
                exhibition_id=exhibition.id,
                name="Script Change",
                slug="script-change",
                description="Pause, avance rapide, retour arrière",
                is_required=False,
                display_order=3,
            ),
        ]
        session.add_all(safety_tools)

        # =====================================================================
        # 7. ZONES & TABLES
        # =====================================================================
        zone_rpg = Zone(
            id=uuid4(),
            exhibition_id=exhibition.id,
            name="Espace JDR",
            name_i18n={"fr": "Espace JDR", "en": "RPG Area"},
            type=ZoneType.RPG,
            delegated_to_group_id=club_jdr_lyon.id,
        )

        zone_12singes = Zone(
            id=uuid4(),
            exhibition_id=exhibition.id,
            name="Stand XII Singes",
            name_i18n={"fr": "Stand XII Singes", "en": "XII Singes Booth"},
            type=ZoneType.RPG,
            delegated_to_group_id=team_12singes.id,
        )

        zone_board = Zone(
            id=uuid4(),
            exhibition_id=exhibition.id,
            name="Espace Jeux de Plateau",
            name_i18n={"fr": "Espace Jeux de Plateau", "en": "Board Game Area"},
            type=ZoneType.BOARD_GAME,
        )

        session.add_all([zone_rpg, zone_12singes, zone_board])

        # RPG Tables (8 in main area)
        rpg_tables = [
            PhysicalTable(
                id=uuid4(),
                zone_id=zone_rpg.id,
                label=f"JDR-{i}",
                capacity=6,
                status=PhysicalTableStatus.AVAILABLE,
            )
            for i in range(1, 9)
        ]

        # 12 Singes booth tables (3 demo tables)
        singes_tables = [
            PhysicalTable(
                id=uuid4(),
                zone_id=zone_12singes.id,
                label=f"12S-{i}",
                capacity=5,
                status=PhysicalTableStatus.AVAILABLE,
            )
            for i in range(1, 4)
        ]

        # Board Game Tables (12 tables)
        board_tables = [
            PhysicalTable(
                id=uuid4(),
                zone_id=zone_board.id,
                label=f"Plateau-{i}",
                capacity=6,
                status=PhysicalTableStatus.AVAILABLE,
            )
            for i in range(1, 13)
        ]

        session.add_all(rpg_tables + singes_tables + board_tables)

        # =====================================================================
        # 8. TIME SLOTS
        # =====================================================================
        time_slots = []
        for day_offset in range(3):
            day = event_start + timedelta(days=day_offset)
            day_name = ["Vendredi", "Samedi", "Dimanche"][day_offset]

            # Morning slot
            time_slots.append(TimeSlot(
                id=uuid4(),
                exhibition_id=exhibition.id,
                name=f"{day_name} Matin",
                start_time=day.replace(hour=10, minute=0),
                end_time=day.replace(hour=13, minute=0),
                max_duration_minutes=180,
                buffer_time_minutes=15,
            ))

            # Afternoon slot
            time_slots.append(TimeSlot(
                id=uuid4(),
                exhibition_id=exhibition.id,
                name=f"{day_name} Après-midi",
                start_time=day.replace(hour=14, minute=0),
                end_time=day.replace(hour=18, minute=0),
                max_duration_minutes=240,
                buffer_time_minutes=15,
            ))

            # Evening slot (except Sunday)
            if day_offset < 2:
                time_slots.append(TimeSlot(
                    id=uuid4(),
                    exhibition_id=exhibition.id,
                    name=f"{day_name} Soirée",
                    start_time=day.replace(hour=19, minute=0),
                    end_time=day.replace(hour=23, minute=0),
                    max_duration_minutes=240,
                    buffer_time_minutes=15,
                ))

        session.add_all(time_slots)

        # =====================================================================
        # 9. GAME SESSIONS (with realistic player distribution)
        # =====================================================================
        sessions_data = [
            # === VALIDATED - Various fill levels ===
            # Session 0: Cthulhu - 2 players (3 available)
            {
                "game": cthulhu,
                "gm": gm1,
                "title": "Les Masques de Nyarlathotep - Prologue",
                "time_slot_idx": 0,
                "table": rpg_tables[0],
                "status": SessionStatus.VALIDATED,
                "max_players": 5,
                "safety_tools": ["x-card", "lines-veils"],
                "min_age": 16,
                "language": "fr",
                "players": players[:2],  # Alice, Bob
            },
            # Session 1: D&D - FULL with waitlist
            {
                "game": dnd,
                "gm": gm2,
                "title": "La Malédiction de Strahd - Chapitre 1",
                "time_slot_idx": 1,
                "table": rpg_tables[1],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": ["x-card"],
                "min_age": 12,
                "language": "fr",
                "players": players[:4],  # Alice, Bob, Claire, David
                "waitlist": players[4:6],  # Emma, François
            },
            # Session 2: Alien - Almost full (4/5)
            {
                "game": alien,
                "gm": gm1,
                "title": "Chariot of the Gods",
                "time_slot_idx": 2,
                "table": rpg_tables[2],
                "status": SessionStatus.VALIDATED,
                "max_players": 5,
                "safety_tools": ["x-card", "lines-veils", "script-change"],
                "min_age": 16,
                "language": "en",
                "players": players[:4],  # Alice, Bob, Claire, David
            },
            # Session 3: COF - Beginner friendly, half full
            {
                "game": cof,
                "gm": gm2,
                "title": "Initiation : Le Donjon de Donjons",
                "time_slot_idx": 3,
                "table": rpg_tables[3],
                "status": SessionStatus.VALIDATED,
                "max_players": 6,
                "safety_tools": ["x-card"],
                "min_age": 10,
                "language": "fr",
                "is_accessible": True,
                "players": players[4:7],  # Emma, François, Géraldine
            },
            # Session 4: Pénombre - 3 players
            {
                "game": penombre,
                "gm": gm1,
                "title": "L'Affaire du Vampire de Düsseldorf",
                "time_slot_idx": 4,
                "table": rpg_tables[4],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": ["x-card", "lines-veils"],
                "min_age": 16,
                "language": "fr",
                "players": players[6:9],  # Géraldine, Hugo, Isabelle
            },
            # Session 5: Maléfices by Arkhane partner
            {
                "game": malefices,
                "gm": partner_arkhane,
                "title": "Le Fantôme de l'Opéra",
                "time_slot_idx": 5,
                "table": rpg_tables[5],
                "status": SessionStatus.VALIDATED,
                "max_players": 5,
                "safety_tools": ["x-card"],
                "min_age": 14,
                "language": "fr",
                "players": players[2:5],  # Claire, David, Emma
            },
            # Session 6: Kult - Mature, 2 players
            {
                "game": kult,
                "gm": gm1,
                "title": "Les Portes de l'Illusion",
                "time_slot_idx": 5,
                "table": rpg_tables[6],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": ["x-card", "lines-veils", "script-change"],
                "min_age": 18,
                "language": "fr",
                "players": players[8:10],  # Isabelle, Julien
            },
            # Session 7: Star Wars - Empty (just opened)
            {
                "game": starwars,
                "gm": gm2,
                "title": "Contrebande sur Tatooine",
                "time_slot_idx": 6,
                "table": rpg_tables[7],
                "status": SessionStatus.VALIDATED,
                "max_players": 5,
                "safety_tools": ["x-card"],
                "min_age": 12,
                "language": "fr",
                "players": [],
            },

            # === 12 SINGES BOOTH SESSIONS ===
            # Session 8: Cats - Family friendly, full
            {
                "game": cats,
                "gm": gm3,
                "title": "Les Mystères de la Ruelle",
                "time_slot_idx": 3,
                "table": singes_tables[0],
                "status": SessionStatus.VALIDATED,
                "max_players": 5,
                "safety_tools": [],
                "min_age": 8,
                "language": "fr",
                "is_accessible": True,
                "group": team_12singes,
                "players": players[:5],  # Full table
            },
            # Session 9: Wastburg
            {
                "game": wastburg,
                "gm": gm3,
                "title": "Intrigues au Quartier des Tanneurs",
                "time_slot_idx": 4,
                "table": singes_tables[1],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": ["x-card"],
                "min_age": 14,
                "language": "fr",
                "group": team_12singes,
                "players": players[5:8],  # François, Géraldine, Hugo
            },

            # === IN_PROGRESS SESSION ===
            # Session 10: In progress with checked-in players
            {
                "game": cthulhu,
                "gm": gm1,
                "title": "Campagne de l'horreur",
                "time_slot_idx": 0,
                "table": rpg_tables[0],
                "status": SessionStatus.IN_PROGRESS,
                "max_players": 4,
                "safety_tools": ["x-card"],
                "min_age": 16,
                "language": "fr",
                "players": players[8:12],  # 4 checked-in players
                "checked_in": True,
            },

            # === FINISHED SESSION ===
            {
                "game": dnd,
                "gm": gm2,
                "title": "One-shot terminé",
                "time_slot_idx": 0,
                "table": rpg_tables[1],
                "status": SessionStatus.FINISHED,
                "max_players": 5,
                "safety_tools": [],
                "min_age": 12,
                "language": "fr",
                "players": [],
            },

            # === CANCELLED SESSION ===
            {
                "game": alien,
                "gm": gm1,
                "title": "Session annulée",
                "time_slot_idx": 4,
                "table": rpg_tables[2],
                "status": SessionStatus.CANCELLED,
                "max_players": 5,
                "safety_tools": ["x-card"],
                "min_age": 16,
                "language": "fr",
                "players": [],
            },

            # === DRAFT SESSION ===
            {
                "game": fadingsuns,
                "gm": gm2,
                "title": "Brouillon en cours",
                "time_slot_idx": 7,
                "table": None,
                "status": SessionStatus.DRAFT,
                "max_players": 5,
                "safety_tools": ["x-card"],
                "min_age": 14,
                "language": "fr",
                "players": [],
            },

            # === BOARD GAME SESSIONS ===
            {
                "game": wingspan,
                "gm": organizer,
                "title": "Découverte Wingspan",
                "time_slot_idx": 3,
                "table": board_tables[0],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": [],
                "min_age": 10,
                "language": "fr",
                "players": players[0:3],  # Alice, Bob, Claire
            },
            {
                "game": catan,
                "gm": organizer,
                "title": "Tournoi Catan - Qualifications",
                "time_slot_idx": 4,
                "table": board_tables[1],
                "status": SessionStatus.VALIDATED,
                "max_players": 4,
                "safety_tools": [],
                "min_age": 8,
                "language": "fr",
                "players": players[3:6],  # David, Emma, François
                "waitlist": [players[6]],  # Géraldine on waitlist
            },
        ]

        game_sessions = []
        for data in sessions_data:
            ts = time_slots[data["time_slot_idx"]]
            gs = GameSession(
                id=uuid4(),
                exhibition_id=exhibition.id,
                time_slot_id=ts.id,
                game_id=data["game"].id,
                physical_table_id=data["table"].id if data["table"] else None,
                provided_by_group_id=data.get("group", club_jdr_lyon if data["game"].category_id == cat_rpg.id else None).id if data.get("group") or data["game"].category_id == cat_rpg.id else None,
                created_by_user_id=data["gm"].id,
                title=data["title"],
                description=f"Session de {data['game'].title}",
                language=data["language"],
                min_age=data["min_age"],
                max_players_count=data["max_players"],
                safety_tools=data["safety_tools"],
                is_accessible_disability=data.get("is_accessible", False),
                status=data["status"],
                scheduled_start=ts.start_time,
                scheduled_end=ts.start_time + timedelta(hours=3),
            )

            if data.get("checked_in"):
                gs.gm_checked_in_at = datetime.now(timezone.utc)
                gs.actual_start = datetime.now(timezone.utc)

            game_sessions.append(gs)
            session.add(gs)

            # Create bookings for players
            for player in data.get("players", []):
                status = BookingStatus.CHECKED_IN if data.get("checked_in") else BookingStatus.CONFIRMED
                session.add(Booking(
                    id=uuid4(),
                    game_session_id=gs.id,
                    user_id=player.id,
                    role=ParticipantRole.PLAYER,
                    status=status,
                    checked_in_at=datetime.now(timezone.utc) if data.get("checked_in") else None,
                ))

            # Create waitlist bookings
            for player in data.get("waitlist", []):
                session.add(Booking(
                    id=uuid4(),
                    game_session_id=gs.id,
                    user_id=player.id,
                    role=ParticipantRole.PLAYER,
                    status=BookingStatus.WAITING_LIST,
                ))

        await session.commit()

        # Summary
        print("=" * 60)
        print("Database seeded successfully!")
        print("=" * 60)
        print("\nTest accounts (password: password123):")
        print(f"  Super Admin:  admin@structura-ludis.dev")
        print(f"  Organizer:    organizer@fdj-lyon.com")
        print(f"  Partner:      contact@les12singes.com, contact@arkhane.com")
        print(f"  GMs:          gm1@example.com, gm2@example.com, gm3@example.com")
        print(f"  Players:      player1@example.com ... player12@example.com")
        print(f"\nExhibition: {exhibition.title}")
        print(f"  - {len(games)} games ({len([g for g in games if g.category_id == cat_rpg.id])} RPGs)")
        print(f"  - {len(game_sessions)} game sessions")
        print(f"  - {len(rpg_tables)} RPG tables + {len(singes_tables)} booth tables + {len(board_tables)} board game tables")
        print(f"  - {len(time_slots)} time slots")
        print("=" * 60)


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(seed(force=force))
