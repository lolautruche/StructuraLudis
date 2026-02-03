# Roadmap & Priorities

This document tracks prioritization decisions and project progress.
**Last updated**: 2026-02-03

---

## Current Priorities

### MVP

#### Core Features

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#92](https://github.com/lolautruche/StructuraLudis/issues/92) | Self-service event creation | JS.06, JS.07 | User submits event, admin validates |
| [#93](https://github.com/lolautruche/StructuraLudis/issues/93) | Zone-level table prefix | JS.A0 | Smart numbering option |
| [#94](https://github.com/lolautruche/StructuraLudis/issues/94) | Event region field | JS.A10 | Predefined region list |
| [#95](https://github.com/lolautruche/StructuraLudis/issues/95) | Event list filters | JS.C10 | Region, date, status filters |
| [#96](https://github.com/lolautruche/StructuraLudis/issues/96) | My Events overview | JS.C11 | Organized + registered events |

#### Game Database

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#55](https://github.com/lolautruche/StructuraLudis/issues/55) | External Game Database Sync | JS.05 | **MVP scope**: Import games from GROG with links. No background worker sync for MVP. |
| [#56](https://github.com/lolautruche/StructuraLudis/issues/56) | Game Autocomplete & Metadata | JS.B3, JS.B9 | On-demand enrichment when creating sessions |

#### Waitlist

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#70](https://github.com/lolautruche/StructuraLudis/issues/70) | Waitlist configuration | JS.A9 | Feature issue |
| [#71](https://github.com/lolautruche/StructuraLudis/issues/71) | Waitlist backend | JS.A9 | Backend implementation |
| [#72](https://github.com/lolautruche/StructuraLudis/issues/72) | Waitlist frontend | JS.A9 | Frontend UI |

#### Infrastructure

| Issue | Title | Notes |
|-------|-------|-------|
| [#89](https://github.com/lolautruche/StructuraLudis/issues/89) | Pre-built Docker images | GitHub Actions + ghcr.io registry |

### Post-MVP

#### Features

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#108](https://github.com/lolautruche/StructuraLudis/issues/108) | Batch time slot creation & flexible session start | JS.A2b, JS.B2 | Pattern-based slot creation + flexible start within slot bounds |
| [#62](https://github.com/lolautruche/StructuraLudis/issues/62) | Notification Center & Bell | JS.C2, JS.C3 | In-app notifications |
| [#38](https://github.com/lolautruche/StructuraLudis/issues/38) | Smart check-in reminders | JS.C3 | Automated reminders |
| [#74](https://github.com/lolautruche/StructuraLudis/issues/74) | Magic link authentication | JS.X1 variant | Passwordless login |
| [#75](https://github.com/lolautruche/StructuraLudis/issues/75) | Persist theme preference | JS.X2 | Theme preference in DB |
| [#41](https://github.com/lolautruche/StructuraLudis/issues/41) | Multi-language email templates | JS.A8 | i18n for emails |
| [#97](https://github.com/lolautruche/StructuraLudis/issues/97) | Pagination for admin lists | - | Users, exhibitions lists |
| [#100](https://github.com/lolautruche/StructuraLudis/issues/100) | Event-scoped user ban | - | Organizers can ban users from their event |
| [#101](https://github.com/lolautruche/StructuraLudis/issues/101) | Sortable columns in admin lists | - | Click headers to sort |

#### GDPR & Privacy

| Issue | Title | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#48](https://github.com/lolautruche/StructuraLudis/issues/48) | Data Access (Right of Access) | JS.E2 | Export user data |
| [#49](https://github.com/lolautruche/StructuraLudis/issues/49) | Account Deletion | JS.E3 | Right to erasure |
| [#50](https://github.com/lolautruche/StructuraLudis/issues/50) | Data Portability | JS.E4 | Download data |
| [#51](https://github.com/lolautruche/StructuraLudis/issues/51) | Consent Management | JS.E5 | Manage consents |
| [#52](https://github.com/lolautruche/StructuraLudis/issues/52) | Data Retention Transparency | JS.E6 | Documentation |
| [#53](https://github.com/lolautruche/StructuraLudis/issues/53) | GDPR Request Management | JS.E7 | Admin tools |
| [#54](https://github.com/lolautruche/StructuraLudis/issues/54) | Data Anonymization | JS.E8 | Anonymize old data |

---

## Recently Completed

| Issue | Title | Job Stories | Date |
|-------|-------|-------------|------|
| [#77](https://github.com/lolautruche/StructuraLudis/issues/77) | Player registration to exhibitions | - | 2026-02-03 |
| [#105](https://github.com/lolautruche/StructuraLudis/issues/105) | Move time slots to zone level | JS.D1, JS.A2 | 2026-02-03 |
| [#10](https://github.com/lolautruche/StructuraLudis/issues/10) | Partner Zone Management | JS.D1 | 2026-02-02 |
| [#99](https://github.com/lolautruche/StructuraLudis/issues/99) | Role architecture refactor | JS.02, JS.02b | 2026-02-02 |
| [#13](https://github.com/lolautruche/StructuraLudis/issues/13) | SuperAdmin Portal | JS.01-04 | 2026-02-01 |
| [#7](https://github.com/lolautruche/StructuraLudis/issues/7) | Admin: Event Configuration | JS.A2, JS.A3, JS.A5 | 2026-02-01 |
| [#8](https://github.com/lolautruche/StructuraLudis/issues/8) | Proposer: Session Submission Form | JS.B1-B5 | 2026-02-01 |
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

### Role Architecture (#99)
- **Global roles**: SUPER_ADMIN, ADMIN, USER (platform-wide)
- **Event-scoped roles**: ORGANIZER, PARTNER (per exhibition via `UserExhibitionRole`)
- Exhibition creator tracked via `created_by_id` (main organizer)
- Main organizer cannot be removed by secondary organizers
- Users cannot remove themselves from an exhibition
- Partners see exhibitions in "My Events" with limited management access (their zones only)

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
