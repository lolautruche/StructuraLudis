# Structura Ludis

**Structura Ludis** is an advanced event management system for tabletop gaming (RPG, Board Games, TCG). It bridges the gap between digital planning and physical logistics by treating table space as a dynamic resource.

## Functional Vision

Designed to eliminate "dead table time" and physical queues at large-scale festivals like *OctoGônes* or *Cannes*.

### Key Pillars
- **Physical Topology:** Map buildings, rooms, and numbered tables.
- **RPG & Multi-Game Focus:** Advanced GM workflows with Safety Tools, drafting mode, and catalog integration.
- **Partner Autonomy (Clubs & Publishers):** Dedicated dashboards for exhibitors to manage their own staff and physical tables independently.
- **Mobile-First Player Journey:** Discovery filters, digital waitlists, and mandatory check-ins to prevent no-shows.

---

## Technical Stack

### Backend
- Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2
- PostgreSQL 16 with Alembic migrations
- Clean Architecture / Domain-Driven Design (DDD)
- JWT authentication

### Frontend
- Next.js 14 (App Router)
- TypeScript, Tailwind CSS
- next-intl for i18n (FR/EN)
- Jest + Testing Library

### Infrastructure
- Fully Dockerized with multi-stage builds
- Docker Compose for local development

---

## Getting Started

### Prerequisites
- Docker & Docker Compose

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/lolautruche/StructuraLudis.git
cd StructuraLudis

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec sl-api alembic upgrade head

# 5. Seed the database with fixtures
docker compose exec sl-api python -m scripts.seed_db
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## Development Fixtures

The seed script creates a complete dataset for development and testing:

### Test Accounts (password: `password123`)

| Role | Email |
|------|-------|
| Super Admin | admin@structura-ludis.dev |
| Organizer | organizer@fdj-lyon.com |
| Partner (XII Singes) | contact@les12singes.com |
| Partner (Arkhane) | contact@arkhane.com |
| GMs | gm1@example.com, gm2@example.com, gm3@example.com |
| Players | player1@example.com ... player12@example.com |

### Fixture Data
- **Organizations:** Festival du Jeu Lyon + 2 partner exhibitors
- **Games:** 13 games (11 RPGs from GROG + 2 board games)
- **Exhibition:** "Festival du Jeu Lyon 2026" with 3 zones, 23 tables, 8 time slots
- **Sessions:** 16 game sessions in various states (validated, in progress, finished, cancelled, draft)
- **Bookings:** Confirmed, waitlist, and checked-in bookings

### Fixture Commands

```bash
# First time seeding
docker compose exec sl-api python -m scripts.seed_db

# Force reseed (clears and recreates all data)
docker compose exec sl-api python -m scripts.seed_db --force

# Complete database reset
docker compose exec sl-api alembic downgrade base
docker compose exec sl-api alembic upgrade head
docker compose exec sl-api python -m scripts.seed_db
```

---

## Running Tests

### Backend
```bash
docker compose exec sl-api pytest
```

### Frontend
```bash
cd frontend
npm test
```

---

## Project Structure

```
StructuraLudis/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, security, database
│   │   ├── domain/           # DDD entities and business logic
│   │   └── infrastructure/   # External services
│   ├── scripts/              # CLI scripts (seed_db, etc.)
│   └── alembic/              # Database migrations
├── frontend/
│   ├── src/
│   │   ├── app/[locale]/     # Next.js pages with i18n
│   │   ├── components/       # React components
│   │   ├── lib/              # API client, utilities
│   │   └── contexts/         # React contexts (Auth, etc.)
│   └── messages/             # i18n translation files
├── doc/                      # Project documentation
│   └── PRD.md               # Product Requirements Document
└── docker-compose.yml
```

---

## Documentation

- [Product Requirements Document (PRD)](doc/PRD.md)
- [Project Context](doc/PROJECT-CONTEXT.md)
- [API Documentation](http://localhost:8000/docs) (when running)

---

## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

This means you are free to use, modify, and distribute this software, but if you run a modified version on a server that users interact with, you must make the source code available to them.

See [LICENSE](LICENSE) for details.

