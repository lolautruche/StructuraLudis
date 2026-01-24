# Structura Ludis

**Structura Ludis** is an advanced event management system for tabletop gaming (RPG, Board Games, TCG). It bridges the gap between digital planning and physical logistics by treating table space as a dynamic resource.

## 🎯 Functional Vision

Designed to eliminate "dead table time" and physical queues at large-scale festivals like *OctoGônes* or *Cannes*.

### Key Pillars
- **Physical Topology:** Map buildings, rooms, and numbered tables.
- **RPG & Multi-Game Focus:** Advanced GM workflows with Safety Tools, drafting mode, and catalog integration.
- **Partner Autonomy (Clubs & Publishers):** Dedicated dashboards for exhibitors to manage their own staff and physical tables independently.
- **Mobile-First Player Journey:** Discovery filters, digital waitlists, and mandatory check-ins to prevent no-shows.

---

## 🛠 Technical Stack

Built for reliability and asynchronous performance.

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2.
- **Database:** PostgreSQL 16 with Alembic migrations.
- **Architecture:** Clean Architecture / Domain-Driven Design (DDD).
- **Infrastructure:** Fully Dockerized with multi-stage builds.

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Poetry (for backend dependency management)

### Quick Start
1. **Clone the repo.**
2. **Setup environment:** Copy `.env` and adjust database credentials.
3. **Launch:** `docker-compose up -d`.
4. **Migrate & Seed:**
   ```bash
   cd backend
   poetry run alembic upgrade head
   poetry run python -m scripts.seed_db
