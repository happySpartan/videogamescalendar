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
[ ] IGDB live sync proven against real credentials           →  works (see below)
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
- **Python 3.14** (`requires-python>=3.14`, `.python-version`, CI, Docker 3.14-slim): the
  2023-pinned binary deps that had no cp314 wheels (asyncpg 0.29, psycopg2-binary 2.9.9,
  pydantic 2.5) and the runtime-incompatible sqlalchemy 2.0.23 are bumped so a plain
  `pip install -e ".[dev]"` works on 3.14. Verified on a real CPython 3.14.7: quiet wheel
  install (+ import of all binary deps incl. greenlet/uvloop), ruff + mypy clean, and all 7
  ADR-0002 release-date checks pass.
- **Live IGDB sync** proven end-to-end against real Codespace-secret credentials: a manual
  full sync (`POST /admin/sync/games`, `full_sync=true`) pulled **92 upcoming games** across
  Aug–Dec 2026 (all with canonical EU/WW dates from real IGDB data) and the calendar
  (`GET /releases`) serves them. This surfaced and fixed several real-API integration bugs;
  see next section.

## Outstanding work

### 1. ~~Restrict CORS (before exposing the API)~~ — DONE

`CORS_ORIGINS` is now wired end-to-end (default `*`, unchanged for local dev):
- `app/main.py` reads `settings.CORS_ORIGINS` (replaces the hardcoded `["*"]` / `TODO`).
- `docker-compose.yml` forwards `${CORS_ORIGINS:-*}` to the app service.
- `.env.example` documents the var; `docs/DEPLOY.md` §6.2 updated to say "set `CORS_ORIGINS` to
  the real frontend origin before exposing the API publicly", e.g.
  `CORS_ORIGINS=https://calendar.example.com` (comma-separated for multiple).

### 2. ~~Set the real frontend → API URL before VPS build~~ — DONE

`VITE_GAME_API_URL` now actually reaches the Vite build. Root cause was twofold — both fixed:
- **Stale local env shadowed it.** A leftover `frontend/.env` (`VITE_API_URL=http://localhost:5050`)
  was copied into the image by `COPY . .` and `client.ts` read `VITE_API_URL` **first**, so the
  deployment URL never took effect (the bundle baked `:5050`). Removed the stale `.env` and added
  `frontend/.dockerignore` excluding `.env*` (keep `.env.example` only) so local env files can't
  be baked into the bundle.
- **Build arg now wired through.** `frontend/Dockerfile` declares `ARG VITE_GAME_API_URL`
  (default `http://localhost:8000`) and sets it as `ENV` before `npm run build`;
  `docker-compose.yml` passes it via `build.args` (`${VITE_GAME_API_URL:-http://localhost:8000}`),
  replacing the ineffective runtime `environment:` block.
- `client.ts` prioritizes `VITE_GAME_API_URL`, keeps `VITE_API_URL` as a backward-compat alias.
- `.env.example` (root + frontend), README env table, and `docs/DEPLOY.md` §6.1 document setting
  it to the real public API URL (`VITE_GAME_API_URL=https://api.calendar.example.com`) before
  `docker compose up -d --build`.

Verified: a build with the arg set bakes the URL (`api.TEST.example.com`) into the bundle and
`:5050` is gone; a default build (no arg) falls back to `http://localhost:8000`.

### 3. Actually deploy to the VPS

`docs/DEPLOY.md` is a complete runbook (Docker install → compose up → TLS via Caddy/nginx →
backups → rolling update), but no VPS has been provisioned. This is the main remaining
epic. Steps: provision box, install Docker, clone repo, set `.env` (`IGDB_CLIENT_ID` /
`IGDB_CLIENT_SECRET` / `ADMIN_TOKEN`), `docker compose up -d --build`, verify `/health` and
`/releases`, add TLS fronting.

### 4. ~~Prove the live IGDB sync end-to-end~~ — DONE

The sync pipeline is implemented and CI can run it with real secrets, but it has not yet been
confirmed against actual IGDB credentials. When credentials are available, trigger a manual
sync (`POST /admin/sync/games` with `{"full_sync": true}`) and confirm rows populate.

Done against real Codespace-secret credentials — see the "Live IGDB sync" entry above and the
bug-fix log below.

### 5. Security hardening (when reaching production)

- Keep `/admin/*` off the public reverse proxy (or add auth in front of it).
- Rotate/use the `ADMIN_TOKEN` from `.env`; never bake it into the frontend build.
- Confirm `.env` files are gitignored (do not commit `IGDB_CLIENT_SECRET` / `ADMIN_TOKEN`).

## Bug fixes: live IGDB integration (from the end-to-end proof)

Fixes required to make the sync work against the real API (all green: ruff + mypy + 7/7
ADR-0002 checks):

- **IGDB v4 `release_dates` field is `release_region`, not `region`.** The old code read
  `region`, which always came back `None`, so `select_release_date` returned `None` and every
  game collapsed to **TBA**. Switched `RELEASE_DATE_FIELDS` and the selector to `release_region`
  (mirrored in the unit test).
- **Drop `game_localizations.language.name`** — IGDB rejects it as an invalid field on the
  `games` endpoint (the API refused the whole query). Removed from `GAME_FIELDS`; the rest of
  the localization shape is unchanged.
- **`companies.start_date` widened INT4 → BIGINT.** IGDB stores full Unix epochs, negative for
  pre-1970 foundations (Nintendo 1889 → negative epoch overflows INT4). New migration
  `2e9c41fbb2a7`; model `Column(Integer)` → `Column(BigInteger)`.
- **`worker.py` session-scoped dedup cache in `_lookup_or_create`.** With SQLAlchemy's batched
  (`insertmanyvalues`) flush, a just-added (not-yet-committed) company/franchise wasn't visible
  to a follow-up `query().filter_by().first()`, so two games referencing the same entity each
  inserted a row → unique `igdb_id` violation. A cache keyed by `(model, igdb_id)` reuses the
  in-flight object. Also added a same-instance `_add_unique` guard when appending to
  many-to-many collections (a studio appearing in several involved-company roles no longer emits
  a duplicate association row).
- **`app/api.py`**: `/games/search` must be declared **before** `/games/{game_id}` (FastAPI
  matches in registration order; the int `{game_id}` route would swallow `search`), `regions`
  detail field is `identifier` (not `code`), and `/genres` + `/platforms` now eager-load
  `games` so `game_count` doesn't N+1.
- **`app/main.py`**: Redis liveness client close changed `aclose()` → `close()` — the
  runtime-available asyncio-redis method on this stack (the earlier `aclose` call broke the
  app/lifespan teardown).

## Backlog carried over from the (retired) architecture plan

These are the only not-done items from `.hermes/plans/2026-08-11_videogame-calendar-architecture.md`
(the rest of the plan is complete; the file was deleted). Tracked here so the work is not lost.

### 6. ~~Commit + push the pending Dependabot config~~ — DONE

`.github/dependabot.yml` is committed — the comment fix removing the stale
`requirements-migrations.txt` reference, pinned to the three **current** manifests (pip @ `/`,
npm @ `/frontend`, github-actions @ `/`), so it no longer auto-generates runs against the
deleted `services/*` dirs. (Still needs a `git push` to reach GitHub.)

### 7. ~~Decide on the Dependabot vulnerabilities~~ — DONE

OSV audit of the **current** pins (post-3.14 bump) found 3 packages with actionable
advisories — `fastapi==0.104.1` (CVE-2024-24762, high DoS), `python-multipart==0.0.6`
(18 advisories, high DoS), and `python-dotenv==1.0.0` (CVE-2026-28684). All bumped:
`fastapi==0.141.1`, `python-multipart==0.0.32`, `python-dotenv==1.2.2`. The app exposes no
form/file/multipart routes, so the FastAPI/multipart class of issue was not exploitable here.
Everything else at current pins is clean (asyncpg, psycopg2, pydantic, sqlalchemy, alembic,
celery, redis, httpx, kombu, uvicorn, dev tools). Verified on real CPython 3.14.7: install,
app boot (/health), ruff + mypy clean, all ADR-0002 checks pass.

### 8. Browser-test the frontend against a running API

The offline runtime gap is covered by CI (`/releases`, `/genres`, `/platforms` smoke tests on a
real Postgres/Redis), but no human/automated browser test of the calendar UI rendering + filters
+ deep-link `/game/:id` has ever run locally. Run `npm run dev` against the backend and verify the
calendar month view, filtering, and navigation.

### 9. Provision the actual VPS

`docs/DEPLOY.md` is a complete runbook (Docker install → compose up → TLS → backups → rolling
update), but the VPS itself has **not** been stood up. This is the main remaining epic (ties into
item 3 above).

## ~~Investigate the concurrent "uncommitted" working-tree edits~~ — DONE

All reviewed and committed as two coherent, deliberately-scoped commits:

- **d410e560** — the Python 3.14 bump: dep pins to cp314-compatible releases +
  the `worker.py` `CursorResult` cast + `app/db.py` `Generator[Session]` modernization.
- **2755f562** — Dependabot advisory fix: fastapi / python-multipart / python-dotenv bumps.

The `.devcontainer/*` changes reviewed here turned out to be part of the same 3.14 work
(devcontainer.json → `image: python:3.14-bookworm`, docker-in-docker feature, ruff/mypy/bandit
in the post-create scripts, extension cleanup). The three deleted `.devcontainer` files —
`Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml` — were orphaned once devcontainer.json
used the base image directly (nothing references them). All staged with `git add <specific paths>`
and committed; never `git add -A`.