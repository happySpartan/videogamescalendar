# Complete Setup Guide

> **Project layout note:** the backend is **one consolidated app** (`app/`), not three
> services. A single FastAPI process serves both public and admin routes, and the same
> package runs the Celery worker/beat plus Alembic migrations. References to the old
> `services/game-api`, `services/admin-api`, `services/data-sync` layout no longer apply —
> start processes with `uvicorn app.main:app` / `celery -A app.sync.celery_app`.

## Prerequisites

- ✅ Python 3.12 installed
- ✅ Node.js 18+ installed
- ✅ Docker or Podman installed
- ✅ Git installed

## 1. Clone & Navigate

```powershell
git clone https://github.com/happySpartan/videogamescalendar.git
cd videogamescalendar
```

## 2. Install Dependencies

```powershell
# Backend (single app package from pyproject.toml)
pip install -e ".[dev]"

# Frontend
cd frontend
npm install
cd ..
```

## 3. Setup Environment Files

```powershell
Copy-Item .env.example .env
# then edit .env and set your IGDB credentials:
#   IGDB_CLIENT_ID=your_client_id
#   IGDB_CLIENT_SECRET=your_client_secret
#   ADMIN_TOKEN=your_secure_token
```

## 4. Start Infrastructure

```powershell
# Podman
podman compose up postgres redis -d

# Docker
docker compose up postgres redis -d
```

Verify with `podman compose ps` / `docker compose ps` — postgres and redis should be "Running".

## 5. Run Migrations

```powershell
pip install -r requirements-migrations.txt   # ensure alembic is available
alembic upgrade head
```

## 6. Start the Backend

The **one** FastAPI process serves both the public API and the token-gated admin API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Start the Celery worker (and beat for scheduled syncs) in separate terminals:

```powershell
celery -A app.sync.celery_app worker --loglevel=info
celery -A app.sync.celery_app beat --loglevel=info
```

## 7. Start the Frontend

```powershell
cd frontend
npm run dev
cd ..
```

## 8. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API (public + admin):** http://localhost:8000 — Swagger UI at http://localhost:8000/docs
- **PostgreSQL:** port `5432` (db `gamecalendar`, user `gameuser`, pass `gamepass`)
- **Redis:** port `6379`

---

## Running the Full Stack in Docker

Compose runs **one app image** in five roles, with automatic migration gating:

```powershell
docker compose up --build
```

Or individual roles: `docker compose up app`, `docker compose up worker`, etc.
`migrate` runs `alembic upgrade head` to completion before `app`/`worker`/`beat` start.

---

## API Surface

**Public** (no auth)
- `GET /health` · `GET /genres` · `GET /platforms`
- `GET /games` · `GET /games/{id}` · `GET /games/search?q=...`
- `GET /releases`

**Admin** (token-gated; send `Authorization: Bearer <ADMIN_TOKEN>` to `/admin/*`):
- `GET /admin/stats/overview` · `GET /admin/stats/database`
- `GET /admin/cache/stats` · `DELETE /admin/cache/clear`
- `POST /admin/sync/games` · `POST /admin/sync/games/{igdb_id}`
- `GET /admin/data/games/recent` · `GET /admin/data/games/problematic`
- `POST /admin/maintenance/cleanup`

---

## Code Quality Checks

```powershell
ruff check app tests
ruff format --check app tests
mypy app
bandit -r app
```

The EU release-date rule is unit-verified without pytest:

```powershell
.venv\Scripts\python tests\test_release_date_rule.py
```

---

## Common Issues & Fixes

### "No module named 'X'"
```powershell
pip install -e ".[dev]"
```

### "Connection refused"
PostgreSQL/Redis not running. Restart infra:
```powershell
docker compose restart postgres redis
# or
podman compose restart postgres redis
```

### Port in use
```powershell
npx kill-port 8000 3000
```

### Postgres/Redis not running
```powershell
podman compose ps
docker compose restart postgres redis
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres DSN (`postgresql://user:pass@host:5432/gamecalendar`) |
| `REDIS_URL` | Redis URL for cache + Celery broker/backend (a single URL) |
| `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` | IGDB API credentials for sync |
| `ADMIN_TOKEN` | Bearer token gating the `/admin/*` routes |

---

## Recommended Workflow

1. Start infra once/day: `docker compose up postgres redis -d`
2. Run migrations: `alembic upgrade head`
3. Start backend: `uvicorn app.main:app --reload --port 8000`
4. Start worker/beat: `celery -A app.sync.celery_app ...`
5. Start frontend: `cd frontend && npm run dev`
6. Stop: `Ctrl+C` in each terminal; end of day `docker compose down`

Happy coding! 🚀