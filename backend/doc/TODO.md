# Backend TODO - PRD Implementation Status

> Generated: 2026-01-29
> PRD Reference: `/doc/PRD.md`

## Overview

| Status | Count | Coverage |
|--------|-------|----------|
| Implemented | 28 features | 76% |
| Partial | 1 feature | 3% |
| Not implemented | 9 features | 21% |
| **Total PRD coverage** | | **~79%** |

---

## Not Implemented - Game Reference Sync

| Feature | PRD Ref | Issue | Complexity | Effort |
|---------|---------|-------|------------|--------|
| External Game Database Sync | JS.05 | #55 | High | 1-2 weeks |
| Game Autocomplete & Metadata | JS.B3, JS.B9 | #56 | Medium | 3-5 days |

---

## Not Implemented - EPIC E: GDPR Compliance

| Feature | PRD Ref | Issue | Complexity | Effort |
|---------|---------|-------|------------|--------|
| ~~Privacy Policy Consent~~ | JS.E1 | #47 | ✅ Done | - |
| Data Access (Right of Access) | JS.E2 | #48 | Medium | 2-3 days |
| Account Deletion (Right to Erasure) | JS.E3 | #49 | High | 3-5 days |
| Data Portability | JS.E4 | #50 | Low | 1 day |
| Consent Management | JS.E5 | #51 | Medium | 2-3 days |
| Data Retention Transparency | JS.E6 | #52 | Low | 1-2 days |
| GDPR Request Management (Admin) | JS.E7 | #53 | High | 5-7 days |
| Data Anonymization | JS.E8 | #54 | High | 3-5 days |

---

## Partially Implemented

| Feature | PRD Ref | Issue | Current % | What's Missing | Complexity | Effort |
|---------|---------|-------|-----------|----------------|------------|--------|
| Smart check-in | JS.C3 | #38 | 60% | Automatic reminders before session, check-in window enforcement | Medium | 3-5 days |

---

## Recently Completed (Phase 1 & Phase 2)

| Feature | PRD Ref | Issue | Status |
|---------|---------|-------|--------|
| Session copy/duplicate | JS.B7 (implicit) | #33 | ✅ Done |
| Partner visibility | JS.D4 | #36 | ✅ Done |
| Delegated moderation | JS.D3 | #32 | ✅ Done |
| Event configuration | JS.03 | #39 | ✅ Done |
| Moderation dialogue | JS.A7, JS.B5 | #30 | ✅ Done |
| Partner team management | JS.D2 | #31 | ✅ Done |
| End-of-session reporting | JS.B8 | #35 | ✅ Done |
| Delegated autonomy | JS.A4 | #40 | ✅ Done (via #31) |
| i18n infrastructure | 1.1 | #34 | ✅ Done |
| Notification system | Cross-cutting | #37 | ✅ Done |

---

## Detailed Feature Breakdown

### ~~Moderation Dialogue (JS.A7, JS.B5) - #30~~ ✅ DONE

Two-way comment/dialogue system for session moderation:
- `ModerationComment` entity with session_id, user_id, content, created_at
- `POST /sessions/{id}/comments` - Add comment to thread
- `GET /sessions/{id}/comments` - List comments chronologically
- `CHANGES_REQUESTED` status for back-and-forth workflow
- Proposer can resubmit after addressing feedback

---

### ~~Partner Team Management (JS.D2) - #31~~ ✅ DONE

Full CRUD for partner groups and member management:
- `GET /groups/` - List groups (with filters)
- `POST /groups/` - Create group (organizers)
- `GET /groups/{id}` - Get group with members
- `PUT /groups/{id}` - Update group details
- `DELETE /groups/{id}` - Delete group
- `POST /groups/{id}/members` - Add member with role
- `PATCH /groups/{id}/members/{user_id}` - Update member role
- `DELETE /groups/{id}/members/{user_id}` - Remove member
- Role hierarchy: OWNER > ADMIN > MODERATOR > MEMBER

---

### ~~Delegated Moderation (JS.D3) - #32~~ ✅ DONE

Partners can now moderate sessions in zones delegated to their group.

---

### ~~Session Copy/Duplicate - #33~~ ✅ DONE

`POST /sessions/{id}/copy` endpoint implemented with optional time slot and schedule override.

---

### ~~i18n Infrastructure (1.1) - #34~~ ✅ DONE

JSONB-based translation system for multi-language content:
- `app/core/i18n.py` - Translation helpers with locale resolution and fallback
- `app/api/deps/i18n.py` - Locale detection from Accept-Language header and user preference
- JSONB `_i18n` fields added to: GameCategory, SafetyTool, Exhibition, Zone
- Schemas updated to accept/return i18n fields
- 22 unit tests for i18n utilities

---

### ~~End-of-Session Reporting (JS.B8) - #35~~ ✅ DONE

Session lifecycle management with reporting:
- `POST /sessions/{id}/start` - Start session (sets actual_start, transitions to IN_PROGRESS)
- `POST /sessions/{id}/end` - End session with optional report
- `SessionEndReport` schema with actual_player_count, table_condition (CLEAN/NEEDS_CLEANING/DAMAGED), notes
- Automatic status transition to FINISHED
- Report data stored in session entity

---

### ~~Partner Visibility (JS.D4) - #36~~ ✅ DONE

`provided_by_group_name` now included in session responses and search results.

---

### ~~Notification System (Cross-cutting) - #37~~ ✅ DONE

Multi-channel notification system with email backends and i18n support:
- `Notification` entity for in-app persistence (user_id, type, channel, subject, body, is_read)
- Email backends: Console (dev), SMTP (Mailpit), SendGrid (prod), Gmail API
- Jinja2 email templates with FR/EN localization
- `GET /notifications/` - List user notifications
- `POST /notifications/mark-read` - Mark specific as read
- `POST /notifications/mark-all-read` - Mark all as read
- `GET /notifications/unread-count` - Unread count
- Firebase Cloud Messaging support for push notifications (configurable)
- See `doc/PROJECT-CONTEXT.md` for configuration details

---

### Smart Check-in Reminders (JS.C3) - #38

**Current state:** Check-in endpoint exists, no reminders

**Required:**
- [ ] Scheduled job to send reminders X minutes before session
- [ ] `Exhibition.reminder_minutes` setting (e.g., 30, 15)
- [ ] Integration with notification service
- [ ] Check-in window enforcement (optional)

**Dependencies:**
- #37 - Notification system must be functional
- Background task scheduler (Celery, APScheduler, or similar)

---

### ~~Event Configuration (JS.03) - #39~~ ✅ DONE

Added to Exhibition entity:
- `is_registration_open: bool` - Control if registrations are open
- `registration_opens_at: datetime` - When registrations open
- `registration_closes_at: datetime` - When registrations close
- `primary_language: str` - Main event language
- `secondary_languages: list[str]` - Additional supported languages

---

### Multi-language Email Templates (JS.A8) - #41

**Current state:** 30% complete

**Required:**
- [ ] Email template structure (Jinja2 or similar)
- [ ] Templates in FR and EN
- [ ] Template selection based on user.locale
- [ ] Fallback to exhibition primary_language

**Dependencies:**
- #37 - Notification system implementation

---

### ~~Privacy Policy Consent (JS.E1) - #47~~ ✅ DONE

GDPR consent requirement at registration:
- `privacy_accepted_at` field added to User entity
- `accept_privacy_policy: bool` required in RegisterRequest
- Registration blocked if consent not given (400 error)
- Consent timestamp stored for audit purposes
- Frontend: Privacy policy page to be implemented separately

---

### Data Access / Export (JS.E2) - #48

**Current state:** Not implemented

**Required:**
- [ ] `GET /api/v1/users/me/data-export` endpoint
- [ ] Export user profile, bookings, notifications, comments
- [ ] Generate downloadable JSON file
- [ ] Audit log for export requests

---

### Account Deletion (JS.E3) - #49

**Current state:** Not implemented

**Required:**
- [ ] `POST /api/v1/users/me/delete-request` endpoint
- [ ] Confirmation with password verification
- [ ] Grace period (7 days) before actual deletion
- [ ] Anonymize historical data (see #54)
- [ ] Confirmation emails before/after deletion

**Dependencies:**
- #54 - Data Anonymization

---

### Data Portability (JS.E4) - #50

**Current state:** Not implemented

**Required:**
- [ ] JSON export format (machine-readable)
- [ ] Document data schema
- [ ] Optional CSV export

**Notes:** Largely covered by #48 (Data Access)

---

### Consent Management (JS.E5) - #51

**Current state:** Not implemented

**Required:**
- [ ] Add preferences to User: `email_notifications`, `marketing_emails`
- [ ] `PATCH /api/v1/users/me/preferences` endpoint
- [ ] Respect preferences in notification service
- [ ] Unsubscribe links in emails

---

### Data Retention Transparency (JS.E6) - #52

**Current state:** Not implemented

**Required:**
- [ ] Define retention policy (inactive accounts, audit logs, anonymized data)
- [ ] Document in privacy policy
- [ ] Automated cleanup job for expired data

---

### GDPR Request Management Admin (JS.E7) - #53

**Current state:** Not implemented

**Required:**
- [ ] `GdprRequest` entity (user_id, type, status, requested_at, processed_at)
- [ ] Admin endpoints for request management
- [ ] 30-day deadline tracking and reminders
- [ ] Audit trail for all GDPR actions
- [ ] Compliance report export

---

### Data Anonymization (JS.E8) - #54

**Current state:** Not implemented

**Required:**
- [ ] Anonymization strategy for deleted users
- [ ] Replace user_id with anonymous reference in Bookings
- [ ] Anonymize ModerationComments (keep content, remove author)
- [ ] Delete Notifications
- [ ] Preserve aggregate statistics

---

### External Game Database Sync (JS.05) - #55

**Current state:** Not implemented

**Required:**
- [ ] GROG scraper for initial RPG catalog import
- [ ] RSS feed worker for updates (daily sync)
- [ ] Game entity fields: external_provider, external_id, external_url, themes, cover_image_url
- [ ] Management command: `import_grog`
- [ ] Future: BGG XML API for board games

**Technical notes:**
- GROG has no API, scraping required (respect rate limits)
- Use RSS feed for staying up to date
- BGG has public XML API

---

### Game Autocomplete & Metadata (JS.B3, JS.B9) - #56

**Current state:** Not implemented

**Required:**
- [ ] `GET /api/v1/games/search?q=` - Autocomplete endpoint
- [ ] `GET /api/v1/games/{id}` - Full game details
- [ ] `POST /api/v1/games` - Manual game entry
- [ ] Frontend: autocomplete input, game card with cover/themes
- [ ] "Can't find your game?" → manual entry fallback

**Dependencies:**
- #55 - External Game Database Sync

---

## Priority Recommendations

### ~~Phase 1: Quick Wins~~ ✅ COMPLETED
1. ~~#33 - Session copy/duplicate~~ ✅
2. ~~#36 - Partner visibility (JS.D4)~~ ✅
3. ~~#32 - Delegated moderation (JS.D3)~~ ✅
4. ~~#39 - Event configuration complete (JS.03)~~ ✅

### ~~Phase 2: Core Features~~ ✅ COMPLETED
5. ~~#30 - Moderation dialogue (JS.A7, JS.B5)~~ ✅
6. ~~#31 - Partner team management (JS.D2)~~ ✅
7. ~~#35 - End-of-session reporting (JS.B8)~~ ✅

### Phase 3: Infrastructure (2-3 weeks)
8. ~~#34 - i18n infrastructure~~ ✅
9. ~~#37 - Notification system complete~~ ✅
10. #38 - Smart check-in reminders (JS.C3)
11. #41 - Multi-language email templates

### Phase 4: GDPR Compliance (3-4 weeks)
12. ~~#47 - Privacy Policy Consent (JS.E1)~~ ✅
13. #51 - Consent Management (JS.E5)
14. #48 - Data Access / Export (JS.E2)
15. #50 - Data Portability (JS.E4)
16. #54 - Data Anonymization (JS.E8)
17. #49 - Account Deletion (JS.E3) - depends on #54
18. #53 - GDPR Request Management Admin (JS.E7)
19. #52 - Data Retention Policy (JS.E6)

### Phase 5: Game Reference Sync (1-2 weeks)
20. #55 - External Game Database Sync (GROG import + RSS)
21. #56 - Game Autocomplete & Metadata Display (JS.B3, JS.B9)

---

## Implemented Features Reference

For completeness, here are the fully implemented features:

| Feature | PRD Ref | Status |
|---------|---------|--------|
| Multi-Event Orchestration | JS.01 | ✅ 100% |
| User Promotion & Roles | JS.02 | ✅ 100% |
| Platform Oversight | JS.04 | ✅ 100% |
| Simplified Topology (Zones) | JS.A0 | ✅ 100% |
| Physical Topology (Tables) | JS.A1 | ✅ 100% |
| Flexible TimeSlots | JS.A2 | ✅ 100% |
| Buffer Times | JS.A3 | ✅ 100% |
| Safety Framework | JS.A5 | ✅ 100% |
| No-Show & Auto-Cancel | JS.A6 | ✅ 100% |
| Asynchronous Drafting | JS.B1 | ✅ 100% |
| Dynamic Slotting | JS.B2 | ✅ 100% |
| Game Identity | JS.B3 | ✅ 100% |
| Safety Tools Commitment | JS.B4 | ✅ 100% |
| Agenda Management | JS.B6 | ✅ 100% |
| No-Show Management | JS.B7 | ✅ 100% |
| Session Cancellation | JS.B4 | ✅ 100% |
| Session Discovery | JS.C1 | ✅ 100% |
| Safe Booking | JS.C2 | ✅ 100% |
| Virtual Waitlist | JS.C4 | ✅ 100% |
| Pop-up Games | JS.C5 | ✅ 100% |
| Language Discovery | JS.C6 | ✅ 100% |
| Partner Space Autonomy | JS.D1 | ✅ 100% |
| Session Copy/Duplicate | JS.B7 | ✅ 100% |
| Partner Visibility | JS.D4 | ✅ 100% |
| Delegated Moderation | JS.D3 | ✅ 100% |
| Event Configuration | JS.03 | ✅ 100% |
| Moderation Dialogue | JS.A7, JS.B5 | ✅ 100% |
| Partner Team Management | JS.D2 | ✅ 100% |
| End-of-Session Reporting | JS.B8 | ✅ 100% |
| Delegated Autonomy | JS.A4 | ✅ 100% |
| i18n Infrastructure | 1.1 | ✅ 100% |