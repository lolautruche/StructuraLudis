# Project Context: Structura Ludis

## Project Knowledge Base
- **PRD**: Detailed requirements are located in `doc/PRD.md`.
- **Database Schema**: Visualization and definitions are in `backend/doc/database-schema.mmd`.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2.
- **Frontend**: Next.js, Tailwind CSS, TypeScript.
- **Database**: PostgreSQL 16.
- **Architecture**: Clean Architecture / Domain-Driven Design (DDD).

## Project Structure
- `/backend`: FastAPI application.
- `/frontend`: Next.js application.
- Monorepo orchestrated by Docker Compose at root.

## Development Environment
- **Always use Docker**: Both frontend and backend must be run via Docker Compose. Never run `npm run dev` or `uvicorn` directly on the host.
- **Use Makefile commands**: Run `make help` to see all available commands.
- **Start services**: `make up`
- **Rebuild after code changes**: `make build`, then `make up`
- **Run migrations**: `make db-migrate`
- **Seed database**: `make db-seed` (keeps existing data) or `make db-fixtures` (reset and reload)
- **Always seed after schema changes**: After modifying the database schema or resetting the DB, always run `make db-fixtures` to ensure test data is available.
- **View logs**: `make logs` (all), `make frontend-logs`, `make backend-logs`
- **Services**:
  - `sl-api`: Backend API (port 8000)
  - `sl-frontend`: Frontend Next.js (port 3000)
  - `sl-db`: PostgreSQL database
  - `sl-mail`: Mailpit for email testing (port 8025)
  - `sl-mq`: RabbitMQ message queue

## Coding Standards
- **Language**: All code, documentation, and comments MUST be in English.
- **Naming**: Use snake_case for Python, camelCase for TypeScript.
- **Frontend Responsive Strategy**: Hybrid approach
    - **Share**: Atomic components (Button, Card, Input, Badge) use Tailwind breakpoints.
    - **Separate**: Complex layouts where mobile UX differs significantly (e.g., bottom sheets, swipe interactions, different navigation patterns).
    - Start responsive with CSS breakpoints. Extract to separate `*Mobile.tsx` only when file becomes unreadable or UX fundamentally diverges.
- **Database**:
    - Always use UUIDs for Primary Keys.
    - Every table must have `created_at` and `updated_at` (UTC).
    - Use `jsonb` for flexible settings.
- **Patterns**:
    - Use Repository pattern for DB access.
    - Separate Domain Models (Pydantic) from DB Models (SQLAlchemy).
    - Logic must reside in Domain Services, not in API routes.

## Testing Requirements
- **Backend**: Every new feature must have unit or integration tests (pytest).
- **Frontend**: Every new component must have tests (Jest + Testing Library).
- Tests must pass before merging any PR.
- Test files location: `__tests__/` folder next to the components or `tests/` at project root.

## Validation Protocol
- Before suggesting code, analyze potential side effects on the database schema.
- If a domain logic involves dates (TimeSlots), always remind me to handle Timezone-aware objects (UTC).
- For every new feature, propose a brief test plan (Unit or Integration).
- For every new feature, open a dedicated branch from the main branch, commit and open a pull-request. Tests must pass in order for the pull-request to be merged.
- Each time the database schema is updated, update the Mermaid schema located at `backend/doc/database-schema.mmd`.

## Business Logic Invariants
- **Consistency**: A User's schedule must be conflict-free within a single Exhibition.
- **Ownership**: Every GameTable must be linked to a UserGroup (Organization or Club).
- **Validation**: Only users with 'MODERATOR' or 'ADMIN' permissions in their UserGroup can approve a GameTable.
- **Age Policy**: Registration must verify that User.age >= GameTable.min_age.
- **External Data**: Always prioritize the 'external_id' mapping for Game entities to sync with catalogs (like GROG).

## AI Instructions
- Be concise.
- If a change affects multiple files, explain the impact before coding.
- Always check for time-slot overlaps in table registrations.
