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
| Session Workflow | `backend/doc/session-workflow.md` | Session approval flows, zone settings |
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

---

## Notification System (#37)

### Notification Types

| Type | Trigger | Channels | Priority |
|------|---------|----------|----------|
| `booking_confirmed` | User books a session | Email, In-App | Normal |
| `booking_cancelled` | Booking is cancelled | Email, In-App | Normal |
| `session_cancelled` | GM/Organizer cancels session | Email, In-App, Push | High |
| `waitlist_promoted` | User promoted from waitlist | Email, In-App, Push | High |
| `session_reminder` | X minutes before session | Email, Push | Normal |
| `moderation_comment` | New comment in moderation thread | In-App | Normal |
| `session_approved` | Session approved by moderator | Email, In-App | Normal |
| `session_rejected` | Session rejected by moderator | Email, In-App | High |
| `changes_requested` | Moderator requests changes | Email, In-App | Normal |

### Notification Channels

| Channel | Backend | Use Case |
|---------|---------|----------|
| Email | SMTP, SendGrid, Gmail API | Transactional emails |
| Push | Firebase Cloud Messaging | Mobile app notifications |
| In-App | Database (Notification entity) | Web app notifications |

### Email Backends

| Backend | Environment | Configuration |
|---------|-------------|---------------|
| `console` | Development/Testing | Logs emails to console |
| `smtp` | Dev/Staging | Mailpit (docker), or any SMTP server |
| `sendgrid` | **Production (recommended)** | `SENDGRID_API_KEY` |
| `gmail` | Small scale | OAuth2 credentials |

### Development Setup

```bash
# Start Mailpit for local email testing
docker compose up sl-mail

# Access Mailpit UI
open http://localhost:8025

# Configure backend
EMAIL_BACKEND=smtp
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Production Setup (SendGrid)

```bash
# Environment variables
EMAIL_BACKEND=sendgrid
EMAIL_ENABLED=true
SENDGRID_API_KEY=SG.xxx
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

### Gmail API Setup (Small Scale)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials.json

```bash
# Install dependencies
poetry add google-api-python-client google-auth-httplib2 google-auth-oauthlib
# Or with pip: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Environment variables
EMAIL_BACKEND=gmail
EMAIL_ENABLED=true
GMAIL_CREDENTIALS_FILE=/path/to/credentials.json
GMAIL_TOKEN_FILE=/path/to/token.json  # Auto-generated on first run
```

Note: Gmail has quotas (500 emails/day for free accounts). For production, prefer SendGrid.

### i18n Support

Email templates support FR/EN localization:
- Templates: `app/templates/email/*.html`
- Translations: `app/core/templates.py` (EMAIL_STRINGS dict)
- User locale from `User.locale` or `Accept-Language` header
