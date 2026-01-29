# Backend TODO - PRD Implementation Status

> Generated: 2026-01-29
> PRD Reference: `/doc/PRD.md`

## Overview

| Status | Count | Coverage |
|--------|-------|----------|
| Implemented | 22 features | 79% |
| Partial | 4 features | 14% |
| Not implemented | 3 features | 11% |
| **Total PRD coverage** | | **~90%** |

---

## Not Implemented (0%)

| Feature | PRD Ref | Issue | Description | Complexity | Effort |
|---------|---------|-------|-------------|------------|--------|
| Moderation dialogue | JS.A7, JS.B5 | #30 | Comment/thread system on sessions for negotiation before validation | Medium | 3-5 days |
| Partner team management | JS.D2 | #31 | Invite/assign demonstrators to partner groups | Medium | 3-5 days |
| i18n infrastructure | 1.1 | #34 | JSONB translation fields for SafetyTools, Categories, Exhibitions, etc. | High | 1-2 weeks |

---

## Partially Implemented

| Feature | PRD Ref | Issue | Current % | What's Missing | Complexity | Effort |
|---------|---------|-------|-----------|----------------|------------|--------|
| Delegated autonomy | JS.A4 | #40 | 70% | Endpoints for group member management (see #31) | Medium | 3-5 days |
| End-of-session reporting | JS.B8 | #35 | 40% | Endpoints for actual attendance, table cleanliness, session closure | Medium | 3-5 days |
| Smart check-in | JS.C3 | #38 | 60% | Automatic reminders before session, check-in window enforcement | Medium | 3-5 days |
| Notifications | Cross-cutting | #37 | 10% | Email integration (SendGrid/SES), push notifications, in-app persistence | High | 1-2 weeks |

---

## Recently Completed (Phase 1 Quick Wins)

| Feature | PRD Ref | Issue | Status |
|---------|---------|-------|--------|
| Session copy/duplicate | JS.B7 (implicit) | #33 | ✅ Done |
| Partner visibility | JS.D4 | #36 | ✅ Done |
| Delegated moderation | JS.D3 | #32 | ✅ Done |
| Event configuration | JS.03 | #39 | ✅ Done |

---

## Detailed Feature Breakdown

### Moderation Dialogue (JS.A7, JS.B5) - #30

**Current state:** Simple approve/reject with one-way rejection_reason

**Required:**
- [ ] `ModerationComment` entity (session_id, user_id, content, created_at)
- [ ] `POST /sessions/{id}/comments` - Add comment
- [ ] `GET /sessions/{id}/comments` - List comments
- [ ] Notification when new comment added
- [ ] Status for "changes requested" workflow

**Files to modify:**
- `app/domain/game/entity.py` - Add ModerationComment
- `app/domain/game/schemas.py` - Add comment schemas
- `app/api/v1/endpoint/game_session.py` - Add endpoints
- `app/services/game_session.py` - Add comment logic

---

### Partner Team Management (JS.D2) - #31

**Current state:** UserGroup and UserGroupMembership entities exist, no CRUD endpoints

**Required:**
- [ ] `POST /groups/{id}/members` - Invite user to group
- [ ] `GET /groups/{id}/members` - List group members
- [ ] `DELETE /groups/{id}/members/{user_id}` - Remove member
- [ ] `PATCH /groups/{id}/members/{user_id}` - Update member role
- [ ] Email invitation system

**Files to modify:**
- `app/api/v1/endpoint/organization.py` or new `group.py`
- `app/services/organization.py` - Add member management logic

---

### ~~Delegated Moderation (JS.D3) - #32~~ ✅ DONE

Partners can now moderate sessions in zones delegated to their group.

---

### ~~Session Copy/Duplicate - #33~~ ✅ DONE

`POST /sessions/{id}/copy` endpoint implemented with optional time slot and schedule override.

---

### i18n Infrastructure (1.1) - #34

**Current state:** `User.locale` exists, no translation mechanism

**Required:**
- [ ] Add `name_i18n: JSONB` to translatable entities (SafetyTool, GameCategory, etc.)
- [ ] Middleware to detect Accept-Language header
- [ ] Helper to resolve translated field based on locale
- [ ] Migration for all affected tables
- [ ] Update schemas to handle translations

**Entities to modify:**
- SafetyTool (name, description)
- GameCategory (name)
- Exhibition (title, description)
- GameSession (title, description) - optional

**Files to modify:**
- All entity files with translatable content
- `app/api/deps.py` - Add locale detection
- New `app/core/i18n.py` - Translation helpers

---

### End-of-Session Reporting (JS.B8) - #35

**Current state:** Fields exist (actual_start, actual_end) but no endpoints

**Required:**
- [ ] `POST /sessions/{id}/start` - Mark session as started (sets actual_start)
- [ ] `POST /sessions/{id}/end` - Mark session as ended with report
- [ ] `SessionEndReport` schema (actual_attendance, table_condition, notes)
- [ ] Update session status to FINISHED
- [ ] Release physical table

**Files to modify:**
- `app/domain/game/schemas.py` - Add SessionEndReport
- `app/api/v1/endpoint/game_session.py` - Add endpoints
- `app/services/game_session.py` - Add reporting logic

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

### Phase 2: Core Features (2 weeks)
5. #30 - Moderation dialogue (JS.A7, JS.B5)
6. #31 - Partner team management (JS.D2)
7. #35 - End-of-session reporting (JS.B8)

### Phase 3: Infrastructure (2-3 weeks)
8. #34 - i18n infrastructure
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