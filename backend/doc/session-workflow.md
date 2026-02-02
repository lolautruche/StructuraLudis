# Session Workflow Documentation

This document describes the session approval workflows for Issue #10 (Partner Zone Management) and #30 (Moderation).

## Table of Contents

1. [Public Session Workflow](#public-session-workflow)
2. [Partner Session Workflow](#partner-session-workflow)
3. [Session Status Overview](#session-status-overview)
4. [Permission Matrix](#permission-matrix)
5. [Moderation Comments Flow](#moderation-comments-flow)

---

## Public Session Workflow

Standard workflow for sessions proposed by players/GMs.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : User creates session

    DRAFT --> PENDING_MODERATION : User submits
    DRAFT --> [*] : User deletes

    PENDING_MODERATION --> VALIDATED : Organizer approves
    PENDING_MODERATION --> REJECTED : Organizer rejects
    PENDING_MODERATION --> CHANGES_REQUESTED : Organizer requests changes

    CHANGES_REQUESTED --> PENDING_MODERATION : User resubmits
    CHANGES_REQUESTED --> [*] : User deletes

    VALIDATED --> IN_PROGRESS : Session starts

    IN_PROGRESS --> FINISHED : Session ends

    note right of DRAFT
        Session is private, only visible to creator.
        Can be edited freely.
    end note

    note right of PENDING_MODERATION
        Awaiting organizer review.
        Moderation comments enabled.
    end note

    note right of VALIDATED
        Session is public and bookable.
        Players can register.
    end note
```

**API Endpoints:**
- `POST /sessions/` - Create session (DRAFT)
- `POST /sessions/{id}/submit` - Submit for review
- `POST /sessions/{id}/moderate` - Approve/reject/request changes
- `POST /sessions/{id}/start` - Start session
- `POST /sessions/{id}/end` - End session

---

## Partner Session Workflow

### With Auto-Validation (zone.partner_validation_enabled = true)

Sessions created by partners in zones with auto-validation enabled skip the moderation process.

```mermaid
stateDiagram-v2
    [*] --> VALIDATED : Partner creates session

    note right of VALIDATED
        Auto-validated: No approval needed
        when zone.partner_validation_enabled=true
    end note

    VALIDATED --> IN_PROGRESS : Session starts
    IN_PROGRESS --> FINISHED : Session ends
```

**API Endpoints:**
- `POST /partner/sessions` - Create single session (auto-validates)
- `POST /partner/sessions/batch` - Create series (auto-validates)

### Without Auto-Validation (zone.partner_validation_enabled = false)

Sessions require organizer approval like standard sessions.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Partner creates session

    DRAFT --> PENDING_MODERATION : Partner submits

    PENDING_MODERATION --> VALIDATED : Organizer approves
    PENDING_MODERATION --> REJECTED : Organizer rejects
    PENDING_MODERATION --> CHANGES_REQUESTED : Organizer requests changes

    CHANGES_REQUESTED --> PENDING_MODERATION : Partner resubmits

    VALIDATED --> IN_PROGRESS : Session starts
    IN_PROGRESS --> FINISHED : Session ends
```

---

## Session Status Overview

```mermaid
flowchart TB
    subgraph Creation["Creation Phase"]
        DRAFT["DRAFT\nPrivate, editable"]
    end

    subgraph Moderation["Moderation Phase"]
        PENDING["PENDING_MODERATION\nAwaiting review"]
        CHANGES["CHANGES_REQUESTED\nNeeds revision"]
        REJECTED["REJECTED\nNot approved"]
    end

    subgraph Active["Active Phase"]
        VALIDATED["VALIDATED\nPublic, bookable"]
        IN_PROGRESS["IN_PROGRESS\nCurrently running"]
        FINISHED["FINISHED\nCompleted"]
        CANCELLED["CANCELLED\nCancelled by GM/organizer"]
    end

    DRAFT --> PENDING
    PENDING --> VALIDATED
    PENDING --> CHANGES
    PENDING --> REJECTED
    CHANGES --> PENDING
    VALIDATED --> IN_PROGRESS
    VALIDATED --> CANCELLED
    IN_PROGRESS --> FINISHED
```

### Status Descriptions

| Status | Description | Visible to Public | Bookable |
|--------|-------------|-------------------|----------|
| DRAFT | Initial state, session is being prepared | No | No |
| PENDING_MODERATION | Submitted for organizer review | No | No |
| CHANGES_REQUESTED | Organizer requested modifications | No | No |
| REJECTED | Session was rejected | No | No |
| VALIDATED | Approved and open for registration | Yes | Yes |
| IN_PROGRESS | Session is currently running | Yes | No |
| FINISHED | Session completed | Yes | No |
| CANCELLED | Session was cancelled | Yes | No |

---

## Permission Matrix

Who can perform which actions:

| Action | Creator | Organizer | Partner (own zone) | Partner (other zone) |
|--------|---------|-----------|-------------------|---------------------|
| Create session | ✓ | ✓ | ✓ | ✗ |
| Edit DRAFT session | ✓ | ✓ | ✓ (own sessions) | ✗ |
| Submit session | ✓ | ✓ | ✓ (own sessions) | ✗ |
| Moderate session | ✗ | ✓ | ✓ (if enabled*) | ✗ |
| Assign table | ✗ | ✓ | ✓ | ✗ |
| Cancel session | ✓ | ✓ | ✓ (own sessions) | ✗ |
| Start/End session | ✓ | ✓ | ✓ (own sessions) | ✗ |

**\*** Partner can moderate sessions if `zone.partner_validation_enabled = true`

---

## Moderation Comments Flow

Communication between session creator and moderators during the review process (#30).

```mermaid
sequenceDiagram
    participant GM as Session Creator
    participant System as System
    participant Mod as Organizer/Partner

    GM->>System: Submit session
    System-->>GM: Status: PENDING_MODERATION

    alt Approved
        Mod->>System: Approve session
        System-->>GM: Status: VALIDATED
    else Request Changes
        Mod->>System: Request changes + comment
        System-->>GM: Status: CHANGES_REQUESTED
        GM->>System: Edit session
        GM->>System: Add comment (optional)
        GM->>System: Resubmit
        System-->>Mod: Status: PENDING_MODERATION
        Mod->>System: Approve
        System-->>GM: Status: VALIDATED
    else Rejected
        Mod->>System: Reject + reason
        System-->>GM: Status: REJECTED
    end
```

**API Endpoints:**
- `GET /sessions/{id}/comments` - List moderation comments
- `POST /sessions/{id}/comments` - Add comment to moderation thread
