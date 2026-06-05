# Project Structure

This document explains the repository layout and the purpose of top-level folders and key files.

- `run.py`: Application entrypoint; starts the Flask app.
- `requirements.txt` / `runtime.txt`: Python dependencies and runtime config for deployment.
- `Procfile`: Process declaration for PaaS platforms.
- `models/`: Domain models (components, builds, users, parts).
- `services/`: Business logic split into submodules (compatibility, pricing, build_finder, activity).
- `routes/`: Flask route handlers that expose HTTP endpoints.
- `database/`: DB helpers and schema; `data reset/` holds sample data and helper scripts.
- `templates/`: Jinja templates for HTML pages.
- `static/`: Static assets (CSS, JS, images); heavy frontend code (builder UI) lives here.
- `docs/`: Documentation; this new `system_architecture/` folder contains architecture and structure docs.
- `instance/`: Instance-specific files (example: `nexus3d_positions.json`).
- `test/`: Unit tests for services and core logic.

Conventions
- Services should be small and single-responsibility; expose testable functions in `services/*`.
- Models are simple data containers with serialization helpers in `models/*`.
- Routes should remain thin: parse input, call services, return responses.

Adding a New Component
1. Add a model to `models/`.
2. Add service logic under `services/<feature>/`.
3. Add route(s) in `routes/` and wire templates/static assets as needed.
4. Add unit tests in `test/`.

Where to update docs
- Use this `docs/system_architecture/` folder for architecture diagrams and evolution notes.

---
Generated on: 2026-06-05
