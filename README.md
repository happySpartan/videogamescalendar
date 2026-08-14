# Videogame Calendar

A monthly calendar of EU video-game releases. The core value is **"what comes
out, and when"**, EU-centric, backed by a single consolidated FastAPI service,
PostgreSQL, Redis, and a Celery worker that syncs from IGDB.

This README is the single entry point — it consolidates the previous split of
setup/quickstart/devcontainer/documentation guides into one place. Architecture
and domain vocabulary live separately (see [Docs](#docs)).

---

## Architecture

The backend is **one `app/` package** running every role (ADR-0001). There are
**no** `services/{game-api,admin-api,data-sync}` microservices anymore — that
layout was consolidated away. One FastAPI process serves both the public and the
token-gated admin routes; the same Python package runs the Celery worker/beat
and Alembic migrations.

```
Frontend (React/Vite) ──► FastAPI app (app.main) ──► PostgreSQL
                                  │   ▲
                                  ▼   │
                             Redis Cache
                                  ▲
                                  │
                    Celery worker/beat (app.sync)
```

Per **ADR-0003**, production deploys as a **Docker Compose stack on a single
small VPS** (not Azure). See [`docs/DEPLOY.md`](docs/DEPLOY.md) for the runbook.

### Technology stack

- **Frontend**: React 18, TypeScript, Vite, React Router, TanStack Query
  (typed API client at `frontend/src/api/client.ts`)
- **Backend**: FastAPI (async), SQLAlchemy ORM, Pydantic v2
- **Database**: PostgreSQL 17 with `pg_trgm` trigram search
- **Cache / broker**: Redis 7 — a **single `REDIS_URL`** serves cache *and* the
  Celery broker/backend
- **Background jobs**: Celery (worker + beat)
- **Migrations**: Alembic
- **Containerization**: Docker & Docker Compose

## Project structure

```
videogamecalendar/
├── app/                    # The consolidated backend package
│   ├── main.py             # FastAPI entry (public + admin), /health
│   ├── api.py              # Public routes: /games, /releases, /genres, /platforms
│   ├── admin.py            # Token-gated admin routes under /admin/*
│   ├── config.py           # Settings (DB URL, IGDB creds, admin token)
│   ├── db.py               # Database engine/session
│   ├── deps.py             # Shared dependencies (e.g. Redis client)
│   ├── models/             # SQLAlchemy models (game, genre, platform, ...)
│   └── sync/               # IGDB sync logic, Celery app + worker
├── alembic/                # Database migrations
├── frontend/               # React application (port 3000)
├── tests/                  # Backend tests (ADR-0002 release-date rule)
├── docs/                   # ADRs + deploy runbook
├── Dockerfile              # One image for web/worker/beat/migrate
├── pyproject.toml          # All backend deps (+ ruff/mypy/bandit dev extras)
└── docker-compose.yml      # postgres, redis, migrate, app, worker, beat, frontend
```

## Quick start

### Prerequisites

- Docker and Docker Compose (`docker compose`, the V2 plugin)
- Python 3.14, Node.js 20 (only for local, non-Docker dev)

### Fastest path — everything in Docker

```bash
cd videogamescalendar
cp .env.example .env        # then set IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, ADMIN_TOKEN
docker compose up --build
```

This builds the single app image and the frontend image, runs the `migrate`
service (`alembic upgrade head`) to completion, then starts `app`, `worker`, and
`beat`. Access:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 — Swagger UI at `/docs`
- PostgreSQL: port `5432` (db `gamecalendar`, user `gameuser`, pass `gamepass`)
- Redis: port `6379`

### Local development (non-Docker)

Compose up the infrastructure, then run each process from the checkout:

```bash
# Terminal 0 — infrastructure (PostgreSQL + Redis)
docker compose up -d postgres redis

# Terminal 1 — backend (public + admin on one process)
pip install -e ".[dev]"        # one-time; installs app + ruff/mypy/bandit
alembic upgrade head           # one-time migration
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Celery worker (processes IGDB sync tasks)
celery -A app.sync.celery_app worker --loglevel=info

# Terminal 3 — Celery beat (scheduled syncs)
celery -A app.sync.celery_app beat --loglevel=info

# Terminal 4 — frontend dev server
cd frontend && npm install && npm run dev
```

> **Windows/PowerShell note:** use the root `.venv` (`.\\.venv\\Scripts\\Activate.ps1`)
> then the exact same commands. There is only **one** venv for the whole project —
> the old per-service `setup-venv.ps1` and `requirements-migrations.txt` are gone.

### Codespaces / dev containers

The repo includes a `.devcontainer/` that is fully wired for GitHub
Codespaces: the post-create script installs Python + Node deps, starts
Postgres/Redis containers, and creates `.env` from `.env.example`. IGDB
credentials are read automatically from the `IGDB_CLIENT_ID` and
`IGDB_CLIENT_SECRET` **Codespace secrets** (set them in Settings → Secrets →
Codespaces) and written into `.env` on container start. See
[`.devcontainer/README.md`](.devcontainer/README.md).

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres DSN (default `postgresql://gameuser:gamepass@postgres:5432/gamecalendar`) |
| `REDIS_URL` | Redis URL for cache **and** the Celery broker/backend (single URL) |
| `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` | IGDB API credentials for sync (get from https://api-docs.igdb.com) |
| `ADMIN_TOKEN` | Bearer token gating the `/admin/*` routes (`openssl rand -hex 32`) |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins (default `*`; set to your real origin in prod) |
| `VITE_GAME_API_URL` | Public API URL the browser calls (frontend **build arg**; default `http://localhost:8000`) |

`NODE_ENV`/`PYTHON_ENV` are development conveniences.

## API surface

**Public** (no auth)

- `GET /health` — DB + Redis liveness
- `GET /games`, `GET /games/{id}` — listing + detail
- `GET /games/search?q=...` — trigram full-text search
- `GET /releases?from=YYYY-MM-DD&to=YYYY-MM-DD` — the release calendar (a month
  window; the frontend buckets by day client-side). Uses the EU release-date rule
  (`docs/adr/0002`)
- `GET /genres`, `GET /platforms` — reference data

**Admin** (token-gated, `Authorization: Bearer <ADMIN_TOKEN>`)

- `GET /admin/stats/overview`, `GET /admin/stats/database`
- `GET /admin/cache/stats`, `DELETE /admin/cache/clear`
- `POST /admin/sync/games` (full or delta), `POST /admin/sync/games/{igdb_id}`
- `GET /admin/data/games/recent`, `GET /admin/data/games/problematic`
- `POST /admin/maintenance/cleanup`

## Background jobs (Celery)

Scheduled on the single Redis URL:

| Schedule | Task | When |
|----------|------|------|
| Hourly delta sync | `data_sync.sync_games` (full_sync=False) | every hour at minute 0 |
| Daily full sync | `data_sync.sync_games` (full_sync=True) | every day at 02:00 UTC |
| Weekly cleanup | `data_sync.cleanup_old_data` | Sunday at 03:00 UTC |

The **EU release-date rule** (`app/sync/igdb_client.py`, ADR-0002) selects the
canonical date: IGDB region Europe → Worldwide → TBA, label-aware rather than
blind-earliest.

## Development

### Quality checks (matches CI scope)

```bash
ruff check app tests
ruff format --check app tests
mypy app
bandit -r app
```

### Tests

The EU release-date rule is unit-verified by a **standalone self-check** (no
pytest required):

```bash
python tests/test_release_date_rule.py
```

### Continuous integration

`.github/workflows/ci.yml` runs offline quality gates (ruff/mypy/tsc/build) plus
a Docker-build job, plus a **runtime job** that applies Alembic migrations to a
real Postgres service container, boots the API, and smoke-tests the calendar
endpoints. A live IGDB sync runs only when real credentials are present as
repository secrets.

### Database features

- `pg_trgm` GIN indexes for fuzzy text search; `uuid-ossp` for UUIDs. Both are
  created idempotently by the Alembic migrations (`alembic/versions/`).
- Main tables (SQLAlchemy models in `app/models/`): `games`, `genres`,
  `platforms`, `companies`, `franchises`, `languages`, `regions` (+ associations).

### Performance & caching

| Endpoint | Cache TTL |
|----------|-----------|
| `/games` (list), `/releases` | 300s (5 min) |
| `/games/{id}`, `/games/search` | 600s (10 min) |
| `/genres`, `/platforms` | 1800s (30 min) |

## Common operations

```bash
docker compose ps                        # running services
docker compose logs -f app worker beat   # watch sync + scheduler
docker compose exec postgres psql -U gameuser -d gamecalendar -c "select count(*) from games;"
celery -A app.sync.celery_app inspect ping   # check workers

# Reset database
docker compose down -v && docker compose up -d postgres redis && alembic upgrade head
```

## Docs

- **Domain glossary** (what things *are*): [`CONTEXT.md`](CONTEXT.md) — frozen,
  implementation-free vocabulary.
- **Architecture decisions** (ADRs): [`docs/adr/`](docs/adr/)
  - `0001` — consolidate to a single service + package
  - `0002` — EU-centric release date with Worldwide fallback
  - `0003` — production deploy on a single VPS with Docker Compose
- **Deploy runbook**: [`docs/DEPLOY.md`](docs/DEPLOY.md) — VPS setup, TLS,
  backups, updates.
- **Dev container**: [`.devcontainer/README.md`](.devcontainer/README.md)
- **Progress & outstanding work**: [`docs/PROGRESS.md`](docs/PROGRESS.md) —
  in-flight status, open tasks, production-readiness gaps.

## Contributing

1. Create a feature branch
2. Implement changes with tests
3. Run quality checks (`ruff`, `mypy`, `bandit` on `app tests`)
4. Open a pull request

Depends on: `pyproject.toml` (all Python deps — there are no `requirements*.txt`),
`frontend/package.json`.