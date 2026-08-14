# Progress & Outstanding Work

Living status of the Video Game Calendar project: what is currently implemented and
working, and what still needs doing. This is the place for **in-flight / not-yet-done**
work. For how the finished system fits together, see [README](../README.md).

> This file deliberately lives apart from the "how it is" docs. Facts move into
> [README](../README.md) / [`CONTEXT.md`](../CONTEXT.md) / ADRs once they are done and stable.

## Current status

The repo is on a **single consolidated backend** (ADR-0001), the **EU release-date rule**
(ADR-0002) is implemented and unit-verified, and CI runs a real Postgres/Redis runtime
pass. Production deploy targets a **single VPS with Docker Compose** (ADR-0003) — the
runbook exists and CI is green, but the VPS has **not been stood up yet**.

```md
[ ] CI green (ruff/mypy/tsc/build + Docker + runtime pass)   →  works (see below)
[ ] ADR-0002 release-date rule implemented + tested          →  works
[ ] VPS deploy (ADR-0003) actually performed                 →  NOT DONE
[ ] IGDB live sync proven against real credentials           →  gated on secrets
```

## Implemented & verified

- **Single `app/` package** (ADR-0001): one FastAPI process serves public + admin routes
  (`uvicorn app.main:app`); same package runs Celery worker/beat; Alembic migrations.
- **EU release-date rule** (ADR-0002) in `app/sync/igdb_client.py`: IGDB region Europe →
  Worldwide → TBA, label-aware rather than blind-earliest. Unit-verified by the standalone
  self-check `python tests/test_release_date_rule.py` (passes without pytest).
- **Frontend** wired to the typed API client (`frontend/src/api/client.ts`) via React Router
  + TanStack Query; `/releases` powers the calendar.
- **CI** (`.github/workflows/ci.yml`): offline quality gates (ruff/mypy/tsc/build), a
  Docker-build job, and a runtime job that applies Alembic migrations to a real Postgres
  service container, boots the API, and smoke-tests `/releases`, `/genres`, `/platforms`.
  A live IGDB sync runs only when real credentials are present as repo secrets.

## Outstanding work

### 1. Restrict CORS (before exposing the API)

`app/main.py:69` currently sets `allow_origins=["*"]` (marked `TODO`). Before the API goes
publicly reachable, restrict it to the real frontend origin(s), e.g.
`allow_origins=["https://calendar.example.com"]`. `CORS_ORIGINS` is already configurable via
env (`app/config.py`).

### 2. Set the real frontend → API URL before VPS build

`docker-compose.yml` bakes `VITE_GAME_API_URL=http://localhost:8000` into the frontend build.
On the VPS the browser calls the API directly, so set this to the public API URL (e.g.
`https://api.calendar.example.com`) in the `frontend` service env **before** building. See
`docs/DEPLOY.md` §6.

### 3. Actually deploy to the VPS

`docs/DEPLOY.md` is a complete runbook (Docker install → compose up → TLS via Caddy/nginx →
backups → rolling update), but no VPS has been provisioned. This is the main remaining
epic. Steps: provision box, install Docker, clone repo, set `.env` (`IGDB_CLIENT_ID` /
`IGDB_CLIENT_SECRET` / `ADMIN_TOKEN`), `docker compose up -d --build`, verify `/health` and
`/releases`, add TLS fronting.

### 4. Prove the live IGDB sync end-to-end

The sync pipeline is implemented and CI can run it with real secrets, but it has not yet been
confirmed against actual IGDB credentials. When credentials are available, trigger a manual
sync (`POST /admin/sync/games` with `{"full_sync": true}`) and confirm rows populate.

### 5. Security hardening (when reaching production)

- Keep `/admin/*` off the public reverse proxy (or add auth in front of it).
- Rotate/use the `ADMIN_TOKEN` from `.env`; never bake it into the frontend build.
- Confirm `.env` files are gitignored (do not commit `IGDB_CLIENT_SECRET` / `ADMIN_TOKEN`).