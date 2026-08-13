# Video Game Calendar — Complete Documentation

## Overview

The Video Game Calendar is a modern web application that displays upcoming video game
releases. It uses a React/TypeScript frontend, a **single consolidated FastAPI backend**,
PostgreSQL, and Redis (which doubles as the Celery broker/backend).

## Architecture

### Single-app architecture
```
Frontend (React/Vite) ──► FastAPI app (app.main) ──► PostgreSQL
                                  │   ▲
                                  ▼   │
                             Redis Cache
                                  ▲
                                  │
                    Celery worker/beat (app.sync)
```
One Python package (`app/`) runs every backend role:
- **Web** — one FastAPI process serves **both** public routes (`app.api`) and token-gated
  admin routes (`app.admin`)
- **Worker** — consumes IGDB sync tasks enqueued by the admin API
- **Beat** — schedules recurring sync/cleanup
- **Migrate** — Alembic schema migrations

### Technology Stack
- **Frontend**: React, TypeScript, Vite, React Router, TanStack Query
- **Backend**: FastAPI (async), SQLAlchemy ORM, Pydantic
- **Database**: PostgreSQL 17 with trigram (`pg_trgm`) search
- **Cache / Message Queue**: Redis 7 (single `REDIS_URL` for cache + Celery broker/backend)
- **Background Jobs**: Celery (worker + beat)
- **Containerization**: Docker & Docker Compose
- **Migrations**: Alembic

## Project Structure

```
videogamecalendar/
├── app/                    # The consolidated backend package
│   ├── main.py             # FastAPI entry (public + admin), /health
│   ├── api.py              # Public routes: /games, /releases, /genres, /platforms, /games/search
│   ├── admin.py            # Token-gated admin routes under /admin/*
│   ├── config.py           # Settings (DB URL, IGDB creds, admin token)
│   ├── db.py               # Database engine/session
│   ├── deps.py             # Shared dependencies (e.g. Redis client)
│   ├── models/             # SQLAlchemy models (game, genre, platform, company, ...)
│   └── sync/               # IGDB sync logic, Celery app + worker
├── alembic/                # Database migrations
├── frontend/               # React application (port 3000)
├── infrastructure/         # init.sql etc.
├── tests/                  # Backend tests (ADR-0002 release-date rule)
├── Dockerfile              # One image for web/worker/beat/migrate
└── docker-compose.yml      # postgres, redis, app, migrate, worker, beat, frontend
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12
- Node.js 18+
- PostgreSQL 17 + Redis 7 (or use the compose containers)

### 1. Environment Setup
```bash
git clone https://github.com/happySpartan/videogamescalendar.git
cd videogamescalendar
cp .env.example .env
# Edit .env with your IGDB API credentials
```

### 2. Infrastructure (Recommended: Docker)
```bash
# Start everything (app + worker + beat + frontend, auto-migrates)
docker compose up --build

# Or infrastructure only, then run locally
docker compose up postgres redis -d
```

### 3. Local Development (Alternative)
```bash
# Install backend (app package + dev deps)
python -m venv .venv
.venv/bin/activate         # or .venv\Scripts\Activate.ps1 on Windows
pip install -e ".[dev]"

# Migrations
alembic upgrade head
```
Then in separate terminals:
```bash
# Terminal 1 — backend (public + admin on one process)
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker (processes sync tasks)
celery -A app.sync.celery_app worker --loglevel=info

# Terminal 3 — Celery beat (scheduled syncs)
celery -A app.sync.celery_app beat --loglevel=info

# Terminal 4 — frontend
cd frontend
npm install
npm run dev
```

## API Documentation

**Public** (no auth)
- `GET /health` - DB + Redis liveness
- `GET /games` - Paginated game listing with filtering
- `GET /games/{id}` - Detailed game information
- `GET /games/search?q=...` - Trigram full-text search
- `GET /releases` - The release calendar (EU release-date rule — see `docs/adr/0002`)
- `GET /genres` - Genre reference data
- `GET /platforms` - Platform reference data
- Swagger UI at `/docs`

**Admin** (token-gated; `Authorization: Bearer $ADMIN_TOKEN`)
- `GET /admin/stats/overview` - System statistics
- `GET /admin/stats/database` - Database metrics
- `GET /admin/cache/stats` - Cache status
- `DELETE /admin/cache/clear` - Clear cache
- `POST /admin/sync/games` - Trigger a full IGDB sync
- `POST /admin/sync/games/{igdb_id}` - Sync one game
- `GET /admin/data/games/recent` - Recently synced games
- `GET /admin/data/games/problematic` - Games with issues
- `POST /admin/maintenance/cleanup` - Cleanup task

## Background Jobs (Celery)

The worker app (`app.sync.celery_app`) schedules on a **single Redis URL**:

| Schedule | Task | When |
|----------|------|------|
| Hourly delta sync | `data_sync.sync_games` (full_sync=False) | every hour at minute 0 |
| Daily full sync | `data_sync.sync_games` (full_sync=True) | every day at 02:00 UTC |
| Weekly cleanup | `data_sync.cleanup_old_data` | Sunday at 03:00 UTC |

The EU release-date rule (`app/sync/igdb_client.py`, ADR-0002) selects the canonical date:
IGDB region Europe → Worldwide → TBA, label-aware rather than blind-earliest.

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://gameuser:***@postgres:5432/gamecalendar

# Redis (cache AND Celery broker/backend — a single URL)
REDIS_URL=redis://redis:6379/0

# IGDB API (Required for data sync)
IGDB_CLIENT_ID=your_igdb_client_id
IGDB_CLIENT_SECRET=your_igdb_client_secret

# Admin Authentication
ADMIN_TOKEN=your_secure_admin_token
```

## Verification & Testing

```bash
# Health
curl http://localhost:8000/health

# Public endpoints
curl http://localhost:8000/games?limit=5
curl http://localhost:8000/releases
curl http://localhost:8000/genres
```

### Tests
The EU release-date rule is unit-verified via a standalone self-check (no pytest needed):
```bash
python tests/test_release_date_rule.py
```

### Quality checks (matches CI scope)
```bash
ruff check app tests
mypy app
bandit -r app
```

## Database Features

### PostgreSQL Optimizations
- GIN **trigram indexes** (`pg_trgm`) for fuzzy text search
- Foreign key relationships for data integrity
- Alembic migrations create `pg_trgm` / `uuid-ossp` idempotently (works on any Postgres)

### Main Tables (SQLAlchemy models in `app/models/`)
- `games`, `genres`, `platforms`, `companies`, `franchises`, `languages`, `regions`
  (+ association tables)

## Performance & Caching

| Endpoint | Cache TTL |
|----------|-----------|
| `/games` (list) | 300s (5 min) |
| `/releases` | 300s (5 min) |
| `/games/{id}` | 600s (10 min) |
| `/games/search` | 600s (10 min) |
| `/genres`, `/platforms` | 1800s (30 min) |

## Monitoring & Maintenance

```bash
# Docker operations
docker compose ps
docker compose logs -f app
docker compose restart redis
docker compose down -v

# Database
psql -h localhost -U gameuser -d gamecalendar
redis-cli ping

# Celery
celery -A app.sync.celery_app inspect ping    # check workers
```

## Deployment

Per ADR-0003, deployment targets a **single VPS with Docker Compose** (not Azure Container
Apps). The compose file runs one app image in five roles (migrate / app / worker / beat) plus
postgres, redis, and frontend; `migrate` runs `alembic upgrade head` before the API starts.

## Troubleshooting

**Database Connection Errors:**
```bash
docker compose logs postgres
psql -h localhost -U gameuser -d gamecalendar
```

**Redis Connection Issues:**
```bash
docker compose ps redis
redis-cli ping
```

**Empty database / no tables:**
```bash
alembic upgrade head
```

**Port Conflicts:**
```bash
netstat -tlnp | grep -E ':8000|:5432'
```

## Contributing

1. Create a feature branch
2. Implement changes with tests
3. Run quality checks (`ruff`, `mypy`, `bandit` on `app tests`)
4. Open a pull request

### Code Standards
- **Python**: ruff (lint + format), type hints, mypy
- **TypeScript**: ESLint, Prettier
- **API**: OpenAPI documentation (`/docs`)
- **Tests**: ADR-0002 unit tests in `tests/`

## Support

For issues, questions, or contributions:
- Create GitHub issues for bugs
- Use discussions for questions
- Follow contribution guidelines
- Check this documentation first

---

This documentation covers the Video Game Calendar application with its consolidated
single-app architecture, providing a scalable and maintainable foundation for development.
Architecture decisions are recorded in `docs/adr/` (ADR-0001 consolidation, ADR-0002 EU
release-date rule, ADR-0003 VPS deployment).