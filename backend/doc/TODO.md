# Backend TODO - PRD Implementation Status

> Generated: 2026-01-29
> PRD Reference: `/doc/PRD.md`

## Overview

| Status | Count | Coverage |
|--------|-------|----------|
| Implemented | 26 features | 93% |
| Partial | 2 features | 7% |
| Not implemented | 0 features | 0% |
| **Total PRD coverage** | | **~96%** |

---

## Not Implemented (0%)

*All core features implemented!*

---

## Partially Implemented

| Feature | PRD Ref | Issue | Current % | What's Missing | Complexity | Effort |
|---------|---------|-------|-----------|----------------|------------|--------|
| Smart check-in | JS.C3 | #38 | 60% | Automatic reminders before session, check-in window enforcement | Medium | 3-5 days |
| Notifications | Cross-cutting | #37 | 10% | Email integration (SendGrid/SES), push notifications, in-app persistence | High | 1-2 weeks |

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

### Notification System (Cross-cutting) - #37

**Current state:** Stub that logs to console

**Required:**
- [ ] Email provider integration (SendGrid, AWS SES, or SMTP)
- [ ] Email templates (session cancelled, booking confirmed, waitlist promoted, reminder)
- [ ] Template localization (FR/EN)
- [ ] Queue system for async sending (optional: Redis + worker)
- [ ] In-app notification persistence (Notification entity)
- [ ] `GET /users/me/notifications` endpoint

**Files to modify:**
- `app/services/notification.py` - Full implementation
- `app/core/config.py` - Email provider settings
- New templates directory
- Optional: `app/domain/notification/entity.py`

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
9. #37 - Notification system complete
10. #38 - Smart check-in reminders (JS.C3)
11. #41 - Multi-language email templates

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