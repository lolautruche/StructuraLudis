# Product Requirement Document (PRD): Structura Ludis

## 1. Vision & Strategic Intent (The WHY)

**Core Vision**
To provide a universal event management ecosystem for all forms of tabletop gaming (RPG, Board Games, Wargames, TCG). Our mission is to eliminate the logistical friction between digital planning and physical reality, ensuring that every seat at every table is optimized, respected, and accessible.

**Problems We Are Solving**
* **Inefficient Resource Optimization:** Large-scale festivals suffer from "dead table time" due to a lack of dynamic rotation management.
* **Static Queue Fatigue:** Players are forced into physical queues for popular games due to the absence of reliable virtual waitlists.
* **Rigid Permission Silos:** Organizers cannot easily delegate autonomy to specialized actors (publishers, clubs) while maintaining oversight.
* **Lack of Accountability:** A disconnect between digital registration and physical presence leads to "ghost" participants and unmonitored venue maintenance.

### 1.1 Global Design Principles
* **Internationalization (i18n) First**: The platform is natively bilingual (English/French). All UI strings must use translation keys, and system entities (Categories, Safety Tools) must support localized labels.
* **Simplified Topology**: Physical space management is handled through "Zones" rather than complex architectural mapping to ensure agility and mobile responsiveness.

---

## 2. Functional Scope (The WHAT): JOB STORIES

### EPIC 0: Global Administration (Super Admin)
*Objective: Manage the platform's multi-event lifecycle and global user permissions.*

* **JS.01 - Multi-Event Orchestration**
    * **When** I am a Global Administrator (Super Admin),
    * **I want** to create a new Event entity with its specific start and end dates,
    * **so that** I can prepare several conventions or editions on the same platform instance without data overlap.

* **JS.02 - User Promotion & Role Management**
    * **When** I am a Super Admin,
    * **I want** to promote a standard user to the rank of "Organizer" or "Partner",
    * **so that** I can delegate the management of a specific event or a specific zone to the right person.

* **JS.03 - Global Event Configuration**
    * **When** creating or editing an event,
    * **I want** to define its global settings (Timezone, Language, Registration visibility),
    * **so that** I can control the public state and the regional context of the convention.

* **JS.04 - Instance Oversight**
    * **When** I am logged into the Super Admin portal,
    * **I want** to see an overview of all active and past events,
    * **so that** I can monitor the platform's global usage and performance.

### EPIC A: The Organizer's Setup

* **JS.A0 - Simplified Topology (Zones)**
    * **When** I prepare a venue plan for a convention,
    * **I want** to create logical "Zones" (e.g., "RPG Area", "Indie Games", "Main Stage") and assign table blocks to them,
    * **so that** I can manage space distribution without the overhead of a full architectural building map.

* **JS.A1 - Complete Physical Topology**
    * **When** I prepare a venue plan for a convention (physical or virtual),
    * **I want** to create a digital inventory (Building > Floor > Room > Numbered Tables),
    * **so that** I can prevent physical resource collisions.

* **JS.A2 - Flexible TimeSlots**
    * **When** I define the schedule for the RPG or Board Game area,
    * **I want** to configure periods (e.g., Morning, Afternoon, Evening, Night) with specific maximum durations allowed per session for each period,
    * **so that** the framework remains adaptable to different game types while allowing for longer sessions at specific times (e.g., 4h afternoon, 6h night).

* **JS.A3 - Buffer Times**
    * **When** I configure periods and spaces,
    * **I want** to define a configurable buffer time (e.g., 0 to 30 min) between sessions on a single physical table,
    * **so that** I can adapt to the event's scale, allowing for either rapid transitions or comfortable cleaning breaks.

* **JS.A4 - Delegated Autonomy**
    * **When** I partner with trusted clubs or publishers,
    * **I want** to assign them exclusive management of specific rooms or table blocks,
    * **so that** they can operate autonomously to schedule their own activities without requesting the main organizer for every change.

* **JS.A5 - Safety Framework**
    * **When** I set the event rules,
    * **I want** to define a library of Safety Tools (X-Card, Lines & Veils, etc.) and audience categories (All Audiences, Adult, Beginner),
    * **so that** safety standards are normalized across all tables.

* **JS.A6 - No-Show & Reallocation Policy**
    * **When** setting global rules,
    * **I want** to define automatic grace periods (e.g., 15 min) and physical table reallocation rules for missing GMs,
    * **so that** the system can autonomously release resources for "pop-up" games without manual intervention.

* **JS.A7 - Moderation Dialogue (Organizer)**
    * **When** a session is submitted for review,
    * **I want** to communicate directly with the proposer on their session sheet,
    * **so that** I can support them in adjusting their table logistics before final validation.

* **JS.A8 - Multi-language Event Presence**
    * **When** configuring an event,
    * **I want** to define a primary language and support secondary languages for the event description and automated communications,
    * **so that** I can attract an international audience while maintaining local relevance.

---

### EPIC B: The Proposer's Journey

* **JS.B1 - Asynchronous Drafting**
    * **When** I propose a session but don't have all details finalized (pitch, visuals, technical needs),
    * **I want** to save my progress as a draft,
    * **so that** I can complete my sheet at my own pace, across multiple logins, without losing my work.

* **JS.B2 - Dynamic Slotting**
    * **When** planning my session,
    * **I want** to choose a start time and duration that fits within the organizer's limits for that period (e.g., max 4h afternoon, 6h for night session),
    * **so that** my game is logistically compatible with the global rotation.

* **JS.B3 - Game Identity (Game Reference)**
    * **When** identifying the game for my session,
    * **I want** to link it to an external reference (e.g., GROG) if available, or enter information manually for prototypes,
    * **so that** players are clearly informed while I retain the freedom to propose new games.

* **JS.B4 - Safety Tools Commitment**
    * **When** configuring my session,
    * **I want** to explicitly select the safety tools (X-Card, Lines & Veils, etc.) I commit to using,
    * **so that** I guarantee a healthy and transparent environment for my future players.

* **JS.B5 - Moderation Workflow (Proposer)**
    * **When** my session is under review,
    * **I want** to communicate directly with moderators,
    * **so that** we can adjust logistics without a flat rejection.

* **JS.B6 - Agenda Management**
    * **When** logged in,
    * **I want** a clear dashboard of my registrations and physical locations (Room/Table),
    * **so that** I avoid scheduling conflicts.

* **JS.B7 - No-show Management**
    * **When** the session start time has passed and registered players haven't checked in,
    * **I want** to declare their absence in one click,
    * **so that** their seats are immediately released for the digital waitlist.

* **JS.B8 - D-Day Accountability**
    * **When** my session ends,
    * **I want** to quickly report actual player attendance and table cleanliness via the app,
    * **so that** I officially release the physical resource and provide accurate usage data to the organizer.

---

### EPIC C: The Player's Experience

* **JS.C1 - Discovery and Exploration**
    * **When** I am on-site with my phone,
    * **I want** to filter available tables by game type (RPG/Board Game), style (SF/Fantasy), accessibility, or immediate availability,
    * **so that** I can find an activity quickly.

* **JS.C2 - Safe Booking**
    * **When** joining a session,
    * **I want** to see the required age and safety tools,
    * **so that** I ensure the experience matches my personal boundaries.

* **JS.C3 - Smart Check-in**
    * **When** registered,
    * **I want** to receive reminders and confirm my presence within a specific window beforehand,
    * **so that** I secure my seat or allow someone else to play if I can't make it.

* **JS.C4 - Virtual Waitlist**
    * **When** a table is full,
    * **I want** to join a digital queue and be notified of openings,
    * **so that** I can explore the convention instead of standing in line.

* **JS.C5 - Pop-up Games**
    * **When** I don't have a planned session but am available,
    * **I want** to see seats or tables that have just been released due to a no-show,
    * **so that** I can join a game spontaneously.

* **JS.C6 - Language-Based Discovery**
    * **When** searching for a game,
    * **I want** to filter tables by the language spoken at the table (e.g., FR, EN, or Bilingual),
    * **so that** I am sure I can participate fully in the session.

---

### EPIC D: Partner Management (Exhibitors & Clubs)

* **JS.D1 - Space Autonomy**
    * **When** I am a publisher or a club with a dedicated area (zone or room),
    * **I want** to administer my own physical tables,
    * **so that** I can schedule my demos or campaigns without requesting the main organizer for every change.

* **JS.D2 - Team Management**
    * **When** I manage a booth or association area,
    * **I want** to invite and assign my own demonstrators or GMs to my tables,
    * **so that** I can manage my team's schedule internally.

* **JS.D3 - Delegated Moderation**
    * **When** a team member proposes a session on my dedicated space,
    * **I want** to validate it myself,
    * **so that** I accelerate the publishing flow while respecting global event rules.

* **JS.D4 - Partner Visibility**
    * **When** I schedule a session,
    * **I want** it clearly identified as "Organized by [Partner Name]",
    * **so that** I promote my brand or club identity to visitors.
