# GitHub Codespaces Setup Guide

This project is fully configured to run in GitHub Codespaces, providing a complete cloud-based development environment with zero local setup required.

## 🚀 Getting Started

### 1. Open in Codespaces

**Option A: From GitHub Repository**
1. Navigate to your repository on GitHub
2. Click the green **"Code"** button
3. Select the **"Codespaces"** tab
4. Click **"Create codespace on main"**

**Option B: From VS Code**
1. Install the GitHub Codespaces extension
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Codespaces: Create New Codespace"
4. Select your repository

### 2. Initial Setup (First Time Only)

When your Codespace starts for the first time, the post-create script (`.devcontainer/post-create-codespaces.sh`) will automatically:

- ✅ Install Python 3.12 and Node.js 20
- ✅ Start PostgreSQL 17 and Redis 7 containers
- ✅ Install the backend app package + dev deps from `pyproject.toml` (`pip install -e ".[dev]"`)
- ✅ Install all frontend dependencies (`npm install`)
- ✅ Create a `.env` file from `.env.example` if one doesn't exist

**This takes about 2-3 minutes.** Watch the terminal for progress.

### 3. Configure Your Environment

Add your IGDB API credentials to the `.env` file:

```bash
IGDB_CLIENT_ID=your_actual_client_id
IGDB_CLIENT_SECRET=your_actual_client_secret
ADMIN_TOKEN=your_secure_random_token
```

**How to get IGDB credentials:**
1. Go to https://api-docs.igdb.com/#account-creation
2. Create a Twitch account (if you don't have one)
3. Register your application at https://dev.twitch.tv/console/apps
4. Copy your Client ID and Client Secret

## 🏗️ Architecture (single consolidated app)

The backend is **one App** (`app/`), not three services. A single FastAPI process
serves both the public and token-gated admin routes, and the same Python package
runs the Celery worker / beat / Alembic migrations. The 3-in-1 layout:

- `app/main.py` — FastAPI app (public + admin routes), entry: `uvicorn app.main:app`
- `app/api.py` — public routes (`/games`, `/releases`, `/genres`, `/platforms`, `/games/search`)
- `app/admin.py` — token-gated admin routes (`/admin/*`)
- `app/sync/` — IGDB sync logic + `celery_app.py` (broker/backend) + `worker.py`
- `app/db.py`, `app/models/`, `app/config.py`, `app/deps.py` — shared backend core
- `alembic/` — database migrations
- `frontend/` — React + Vite app

## ▶️ Start Development Services

Local dev runs the FastAPI/Celery processes from the checkout against Postgres/Redis
containers. Run the infra first, then each process in its own terminal:

```bash
# Terminal 0 — infrastructure (PostgreSQL + Redis)
docker compose up -d postgres redis

# Terminal 1 — backend API (public + admin on one process)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Celery worker (processes IGDB sync tasks)
celery -A app.sync.celery_app worker --loglevel=info

# Terminal 3 — Celery beat (scheduled syncs)
celery -A app.sync.celery_app beat --loglevel=info

# Terminal 4 — frontend dev server
cd frontend && npm run dev
```

To run the **entire stack in Docker** instead (web + worker + beat + frontend, with
automatic migrations):

```bash
docker compose up --build
```

Run migrations manually: `alembic upgrade head`.

## 🔌 Access Your Application

Codespaces auto-forwards ports and provides URLs:

- **Frontend:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000` — Swagger UI at `/docs`
- **PostgreSQL:** port `5432` (db `gamecalendar`, user `gameuser`, pass `gamepass`)
- **Redis:** port `6379`

## 🗺️ API surface

**Public** (no auth):
- `GET /health` — DB + Redis liveness
- `GET /games`, `GET /games/{id}`, `GET /games/search?q=...`
- `GET /releases` — the release calendar
- `GET /genres`, `GET /platforms`

**Admin** (token-gated, `Authorization: Bearer $ADMIN_TOKEN`):
- `GET /admin/stats/overview`, `GET /admin/stats/database`
- `GET /admin/cache/stats`, `DELETE /admin/cache/clear`
- `POST /admin/sync/games`, `POST /admin/sync/games/{igdb_id}` — enqueue IGDB sync
- `GET /admin/data/games/recent`, `GET /admin/data/games/problematic`
- `POST /admin/maintenance/cleanup`

## ✅ Running Code Quality Checks

```bash
ruff check app tests        # CI lints `app tests` (matches .github/workflows/ci.yml)
ruff format --check app tests
mypy app                    # type checking (dev dep in pyproject)
bandit -r app               # security scan (dev dep in pyproject)
```

**Tests:** the EU release-date rule lives in `app/sync/igdb_client.py` and is verified by
`python tests/test_release_date_rule.py` (a standalone PASS/FAIL self-check that runs
without pytest). Run it with the project venv:

```bash
.venv/bin/python tests/test_release_date_rule.py
```

## 🔧 Common Tasks

**Reset database:**
```bash
docker compose down -v && docker compose up -d postgres redis && alembic upgrade head
```

**Install backend deps:** `pip install -e ".[dev]"` (from repo root)

**Frontend deps:** `cd frontend && npm install`

**View logs:** `docker compose logs -f`

## 🔐 Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres DSN (default `postgresql://gameuser:***@postgres:5432/gamecalendar`) |
| `REDIS_URL` | Redis URL used for cache **and** the Celery broker/backend (single URL) |
| `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` | IGDB API credentials for sync |
| `ADMIN_TOKEN` | Bearer token gating the `/admin/*` routes |

## 🆘 Getting Help

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) — detailed setup instructions
- [CONTEXT.md](./CONTEXT.md) — glossary and architecture context
- [docs/](./docs) — architecture decision records (ADRs) under `docs/adr/`
- `docker compose ps` / `docker compose logs -f` — inspect running services

## 🎮 Happy Coding!