# Roadmap & Priorities

This document tracks prioritization decisions and project progress.
**Last updated**: 2026-02-01

---

## Current Priorities

### Next Up (MVP)

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#62](https://github.com/lolautruche/StructuraLudis/issues/62) | Notification Center & Bell | JS.C2, JS.C3 | In-app notifications |
| [#8](https://github.com/lolautruche/StructuraLudis/issues/8) | Proposer: Session Submission Form | JS.B1-B5 | Submission form (partially done) |
| [#7](https://github.com/lolautruche/StructuraLudis/issues/7) | Admin: Event Configuration | JS.A2, JS.A3, JS.A5 | Slots/zones admin config |

### Post-MVP

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#74](https://github.com/lolautruche/StructuraLudis/issues/74) | Magic link authentication | JS.X1 variant | Passwordless login |
| [#75](https://github.com/lolautruche/StructuraLudis/issues/75) | Persist theme preference | JS.X2 | Theme preference in DB |
| [#70](https://github.com/lolautruche/StructuraLudis/issues/70) | Waitlist configuration | JS.A9 | Waitlist config per event |
| [#55](https://github.com/lolautruche/StructuraLudis/issues/55) | External Game Database Sync | JS.05 | GROG/BGG import |
| [#56](https://github.com/lolautruche/StructuraLudis/issues/56) | Game Autocomplete & Metadata | JS.B3, JS.B9 | Enrich game metadata |
| [#13](https://github.com/lolautruche/StructuraLudis/issues/13) | SuperAdmin Portal | JS.01-04 | Global admin |
| [#10](https://github.com/lolautruche/StructuraLudis/issues/10) | Partner Zone Management | JS.D1 | Partner zone management |

### GDPR (to be planned)

| Issue | Title | Job Stories |
|-------|-------|-------------|
| [#48](https://github.com/lolautruche/StructuraLudis/issues/48) | Data Access (Right of Access) | JS.E2 |
| [#49](https://github.com/lolautruche/StructuraLudis/issues/49) | Account Deletion | JS.E3 |
| [#50](https://github.com/lolautruche/StructuraLudis/issues/50) | Data Portability | JS.E4 |
| [#51](https://github.com/lolautruche/StructuraLudis/issues/51) | Consent Management | JS.E5 |
| [#52](https://github.com/lolautruche/StructuraLudis/issues/52) | Data Retention Transparency | JS.E6 |
| [#53](https://github.com/lolautruche/StructuraLudis/issues/53) | GDPR Request Management | JS.E7 |
| [#54](https://github.com/lolautruche/StructuraLudis/issues/54) | Data Anonymization | JS.E8 |

---

## Recently Completed

| Issue | Title | Job Stories | Date |
|-------|-------|-------------|------|
| [#60](https://github.com/lolautruche/StructuraLudis/issues/60) | User Settings & Profile Page | JS.X2, JS.E2, JS.E5 | 2026-02-01 |
| [#73](https://github.com/lolautruche/StructuraLudis/issues/73) | Email verification on registration | JS.E1 | 2026-01-31 |
| [#61](https://github.com/lolautruche/StructuraLudis/issues/61) | Session Detail & Booking Flow | JS.C1, JS.C2, JS.C4, JS.C8, JS.C9 | 2026-01-31 |
| [#69](https://github.com/lolautruche/StructuraLudis/issues/69) | Light theme option | - | 2026-01-31 |
| [#59](https://github.com/lolautruche/StructuraLudis/issues/59) | Authentication Pages | JS.X1 | 2026-01-30 |
| [#58](https://github.com/lolautruche/StructuraLudis/issues/58) | Frontend Foundation | - | 2026-01-29 |
| [#47](https://github.com/lolautruche/StructuraLudis/issues/47) | Privacy Policy Consent | JS.E1 | 2026-01-28 |

---

## Design Decisions

### Email Verification (#73)
- **Decision**: Don't block login, but block bookings if email not verified
- **Rate limiting**: 60s cooldown via `email_verification_sent_at`
- **Token expiration**: 7 days

### Frontend Architecture
- Next.js 14 with App Router
- next-intl for i18n (FR/EN)
- Tailwind CSS + custom UI components
- API client with fetch wrapper

### Backend Architecture
- FastAPI + SQLAlchemy async
- PostgreSQL
- Alembic for migrations
- Jinja2 email templates with i18n

### User Settings (#60)
- Profile editing: name, birth date, timezone, locale
- Password change with email notification
- Email change with verification (token expires in 7 days)
- Remember me: 30-day token vs 24h default
- Forgot password: reset link expires in 1 hour

---

## Technical Debt

| Issue | Item | Priority | Notes |
|-------|------|----------|-------|
| [#81](https://github.com/lolautruche/StructuraLudis/issues/81) | Migrate passlib to libpass | Low | passlib uses deprecated `crypt` module (removed in Python 3.13). Warning is harmless with bcrypt. Migrate to [libpass](https://pypi.org/project/libpass/) when upgrading to Python 3.13. |
| [#82](https://github.com/lolautruche/StructuraLudis/issues/82) | Upgrade Next.js 14 → 16 | Medium | Current: 14.2.0, Latest: 16.x. Major version jump with potential breaking changes (async APIs, React 19, caching). |

---

## Job Stories Reference

Job Stories are defined in [PRD.md](./PRD.md).

### EPIC Legend
- **EPIC 0**: Global Administration (Super Admin)
- **EPIC A**: Organizer Setup
- **EPIC B**: Proposer Journey (GM)
- **EPIC C**: Player Experience
- **EPIC D**: Partner Management
- **EPIC E**: GDPR & Privacy
- **Cross-cutting**: Auth, profile, notifications
