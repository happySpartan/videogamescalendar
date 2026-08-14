# Progress & Outstanding Work

Living status of the Video Game Calendar project: what is currently implemented and
working, and what still needs doing. This is the place for **in-flight / not-yet-done**
work. For how the finished system fits together, see [README](../README.md).

> This file deliberately lives apart from the "how it is" docs. Facts move into
> [README](../README.md) / [`CONTEXT.md`](../CONTEXT.md) / ADRs once they are done and stable.
> The one-shot architecture plan (`.hermes/plans/2026-08-11_…md`) is **complete and retired**;
> its leftover open items are folded into the Backlog section below.

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

## Backlog carried over from the (retired) architecture plan

These are the only not-done items from `.hermes/plans/2026-08-11_videogame-calendar-architecture.md`
(the rest of the plan is complete; the file was deleted). Tracked here so the work is not lost.

### 6. Commit + push the pending Dependabot config

`.github/dependabot.yml` is still an uncommitted working-tree edit (a comment fix removing the
stale `requirements-migrations.txt` reference). It also pins Dependabot to the three **current**
manifests (pip @ `/`, npm @ `/frontend`, github-actions @ `/`) so it stops auto-generating runs
against the deleted `services/*` dirs. Commit + push to take effect.

### 7. Decide on the 36 Dependabot vulnerabilities (18 high)

GitHub reports 36 vulnerable dependencies (18 high) on the default branch. Needs a decision:
auto-update (Dependabot PRs) vs a manual bump, and a plan for CI to gate on them.

### 8. Browser-test the frontend against a running API

The offline runtime gap is covered by CI (`/releases`, `/genres`, `/platforms` smoke tests on a
real Postgres/Redis), but no human/automated browser test of the calendar UI rendering + filters
+ deep-link `/game/:id` has ever run locally. Run `npm run dev` against the backend and verify the
calendar month view, filtering, and navigation.

### 9. Provision the actual VPS

`docs/DEPLOY.md` is a complete runbook (Docker install → compose up → TLS → backups → rolling
update), but the VPS itself has **not** been stood up. This is the main remaining epic (ties into
item 3 above).

## Investigate the 11 uncommitted "concurrent" working-tree edits

Not from the doc-cleanup sessions — these files were modified by some other process/edit and are
still **unstaged and uncommitted**. Before committing them, review each diff to confirm intent and
avoid another silent sweep like `bd467233`:

- `.devcontainer/Dockerfile`, `.devcontainer/devcontainer.json`,
  `.devcontainer/post-create.sh`, `.devcontainer/post-create-codespaces.sh`,
  `.devcontainer/README.md`
- `.github/workflows/ci.yml`
- `.github/dependabot.yml` (ties into item 6 above)
- `Dockerfile`
- `app/db.py`
- `pyproject.toml`
- `.python-version`

Determine whether each change is (a) a deliberate local tweak to keep, (b) a leftover of an
aborted edit to revert, or (c) something that should also land in the ADRs/README. Commit the
intended ones as a separate, clearly-scoped commit (`git add <specific paths>`, then
`git commit --no-gpg-sign`); never `git add -A`.