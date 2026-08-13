# Devcontainer Setup

## ✅ What Was Fixed (history)

### Problem 1: Docker-in-Docker Feature
The original devcontainer configuration failed to build with this error:
```
ERROR: Feature "Docker (Docker-in-Docker)" (ghcr.io/devcontainers/features/docker-in-docker) failed to install!
The 'moby' option is not supported on Debian 'trixie'
```

### Problem 2: Post-Create Script
The post-create script failed with:
```
docker-compose: command not found
```

### Root Causes
1. The `docker-in-docker` feature was incompatible with the base image
2. In GitHub Codespaces, Docker is already available on the host
3. The script was using deprecated `docker-compose` instead of `docker compose` (V2)

### Solutions Applied
1. Removed the incompatible `docker-in-docker` feature
2. Changed to a simple image-based configuration
3. Updated all `docker-compose` commands to `docker compose`
4. Added error handling for cases where Docker might not be available yet

**Before:** `dockerComposeFile` integration, `docker-in-docker` feature, complex orchestration
**After:** base `python:3.11-bullseye` image, simple features (Node.js, GitHub CLI), a
post-create script that starts Postgres/Redis and installs deps.

## 🏗️ Backend Consolidation (architectural)

The backend was later consolidated from three microservices
(`services/{game-api,admin-api,data-sync}`) into **one app package** (`app/`). A single
FastAPI process now serves both public and admin routes, and the same package runs the
Celery worker/beat plus Alembic migrations. **All devcontainer scripts and VS Code config
already use this consolidated layout.**

## 🚀 How to Use

### Rebuild the Container (Recommended)
1. Press `F1` or `Ctrl+Shift+P`
2. Type and select: **"Codespaces: Rebuild Container"**
3. Wait 2-3 minutes for the rebuild

The post-create script (`.devcontainer/post-create-codespaces.sh`) will automatically:
1. ✅ Install the app package + dev deps (`pip install -e ".[dev]"`)
2. ✅ Install all npm packages
3. ✅ Start PostgreSQL and Redis containers
4. ✅ Create a `.env` file template
5. ✅ Wait for services to be ready

### Starting Your Services

```bash
# Infrastructure (PostgreSQL + Redis)
docker compose up -d postgres redis

# Run migrations
alembic upgrade head

# Backend API (public + admin on ONE process)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker (processes IGDB sync tasks) — separate terminal
celery -A app.sync.celery_app worker --loglevel=info

# Celery beat (scheduled syncs) — separate terminal
celery -A app.sync.celery_app beat --loglevel=info

# Frontend (separate terminal)
cd frontend
npm run dev
```

Or run the **entire stack in Docker**: `docker compose up --build` (web + worker + beat +
frontend, with automatic migrations via the `migrate` service).

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (Swagger UI at `/docs`)
- PostgreSQL: port 5432 (db `gamecalendar`, user `gameuser`, pass `gamepass`)
- Redis: port 6379

## 📝 Configuration Files

- ✅ `.devcontainer/devcontainer.json` - Main config
- ✅ `.devcontainer/post-create-codespaces.sh` - Setup script for Codespaces
- ✅ `.devcontainer/post-create.sh` - Setup script for local devcontainer
- ✅ `.devcontainer/README.md` - Documentation
- ✅ `.env.example` - Environment variables template

### Files You May Need to Update:
- `.env` - Add your IGDB API credentials after rebuild (`IGDB_CLIENT_ID`,
  `IGDB_CLIENT_SECRET`, `ADMIN_TOKEN`)

## 🔧 Troubleshooting

### If services won't start after rebuild:
```bash
# Check if Docker is available
docker ps

# Start services manually
docker compose up -d postgres redis
docker compose ps
docker compose logs -f postgres redis
```

### If Python packages are missing:
```bash
pip install -e ".[dev]"
```

### If Node modules are missing:
```bash
cd frontend
npm install
```

### If the database has no tables:
```bash
alembic upgrade head
```

## 🎉 Next Steps

1. **Rebuild the container** to apply the fixes
2. **Update `.env`** with your IGDB API credentials
3. **Start developing!**

The devcontainer is properly configured for GitHub Codespaces and will work correctly on rebuild.