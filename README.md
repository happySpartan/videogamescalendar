# Videogame Calendar

A monthly calendar of EU video-game releases. The core value is **"what comes
out, and when"**, EU-centric, backed by a single consolidated FastAPI service,
PostgreSQL, Redis, and a Celery worker that syncs from IGDB.

This README is the single entry point and consolidates the previous split of
setup/quickstart/devcontainer/deploy/domain documentation into one place.

---

## Domain glossary

Pure domain vocabulary, implementation-free — the "what things ARE" of the
product. Updated the moment a term resolves.

- **Videogame Calendar** — what the product IS: a web app that shows a monthly
  calendar of video-game releases. The core value is "what comes out, and when",
  EU-centric. _Avoid_: "game calendar", "release tracker" as interchangeable
  synonyms — the calendar view is the product, the underlying data is a set of
  releases.

- **Game** — a title in the catalog (e.g. "Zelda: Tears of the Kingdom"). Has a
  name, is associated to genres, platforms, a studio/company and optionally a
  franchise.

- **Release** — a Game's dated calendar event. One Game has exactly ONE canonical
  Release shown on the calendar, on one day (see **EU release date**). Not to be
  confused with the many raw dates IGDB may hold for a game — the sync collapses
  those into one.

- **EU release date** — the single canonical date a Game appears on the calendar.
  Defined by the **release-date rule**: prefer an IGDB entry whose region is Europe
  (1); among several EU dates prefer the one whose human-readable label/note matches
  the announced date, else the earliest. Fall back to the Worldwide (8) region under
  the same rule. With no dated entry at all, the Game is **TBA**.
  _Avoid_: "release_date"/"first_release_date" as two different columns — there is
  ONE date.

- **Worldwide (IGDB region 8)** — the fallback region used when a Game has no
  Europe-dated IGDB entry, so well-known titles aren't marked TBA just for lacking
  an EU row. IGDB region codes: 1=Europe, 8=Worldwide, 2=NA, 3=AU, 5=JP.

- **TBA** — a Game with no usable date under the release-date rule. Shown as "TBA",
  kept in the catalog, but NOT placed on the calendar grid until it acquires a date.

- **Released / Upcoming** — derived status of a Game from its **EU release date**:
  released = date ≤ now, upcoming = date > now. Derived, never stored as separate
  columns.

- **Genre / Platform** — the two filter dimensions of the catalog. A Game has
  many-to-many relationships to both. Used by the calendar's filter bar.

- **Studio (Company)** — the maker of a Game. A Game belongs to a Company;
  optionally a Game belongs to one **Franchise** (a series identity spanning
  multiple Games).

- **Sync** — the recurring process that pulls data from **IGDB** into the catalog and
  computes each Game's **EU release date**. Runs on a schedule (the **sync cadence**),
  and can be triggered manually from **Admin**.

- **Sync cadence** — how often the **Sync** runs. Current choice: keep the existing
  cadence (hourly delta, daily full, weekly cleanup — see Background jobs).

- **IGDB** — the external data source (release dates, genres, platforms, companies,
  franchises). The catalog is populated entirely from it; the app holds no
  hand-entered game data.

- **Admin** — the token-gated operations surface for things like triggering a manual
  **Sync**. v1 has no end-user accounts; only this admin ops surface exists, gated by
  a token.

- **Calendar** — the product's primary view: a month grid of **Releases** bucketed by
  day. Loading a month is one request for that month's window; days are grouped
  client-side. _Avoid_: using "calendar" to mean the underlying release data — the
  data is **Releases**.

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

Per **ADR-0004**, the public site is a **static build on GitHub Pages**, refreshed
from IGDB by a scheduled workflow. See [Deployment](#deployment-static-site-on-github-pages).
The full stack can still run on a VPS with Docker Compose (ADR-0003).

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
├── docs/                   # ADRs + progress/outstanding-work status
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

The repo includes a `.devcontainer/` fully wired for **GitHub Codespaces** — the
post-create script installs Python + Node deps, starts Postgres/Redis containers,
and creates `.env` from `.env.example`. There is **one consolidated `app/` package**
(a single FastAPI process for public + admin routes, plus the Celery worker/beat and
Alembic migrations) running alongside the frontend.

#### Included toolchain

- **Python 3.14** with the app package + dev deps installed from `pyproject.toml`
- **uv** — fast Python package/venv manager (preferred over raw pip here)
- **Node.js 20** for the React/Vite frontend
- **PostgreSQL client** (`psql`, `pg_dump`) and **Redis CLI** (`redis-cli`)
- **jq**, **Docker-in-Docker**, and the **GitHub CLI** (`gh`)

#### Services

| Service | Purpose | Port |
|---------|---------|------|
| PostgreSQL 17 | main database | 5432 |
| Redis 7 | cache + Celery broker/backend | 6379 |
| Backend | one FastAPI process (public + admin) | 8000 |
| Frontend | Vite dev server | 3000 |

#### IGDB credentials via Codespace secrets (recommended)

Set these as **GitHub Codespace secrets** (repo-level: Settings → Secrets and
variables → Codespaces, or user-level for use across repos). They are injected as
environment variables at container start and written into `.env` by the post-create
script automatically:

- `IGDB_CLIENT_ID`
- `IGDB_CLIENT_SECRET`
- `ADMIN_TOKEN` (optional but recommended)

> Requires a container **rebuild** after adding/updating a secret — Codespace
> secrets are only injected into new container sessions, not running ones.

If the secrets are present at build time you'll see "IGDB credentials populated from
Codespace secrets." Otherwise `.env` keeps placeholders and can be edited manually.

#### Using it

**Codespaces (recommended):** open the repo with "Code" → "Codespaces" → "New
codespace", wait ~2–3 minutes for the post-create setup, add IGDB credentials, and
start developing.

**Local VS Code with Dev Containers:** install [Docker Desktop](https://www.docker.com/products/docker-desktop)
and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers),
then:

```bash
git clone https://github.com/happySpartan/videogamescalendar.git
cd videogamescalendar
cp .env.example .env   # then add your IGDB credentials
code .
```

When prompted, click "Reopen in Container" (or `F1` → "Dev Containers: Reopen in
Container") and wait for the post-create script to complete.

#### Dev container troubleshooting

- **Container won't start** — make sure Docker Desktop is running; try `F1` → "Dev
  Containers: Rebuild Container".
- **Database connection issues** — check `pg_isready -h postgres -U gameuser -d gamecalendar`,
  or `docker compose logs postgres`.
- **Port conflicts** — ensure 3000, 5432, 6379, and 8000 are free.
- **Node modules issues** — `cd frontend && rm -rf node_modules package-lock.json && npm install`.
- **Python dependency issues** — `pip install -e ".[dev]" --force-reinstall`.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres DSN (default `postgresql://gameuser:***@postgres:5432/gamecalendar`) |
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
python tests/test_static_export.py   # ADR-0004 static export
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

---

## Deployment (static site on GitHub Pages)

The public site is a **static build on GitHub Pages** (ADR-0004) — no server, database or
Redis in production. `.github/workflows/pages.yml` runs every 6 hours (and on push to
`main`, or manually via **Actions → Static site (GitHub Pages) → Run workflow**):

1. `python -m app.static_export --out frontend/public/data` pulls releases from IGDB
   (2 months back, 12 months ahead) with the EU release-date rule and writes JSON:
   `releases/YYYY-MM.json`, `games/<igdb_id>.json`, `genres.json`, `platforms.json`,
   `meta.json`.
2. The frontend is built with `VITE_DATA_MODE=static`, so it reads those files instead of
   the API (`VITE_BASE_PATH` sets the sub-path when served from `<user>.github.io/<repo>/`).
3. `frontend/dist` is deployed to Pages; `404.html` is a copy of `index.html` so deep links
   like `/game/123` work.

One-time setup:

- **Settings → Secrets and variables → Actions**: `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET`.
- **Settings → Pages → Build and deployment → Source: GitHub Actions**.
- Custom domain: **Settings → Pages → Custom domain**, then a DNS `CNAME` record
  (`www` → `<user>.github.io`) or `A` records for an apex domain; tick **Enforce HTTPS**.

Try static mode locally:

```bash
python -m app.static_export --out frontend/public/data   # needs IGDB creds in env
cd frontend && VITE_DATA_MODE=static npm run dev
```

## Deployment (VPS with Docker Compose)

> Alternative to the static site above, for when a live API is needed (ADR-0003).

Deployment target per **ADR-0003**: one always-on small VPS (e.g. OVH) running the whole
system as a Docker Compose stack. No managed autoscaling; the single box pays for idle,
which is the right trade-off at this scale. There is **no Azure deployment** — the obsolete
Azure workflow was removed.

> This runbook matches the current `docker-compose.yml` (one app image, five roles:
> `migrate`, `app`, `worker`, `beat` — plus `postgres`, `redis`, `frontend`).

### Architecture being deployed

| Compose service | Role | Talks on |
|-----------------|------|----------|
| `postgres`      | PostgreSQL 17 | 5432 (internal) |
| `redis`         | Redis 7 (cache + Celery broker/backend) | 6379 (internal) |
| `migrate`       | runs `alembic upgrade head`, exits 0 | – (one-shot) |
| `app`           | FastAPI — public + admin routes | **8000** |
| `worker`        | Celery worker — consumes IGDB sync tasks | – |
| `beat`          | Celery beat — hourly delta / daily 2am / weekly cleanup | – |
| `frontend`      | built React app served by nginx | **80 → 3000** (dev), port 80 in prod |

`app`/`worker`/`beat` start only **after** `migrate` completes successfully
(`service_completed_successfully`), so a fresh database is migrated automatically.

### 1. Prerequisites

- A VPS (1–2 vCPU, 2–4 GB RAM is plenty): any recent Ubuntu/Debian.
- SSH access (as root or a sudo user).
- Docker Engine **with the compose plugin** (`docker compose`, not the legacy `docker-compose`).
- A domain (recommended) and a way to issue TLS (Caddy makes this automatic).

### 2. Install Docker on the VPS

```bash
# Official convenience script (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# re-login, then confirm
docker --version && docker compose version
```

### 3. Clone the repo and configure environment

```bash
sudo mkdir -p /opt/videogamescalendar && sudo chown "$USER":"$USER" /opt/videogamescalendar
git clone https://github.com/happySpartan/videogamescalendar.git /opt/videogamescalendar/app
cd /opt/videogamescalendar/app

cp .env.example .env
# EDIT .env — must set:
#   IGDB_CLIENT_ID=...
#   IGDB_CLIENT_SECRET=...
#   ADMIN_TOKEN=<openssl rand -hex 32>
# DATABASE_URL/REDIS_URL in compose are overridden to point at the postgres/redis
# services, so you normally leave those as-is.
```

> See `.env.example` for the full list. The backend defaults are fine for a first boot; the
> three you must set for a running product are the IGDB credentials and the admin token.

### 4. Build and start the stack

```bash
docker compose up -d --build
```

This builds the single app image and the frontend image, applies migrations via `migrate`,
then starts `app`, `worker`, and `beat`.

### 5. Verify

```bash
docker compose ps                 # all services Up/healthy
curl -fsS http://localhost:8000/health   # {"status":"healthy", database:"connected", redis:"connected"...}
curl -fsS 'http://localhost:8000/releases?from=2030-01-01&to=2030-01-31&limit=10'
docker compose logs -f app worker beat   # watch sync + scheduler activity
```

Trigger a manual sync (the worker consumes it); the admin API is token-gated:

```bash
curl -fsS -X POST http://localhost:8000/admin/sync/games \
  -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" \
  -d '{"full_sync": true}'
# then confirm rows grow
docker compose exec postgres psql -U gameuser -d gamecalendar -c "select count(*) from games;"
```

### 6. Put it behind TLS with a reverse proxy (recommended)

The API listens on `:8000` and the frontend on `:80`. For a real deployment:

- **Option A — Caddy (easiest, automatic Let's Encrypt):**

  ```caddyfile
  # /etc/caddy/Caddyfile
  calendar.example.com {
      # frontend
      handle {
          reverse_proxy localhost:80
      }
  }
  api.calendar.example.com {
      # API (public + admin)
      reverse_proxy localhost:8000
  }
  ```

- **Option B — nginx:** proxy `api.<domain>` → `localhost:8000` and `<domain>` → `localhost:80`,
  with a certbot TLS block.

#### Production-readiness gaps to close while you're here

1. **Frontend → API URL.** The frontend image bakes `VITE_GAME_API_URL` into the JS bundle at
   `npm run build` time. It is now a **build arg** (`frontend/Dockerfile`), wired through
   `docker-compose.yml` as `VITE_GAME_API_URL: ${VITE_GAME_API_URL:-http://localhost:8000}`.
   On the VPS the browser, not the server, calls the API — set `VITE_GAME_API_URL` in `.env` to
   the real public API URL (e.g. `https://api.calendar.example.com`) **before** `docker compose
   up -d --build`. Setting it at runtime (the old `environment:` block) had zero effect because
   Vite reads it during the build.
2. **CORS.** The API reads its allowed origins from the `CORS_ORIGINS` env var
   (`app/main.py` → `app/config.py`), defaulting to `*`. Before exposing the API publicly, set
   it in `.env` to your real frontend origin(s), e.g. `CORS_ORIGINS=https://calendar.example.com`
   (comma-separated for multiple). `docker-compose.yml` forwards `${CORS_ORIGINS:-*}` to the app
   service.
3. **Admin token.** The `/admin/*` routes are gated by `ADMIN_TOKEN` (env). Do **not** expose
   `/admin` through the proxy unless you add auth in front; keep it on the private interface if
   possible.
4. **Persistent data.** Both `postgres_data` and `redis_data` volumes persist via compose;
   don't `docker compose down -v` unless you intend to wipe them.

### 7. Backups

With the stack running (and preferably the app briefly stopped for a clean dump):

```bash
docker compose exec postgres pg_dump -U gameuser -d gamecalendar -Fc -f /tmp/app.dump
docker compose cp postgres:/tmp/app.dump ./backups/$(date +%F).dump
```

Store backups off-box (rsync to another host, or object storage). Redis is a cache/broker —
its data is re-derivable from IGDB, so a Redis backup is optional.

### 8. Updates (rolling deploy)

```bash
cd /opt/videogamescalendar/app
git pull
docker compose up -d --build
# migrations apply automatically via the migrate service before app/worker/beat restart
# verify:
curl -fsS http://localhost:8000/health
```

### 9. Troubleshooting

| Symptom | Likely cause / check |
|---------|----------------------|
| `/health` shows `database: disconnected` | Postgres not up/healthy: `docker compose ps`, `docker compose logs postgres` |
| Empty tables | migration didn't run: `docker compose logs migrate`; run `docker compose run --rm migrate` |
| No new games after sync | IGDB creds missing or invalid; check `docker compose logs worker`; test the OAuth token manually |
| `migrate` never completes | `docker compose logs migrate` for the Alembic error (e.g. missing `pg_trgm` — the initial migration creates it) |
| Frontend calls `localhost` | `VITE_GAME_API_URL` baked at build time — rebuild after setting the public URL (see §6.1) |

### 10. Teardown (if ever needed)

```bash
docker compose down          # keep volumes
docker compose down -v       # WIPE postgres_data + redis_data
```

---

## Docs

- **Architecture decisions** (ADRs): [`docs/adr/`](docs/adr/)
  - `0001` — consolidate to a single service + package
  - `0002` — EU-centric release date with Worldwide fallback
  - `0003` — production deploy on a single VPS with Docker Compose
- **Progress & outstanding work**: [`docs/PROGRESS.md`](docs/PROGRESS.md) — living status:
  open/in-flight tasks first, then an archive of what's done.
- **Domain glossary** and **deployment runbook**: consolidated here in this README.

## Contributing

1. Create a feature branch
2. Implement changes with tests
3. Run quality checks (`ruff`, `mypy`, `bandit` on `app tests`)
4. Open a pull request

Depends on: `pyproject.toml` (all Python deps — there are no `requirements*.txt`),
`frontend/package.json`.