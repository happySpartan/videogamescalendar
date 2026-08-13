# Quick Reference — Dev Container / Codespaces

## ✅ Status: ALL FIXES APPLIED

- ✅ Docker-in-Docker incompatibility removed from devcontainer.json
- ✅ `docker compose` (V2) used instead of deprecated `docker-compose`
- ✅ Backend consolidated to a single `app/` package (one process for public + admin)

## 🔄 Rebuild the Container

**Using Command Palette**
```
Press: F1 or Ctrl+Shift+P
Type: "Codespaces: Rebuild Container"
Select: The option and press Enter
```

## 📦 What Happens During Rebuild

1. **Container Build** (~2-3 minutes)
   - Base image: `python:3.11-bullseye`
   - Features: Node.js 20, GitHub CLI

2. **Post-Create Script** (~3-5 minutes)
   - Install the app package + dev deps from pyproject.toml (`pip install -e ".[dev]"`)
   - Install frontend deps (`npm install`)
   - Start PostgreSQL and Redis containers
   - Create a `.env` template

3. **VS Code Extensions** (~1 minute)

**Total time: ~6-9 minutes**

## 🚀 After Rebuild — Starting Services

### Everything in Docker (recommended)
```bash
docker compose up --build
```

### Infrastructure only
```bash
docker compose up -d postgres redis
```

### Backend API (public + admin on ONE process)
```bash
alembic upgrade head            # apply migrations
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery worker & beat (separate terminals)
```bash
celery -A app.sync.celery_app worker --loglevel=info
celery -A app.sync.celery_app beat --loglevel=info
```

### Frontend (development mode)
```bash
cd frontend
npm run dev
```

## 🔍 Verification Commands

```bash
# Check running containers
docker compose ps

# View logs
docker compose logs -f
docker compose logs -f postgres
docker compose logs -f redis

# Test PostgreSQL connection
docker compose exec postgres pg_isready -U gameuser -d gamecalendar

# Test Redis connection
docker compose exec redis redis-cli ping

# Backend health
curl http://localhost:8000/health
```

## ⚙️ Environment Configuration

After rebuild, edit your `.env` file:

- `IGDB_CLIENT_ID` → Your IGDB client ID
- `IGDB_CLIENT_SECRET` → Your IGDB client secret
- `ADMIN_TOKEN` → Your secure admin token

Get IGDB credentials: https://api-docs.igdb.com/#getting-started

## 🐛 Troubleshooting

### If Docker services won't start
```bash
# Check Docker status
docker ps

# Restart services
docker compose restart postgres redis

# Full restart
docker compose down
docker compose up -d postgres redis
```

### If Python packages are missing
```bash
pip install -e ".[dev]"
```

### If the database has no tables
```bash
alembic upgrade head
```

### If Node modules are missing
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Check post-create script execution
```bash
bash .devcontainer/post-create-codespaces.sh
```

## 📝 Port Forwarding

Codespaces automatically forwards these ports:

- **3000** - Frontend (Vite dev server)
- **8000** - Backend API (public + admin), Swagger UI at `/docs`
- **5432** - PostgreSQL
- **6379** - Redis

Access via the "Ports" tab in VS Code or the forwarded URL.

## 🎯 Development Workflow

1. Ensure infra is running: `docker compose ps`
2. Start the backend: `uvicorn app.main:app --reload --port 8000`
3. Start the worker/beat: `celery -A app.sync.celery_app ...`
4. Start the frontend: `cd frontend && npm run dev`
5. Open browser to forwarded port 3000
6. Code and enjoy hot reload! 🔥

---

**Everything is ready! Rebuild and start coding! 🚀**