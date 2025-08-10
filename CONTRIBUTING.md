# Contributing to Sync2Cal

Thanks for your interest in contributing! This guide explains setup, coding standards, and how to add new integrations.

## Quick Start

- Python 3.10+
- Install deps:
  ```bash
  pip install -r requirements.txt
  ```
- Run locally:
  ```bash
  uvicorn main:app --reload --env-file .env
  ```
- Open docs: http://localhost:8000/docs

## Code Style & Tooling

- Prefer small functions, descriptive names, early returns, and clear error handling.
- Formatting/linting: Black, Ruff. Type-checking (optional): MyPy. Consider pre-commit hooks.

## Architecture Overview

- `base/`: primitives
  - `IntegrationBase`: integration metadata and multi-calendar hooks
  - `CalendarBase`: contract for `fetch_events(...)-> List[Event]`
  - `mount_integration_routes(...)`: wires `GET /events`
- `integrations/`: one file per provider with `XyzCalendar` and `XyzIntegration`
- `main.py`: registers integration instances and mounts them in a loop

## Adding a New Integration

1) Create `integrations/<name>.py` with:
   - `class <Name>Calendar(CalendarBase)` implementing `fetch_events(...)-> List[Event]`
   - `class <Name>Integration(IntegrationBase)`
2) Append an instance to the `integrations` list in `main.py`.
3) Do not create custom routes; rely on `mount_integration_routes`.

Tips
- Validate inputs; use simple param types (str/int/bool) and defaults.
- Map network errors to `HTTPException(status_code=502, detail=...)`.
- For all-day events, set `end = start + timedelta(days=1)` and `all_day=True`.
- Build deterministic `uid` values (e.g., `tmdb-<slug>-<date>`).

## Testing

- Use `pytest` + `fastapi.testclient`.
- Monkeypatch calendar methods to avoid live network calls.
- Snapshot ICS after normalizing volatile fields (e.g., `DTSTAMP`).

## PRs

- Keep PRs focused and include a short rationale and test notes.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
