# Quick Reference - Post-Fix Actions

## ✅ Status: ALL FIXES APPLIED

Both issues have been resolved:

1. ✅ Docker-in-Docker incompatibility → Removed from devcontainer.json
2. ✅ docker-compose command not found → Changed to `docker compose` (V2)

## 🔄 Rebuild the Container

**Option 1: Using Command Palette**

```
Press: F1 or Ctrl+Shift+P
Type: "Codespaces: Rebuild Container"
Select: The option and press Enter
```

**Option 2: Using Terminal**
You can't rebuild from inside the container, use Option 1.

## 📦 What Happens During Rebuild

1. **Container Build** (~2-3 minutes)

   - Base image: Python 3.11 (Debian Bullseye)
   - Features: Node.js 20, Git, GitHub CLI, common-utils

2. **Post-Create Script** (~3-5 minutes)

   - Install Python dependencies (game-api, admin-api, data-sync)
   - Install Node.js dependencies (frontend)
   - Start PostgreSQL container
   - Start Redis container
   - Create .env template

3. **VS Code Extensions** (~1 minute)
   - Auto-install all configured extensions

**Total time: ~6-9 minutes**

## 🚀 After Rebuild - Starting Services

### Start All Services with Docker Compose

```bash
docker compose up -d
```

### Start Individual Services

**PostgreSQL and Redis (background)**

```bash
docker compose up -d postgres redis
```

**Game API (development mode)**

```bash
cd services/game-api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Admin API (development mode)**

```bash
cd services/admin-api
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend (development mode)**

```bash
cd frontend
npm run dev
```

## 🔍 Verification Commands

**Check running containers**

```bash
docker compose ps
```

**View logs**

```bash
docker compose logs -f
docker compose logs -f postgres
docker compose logs -f redis
```

**Test PostgreSQL connection**

```bash
docker compose exec postgres pg_isready -U gameuser -d gamecalendar
```

**Test Redis connection**

```bash
docker compose exec redis redis-cli ping
```

## ⚙️ Environment Configuration

After rebuild, edit your `.env` file:

```bash
code .env
```

**Required changes:**

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
docker compose up -d
```

### If Python packages are missing

```bash
pip install -r services/game-api/requirements.txt
pip install -r services/admin-api/requirements.txt
pip install -r services/data-sync/requirements.txt
```

### If Node modules are missing

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Check post-create script execution

```bash
# Run manually to see output
bash .devcontainer/post-create-codespaces.sh
```

## 📝 Port Forwarding

Codespaces automatically forwards these ports:

- **3000** - Frontend (Vite dev server)
- **8000** - Game API
- **8001** - Admin API
- **5432** - PostgreSQL
- **6379** - Redis

Access via the "Ports" tab in VS Code or the forwarded URL.

## 🎯 Development Workflow

1. Ensure services are running: `docker compose ps`
2. Start your frontend: `cd frontend && npm run dev`
3. Start your API: `cd services/game-api && uvicorn main:app --reload`
4. Open browser to forwarded port 3000
5. Code and enjoy hot reload! 🔥

---

**Everything is ready! Rebuild and start coding! 🚀**
