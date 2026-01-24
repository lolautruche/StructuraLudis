# Structura Ludis - Project Context

## Overview

**Structura Ludis** is an open-source platform for managing tabletop gaming tables (RPG, Board Games, Wargames, TCG) at conventions, festivals, and gaming clubs.

### Core Vision
Eliminate logistical friction between digital planning and physical reality, ensuring every seat at every table is optimized, respected, and accessible.

### Problems Solved
- **Dead table time**: Dynamic rotation management for large-scale events
- **Static queue fatigue**: Virtual waitlists replace physical queues
- **Rigid permission silos**: Delegated autonomy for publishers/clubs with organizer oversight
- **Ghost participants**: Check-in/check-out accountability

---

## Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| PRD (Requirements) | `doc/PRD.md` | Job stories, epics, business rules |
| Database Schema | `backend/doc/database-schema.mmd` | ERD visualization |
| AI Instructions | `AGENTS.md` | Coding standards, invariants |

---

## Functional Epics (from PRD)

### EPIC A: Organizer's Setup
- Physical topology (Building > Floor > Room > Table)
- Flexible TimeSlots with max duration per period
- Buffer times between sessions
- Delegated autonomy to partners
- Safety tools library (X-Card, Lines & Veils...)
- No-show & reallocation policy

### EPIC B: Proposer's Journey (GM)
- Asynchronous session drafting
- Dynamic slotting within period limits
- Game identity via external reference (GROG) or manual
- Safety tools commitment
- Moderation workflow / dialogue
- No-show declaration

### EPIC C: Player's Experience
- Discovery & filtering (game type, style, accessibility)
- Safe booking with age/safety info
- Smart check-in with reminders
- Virtual waitlist
- Pop-up games from released seats

### EPIC D: Partner Management
- Space autonomy for publishers/clubs
- Team management (invite GMs)
- Delegated moderation
- Partner branding visibility

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2 |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 |
| Queue | RabbitMQ |
| Infra | Docker Compose, Kubernetes-ready |

---

## Architecture: Clean Architecture / DDD

```
backend/app/
├── main.py                 # FastAPI entry point
├── core/
│   ├── config.py           # Settings (env vars)
│   └── database.py         # DB engine, session
├── domain/
│   ├── shared/             # Base, mixins, enums
│   ├── organization/       # Organization, UserGroup
│   ├── user/               # User, Membership
│   ├── exhibition/         # Exhibition, TimeSlot
│   ├── game/               # Game, GameTable, Participant
│   └── media/              # Media, AuditLog
└── api/
    └── v1/endpoints/       # REST controllers
```

### Symfony Analogies

| Symfony | Python/FastAPI |
|---------|----------------|
| Kernel | `main.py` (FastAPI app) |
| Controller | Router endpoint |
| services.yaml | `Depends()` injection |
| Doctrine Entity | SQLAlchemy Model |
| Doctrine Repository | SQLAlchemy queries |
| DTO / Form | Pydantic Schema |
| Gedmo Timestampable | `TimestampMixin` |
| Voters | Permission checks in dependencies |

---

## Business Invariants

1. **No Schedule Conflicts**: User's schedule must be conflict-free within an Exhibition
2. **Ownership**: Every GameTable must be linked to a UserGroup
3. **Approval**: Only MODERATOR/ADMIN of a UserGroup can approve a GameTable
4. **Age Policy**: Registration requires User.age >= GameTable.min_age
5. **External Sync**: Prioritize `external_id` for Game entities (GROG)
6. **Timezone**: All dates stored in UTC

---

## Developer Context

**Profile**: Senior PHP/Symfony developer learning Python

**Preferences**:
- Discussions in French, code in English
- Docker-first approach
- Explain Python idioms with Symfony analogies

**Target Deployment**: Synology NAS (Container Manager) → Kubernetes
