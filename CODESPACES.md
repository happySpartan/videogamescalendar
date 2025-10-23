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

When your Codespace starts for the first time, it will automatically:
- ✅ Install Python 3.12 and Node.js 20
- ✅ Start PostgreSQL 17 and Redis 7 containers
- ✅ Install all Python dependencies for all services
- ✅ Install all frontend dependencies (npm packages)
- ✅ Create a `.env` file with default configuration

**This takes about 2-3 minutes.** Watch the terminal for progress.

### 3. Configure Your Environment

#### Add IGDB API Credentials

You need to add your IGDB API credentials to the `.env` file:

1. Open `.env` in the root directory
2. Replace the placeholder values:
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

### 4. Start Development Services

You have two options:

#### Option A: Use VS Code Tasks (Recommended)

Press `Ctrl+Shift+P` and select **"Tasks: Run Task"**, then choose:
- **🚀 Start All Services** - Starts everything at once
- **🎮 Start Game API** - Start Game API only
- **⚙️ Start Admin API** - Start Admin API only
- **🔄 Start Data Sync** - Start Celery worker only
- **⚛️ Start Frontend** - Start React app only

#### Option B: Manual Terminal Commands

**Terminal 1 - Game API:**
```bash
cd services/game-api
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Admin API:**
```bash
cd services/admin-api
uvicorn main:app --reload --port 8001
```

**Terminal 3 - Data Sync Worker:**
```bash
cd services/data-sync
celery -A worker worker --loglevel=info --pool=solo
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access Your Application

GitHub Codespaces will automatically forward ports and provide URLs:

- **Frontend:** Click the "Ports" tab → Open port 3000 in browser
- **Game API Docs:** Click the "Ports" tab → Open port 8000 in browser (add `/docs`)
- **Admin API Docs:** Click the "Ports" tab → Open port 8001 in browser (add `/docs`)

Or look for pop-up notifications when services start with "Open in Browser" buttons.

---

## 🛠️ Development Workflow

### Hot Reload

All services support hot reload:
- **Python APIs:** Uvicorn automatically reloads on file changes
- **Frontend:** Vite HMR updates instantly
- **Celery Worker:** Restart required for changes

### Running Code Quality Checks

Press `Ctrl+Shift+P` → **"Tasks: Run Task"** → **"✅ Run All Quality Checks"**

Or manually:
```bash
cd services/game-api
ruff check .
ruff format .
mypy .
bandit -r . -c pyproject.toml
```

### Debugging

Use VS Code's debugger (F5):
1. Press `F5`
2. Select a debug configuration:
   - **🎮 Debug Game API**
   - **⚙️ Debug Admin API**
   - **🔄 Debug Data Sync Worker**
   - **🚀 Debug All APIs** (compound)
   - **🌟 Debug Full Stack** (compound - everything)

Set breakpoints in your code, and the debugger will pause execution.

---

## 📦 Infrastructure Services

### PostgreSQL Database

- **Host:** `postgres` (or `localhost` from app container)
- **Port:** `5432`
- **Database:** `gamecalendar`
- **User:** `gameuser`
- **Password:** `gamepass`

**Connect with psql:**
```bash
psql -h postgres -U gameuser -d gamecalendar
```

### Redis Cache

- **Host:** `localhost`
- **Port:** `6379`
- **Database:** `0`

**Connect with redis-cli:**
```bash
redis-cli -h localhost -p 6379
```

### Checking Service Status

**PostgreSQL:**
```bash
pg_isready -h postgres -p 5432 -U gameuser
```

**Redis:**
```bash
redis-cli -h localhost -p 6379 ping
```

---

## 🔧 Common Tasks

### Restart Infrastructure Services

```bash
# Restart PostgreSQL
docker restart <postgres_container_id>

# Restart Redis
docker restart <redis_container_id>

# Check container IDs
docker ps
```

### Reset Database

```bash
# Connect to PostgreSQL
psql -h postgres -U gameuser -d gamecalendar

# Drop and recreate tables (or run migration scripts)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

### Install New Dependencies

**Python:**
```bash
cd services/game-api  # or admin-api, data-sync
pip install <package-name>
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install <package-name>
```

### View Logs

**Application logs:** Check the terminal where the service is running

**Database logs:**
```bash
docker logs <postgres_container_id>
```

**Redis logs:**
```bash
docker logs <redis_container_id>
```

---

## 🐛 Troubleshooting

### "Connection refused" errors

**Cause:** PostgreSQL or Redis not running

**Fix:**
```bash
# Check if containers are running
docker ps

# Restart the Codespace if needed
# Click the menu (three dots) → Rebuild Container
```

### "Module not found" errors

**Cause:** Dependencies not installed

**Fix:**
```bash
cd services/<service-name>
pip install -r requirements.txt
```

### Frontend won't start

**Cause:** Node modules not installed

**Fix:**
```bash
cd frontend
npm install
```

### Port already in use

**Cause:** Service already running

**Fix:**
```bash
# Kill process on port
npx kill-port 8000 8001 3000

# Or restart the terminal
```

### IGDB API errors

**Cause:** Invalid or missing credentials

**Fix:**
1. Check `.env` file has correct IGDB_CLIENT_ID and IGDB_CLIENT_SECRET
2. Verify credentials at https://dev.twitch.tv/console/apps
3. Restart the API services

---

## 🎯 Best Practices

### Daily Workflow

1. **Open Codespace** - Your environment is saved between sessions
2. **Start services** - Use VS Code tasks or manual commands
3. **Code & Test** - All changes auto-reload
4. **Run quality checks** - Before committing
5. **Commit & Push** - Your work is automatically synced to GitHub

### Resource Management

- **Stop services** when not in use (Ctrl+C in terminal)
- **Stop Codespace** when done for the day (saves billing hours)
- **Delete Codespace** if you need a fresh start

### Code Quality

Always run before committing:
```bash
# Run quality checks
ruff check .
ruff format .
mypy .

# Run tests (when available)
pytest
```

---

## 💡 Tips & Tricks

### Multiple Terminals

- Press `Ctrl+Shift+`` (backtick) to open a new terminal
- Use split terminals: Click the split icon in terminal panel
- Name terminals: Right-click → Rename

### VS Code Extensions

Pre-installed extensions:
- **Python** - IntelliSense, debugging, linting
- **Ruff** - Fast linting and formatting
- **Pylance** - Type checking and auto-completion
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **Docker** - Container management
- **GitLens** - Enhanced Git integration

### Customization

You can customize your Codespace:
- Add extensions: Press `Ctrl+Shift+X`
- Modify settings: `.vscode/settings.json`
- Add tasks: `.vscode/tasks.json`
- Update devcontainer: `.devcontainer/devcontainer.json`

### Performance

- Use VS Code tasks instead of manual commands
- Enable auto-save: File → Auto Save
- Use the integrated terminal (faster than external)

---

## 🆘 Getting Help

### Documentation Links

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Detailed setup instructions
- [README.md](./README.md) - Project overview and architecture
- [VENV_SETUP.md](./VENV_SETUP.md) - Virtual environment guide (not needed in Codespaces)

### Common Commands Reference

```bash
# Start all services (use VS Code tasks instead)
cd services/game-api && uvicorn main:app --reload --port 8000 &
cd services/admin-api && uvicorn main:app --reload --port 8001 &
cd services/data-sync && celery -A worker worker --loglevel=info --pool=solo &
cd frontend && npm run dev &

# Stop all services
pkill -f uvicorn
pkill -f celery
pkill -f vite

# Check what's running
ps aux | grep -E 'uvicorn|celery|vite'
```

---

## 🎮 Happy Coding!

Your complete development environment is ready to go. No local setup, no dependency issues, no Docker confusion - just pure development productivity!

**Questions?** Check the troubleshooting section above or review the project documentation.
