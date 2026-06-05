# System Architecture

## Purpose
Provide a concise overview of the application's architecture, components, and data flows to help developers and stakeholders understand how the system is organized and how parts interact.

## High-level Components
- Frontend: templates/ and static/ (HTML, CSS, JS) — user UI and builder tools.
- Backend: `run.py`, `routes/` and `services/` — HTTP endpoints and business logic.
- Models: `models/` — domain objects (components, builds, users).
- Database: `database/` and `data reset/` — persistence layer and migration scripts.
- Services: modular service layer in `services/` (compatibility, build finder, pricing, activity).
- Tests: `test/` — unit tests for services and compatibility logic.

## Data Flow
1. User interacts with frontend (templates + JS).
2. Frontend calls backend routes in `routes/`.
3. Routes invoke service layer functions in `services/`.
4. Services use `models/` and `database/db.py` to read/write data.
5. Background tasks (if any) update caches and activity logs.

## Integration Points
- External services (e.g., package repositories, pricing APIs) should be wrapped by service adapters under `services/pricing/`.
- Caching layer lives in `services/cache.py`.

## Deployment & Runtime
- Single-process WSGI/Flask app launched from `run.py`.
- Environment pinned via `requirements.txt` and `runtime.txt`.
- Procfile indicates process startup for PaaS deployments.

## Non-functional Concerns
- Security: validate inputs in routes and services; secure any file/database access.
- Observability: add logging in `services/*` and metrics around critical flows (build generation, compatibility checks).
- Scalability: separate read-heavy endpoints behind caching and consider background workers for long-running build-fix tasks.

## Diagram Notes
- Add architecture diagrams into this folder (PNG/SVG) or use Mermaid blocks in future revisions.

---
Generated on: 2026-06-05
