# Complete Setup Guide

## Current Issues & Solutions

### Issue 1: Python Version Mismatch ❌

**Problem:** You have Python 3.13 installed (`c:\Python313\python.exe`), but the project requires Python 3.12.

**Solution:**

1. **Download Python 3.12:**
   - Go to: https://www.python.org/downloads/release/python-31210/
   - Download "Windows installer (64-bit)"

2. **Install Python 3.12:**
   - Run the installer
   - ✅ Check "Add python.exe to PATH"
   - ✅ Check "Install for all users" (optional)
   - Click "Install Now"

3. **Verify Installation:**
   ```powershell
   python --version
   # Should show: Python 3.12.x
   ```

4. **If you still see Python 3.13:**
   ```powershell
   # Use py launcher to specify version
   py -3.12 --version

   # Or add Python 3.12 to PATH before Python 3.13
   # Edit System Environment Variables → Path
   # Move C:\Python312\ ABOVE C:\Python313\
   ```

---

### Issue 2: pip-system-certs Error ⚠️

**Problem:**
```
pip_system_certs: ERROR: could not inject truststore: module 'pip._vendor.truststore' has no attribute 'SSLContext'
```

**Solution:**

```powershell
# Uninstall the problematic package
pip uninstall pip-system-certs -y

# Or if using py launcher:
py -3.12 -m pip uninstall pip-system-certs -y
```

**Note:** `pip-system-certs` is only needed for corporate proxies like ZScaler. If you don't need it, you're good to go.

**If you DO need ZScaler certificates:**
```powershell
# Set environment variables instead
$env:REQUESTS_CA_BUNDLE = "C:\path\to\zscaler\cert.pem"
$env:SSL_CERT_FILE = "C:\path\to\zscaler\cert.pem"
```

---

### Issue 3: Missing Python Dependencies ❌

**Problem:**
```
ModuleNotFoundError: No module named 'redis'
ModuleNotFoundError: No module named 'celery'
```

**Solution - Install All Dependencies:**

```powershell
# Navigate to project root
cd C:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar

# Game API
cd services\game-api
pip install -r requirements.txt

# Admin API
cd ..\admin-api
pip install -r requirements.txt

# Data Sync
cd ..\data-sync
pip install -r requirements.txt

# Return to project root
cd ..\..
```

**Or use the VS Code Task:**
1. Press `Ctrl+Shift+P`
2. Select "Tasks: Run Task"
3. Choose **"🐍 Install Backend Dependencies"**

---

## Step-by-Step Setup (Fresh Start)

### 1. Prerequisites

- ✅ Python 3.12 installed
- ✅ Node.js 18+ installed
- ✅ Docker or Podman installed
- ✅ Git installed

### 2. Clone & Navigate

```powershell
git clone <your-repo-url>
cd videogamecalendar
```

### 3. Fix pip-system-certs

```powershell
pip uninstall pip-system-certs -y
```

### 4. Install All Dependencies

**Option A: Use VS Code Tasks (Recommended)**
1. Open project in VS Code
2. Press `Ctrl+Shift+P` → "Tasks: Run Task"
3. Select **"🛠️ Setup Dev Environment"**

**Option B: Manual Install**

```powershell
# Backend
cd services\game-api
pip install -r requirements.txt

cd ..\admin-api
pip install -r requirements.txt

cd ..\data-sync
pip install -r requirements.txt

# Frontend
cd ..\..\frontend
npm install
```

### 5. Setup Environment Files

```powershell
# Copy environment file
copy .env.example .env

# Edit .env and add your IGDB credentials:
# IGDB_CLIENT_ID=your_client_id
# IGDB_CLIENT_SECRET=your_client_secret
# ADMIN_TOKEN=your_secure_token
```

### 6. Start Infrastructure

**Option A: Using Podman**
```powershell
podman compose up postgres redis -d
```

**Option B: Using Docker**
```powershell
docker-compose up postgres redis -d
```

**Option C: Use VS Code Task**
1. Press `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select **"🐋 Start Infrastructure"**

### 7. Verify Infrastructure is Running

```powershell
# For Podman
podman compose ps

# For Docker
docker-compose ps

# Should show postgres and redis as "Running"
```

### 8. Start Services

**Option A: Start All Services (Recommended for First Time)**
1. Press `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select **"🚀 Start All Services"**

**Option B: Start Individual Services**

**Terminal 1 - Game API:**
```powershell
cd services\game-api
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Admin API:**
```powershell
cd services\admin-api
uvicorn main:app --reload --port 8001
```

**Terminal 3 - Data Sync Worker:**
```powershell
cd services\data-sync
celery -A worker worker --loglevel=info --pool=solo
```

**Terminal 4 - Frontend:**
```powershell
cd frontend
npm run dev
```

### 9. Access the Application

- **Frontend:** http://localhost:3000
- **Game API Docs:** http://localhost:8000/docs
- **Admin API Docs:** http://localhost:8001/docs

---

## Understanding VS Code Debug Configurations

### Individual Debuggers

1. **🎮 Debug Game API**
   - Debugs the Game API service
   - Sets breakpoints in `services/game-api/`
   - Port: 8000

2. **⚙️ Debug Admin API**
   - Debugs the Admin API service
   - Sets breakpoints in `services/admin-api/`
   - Port: 8001

3. **🔄 Debug Data Sync Worker**
   - Debugs the Celery worker
   - Sets breakpoints in `services/data-sync/`

4. **⚛️ Debug Frontend (Vite)**
   - Launches Vite dev server
   - For debugging the React app

5. **🌐 Launch Chrome (Frontend)**
   - Opens Chrome browser pointed at http://localhost:3000
   - Used WITH "Debug Frontend (Vite)"
   - Allows you to debug in browser + VS Code

6. **🧪 Debug Python Script**
   - Generic debugger for ANY Python file
   - Open a `.py` file and press F5
   - Useful for utility scripts, tests, etc.

### Compound Configurations (Multiple Services)

1. **🚀 Debug All APIs**
   - Game API + Admin API
   - Both running with debugger attached

2. **🌟 Debug Full Stack**
   - Game API + Admin API + Frontend (Vite) + Chrome
   - Everything running, full debugging capability

3. **🎯 Debug Backend Only**
   - Game API + Admin API + Data Sync Worker
   - All backend services with debugger

---

## Common Issues & Fixes

### "No module named 'X'"

**Fix:**
```powershell
cd services\<service-name>
pip install -r requirements.txt
```

### "Connection refused" or "Target machine actively refused"

**This means the debugger can't connect. Usually because:**
- Another instance is already running (kill it first)
- Port is in use (check with `netstat -ano | findstr :8000`)

**Fix:**
```powershell
# Kill process on port 8000
npx kill-port 8000 8001 3000
```

### PostgreSQL/Redis not running

**Fix:**
```powershell
# Check status
podman compose ps
# or
docker-compose ps

# Restart if needed
podman compose restart postgres redis
```

### Python 3.13 still being used

**Fix:**
```powershell
# Use py launcher
py -3.12 -m pip install -r requirements.txt

# Or update PATH to prioritize Python 3.12
# Windows Settings → Environment Variables → Path
# Move C:\Python312\ to the TOP
```

---

## Recommended Development Workflow

### Daily Workflow

1. **Start Infrastructure** (only once per day)
   ```powershell
   podman compose up postgres redis -d
   ```

2. **Start Services** (use VS Code tasks or manual)
   - Press `F5` → Select **"🌟 Debug Full Stack"**
   - OR use tasks: **"🚀 Start All Services"**

3. **Make Changes**
   - Hot reload is enabled for all services
   - Just save your files and see changes instantly

4. **Stop Services**
   - Press `Ctrl+C` in each terminal
   - OR click "Stop" in VS Code Debug panel

5. **Stop Infrastructure** (end of day)
   ```powershell
   podman compose down
   ```

### Code Quality Checks

**Before committing code:**
```powershell
# Run all quality checks
# Use VS Code Task: "✅ Run All Quality Checks"

# Or manually:
cd services\game-api
ruff check .
ruff format .
mypy .
bandit -r . -c pyproject.toml
```

---

## Quick Commands Reference

### Infrastructure
```powershell
# Start
podman compose up postgres redis -d

# Stop
podman compose down

# Clean (remove data)
podman compose down -v
```

### Game API
```powershell
cd services\game-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Admin API
```powershell
cd services\admin-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Data Sync
```powershell
cd services\data-sync
pip install -r requirements.txt
celery -A worker worker --loglevel=info --pool=solo
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

---

## Need Help?

1. **Check logs:**
   - Backend: Look in terminal output
   - Podman: `podman compose logs postgres redis`
   - Frontend: Browser console (F12)

2. **Clean restart:**
   ```powershell
   podman compose down -v
   podman compose up postgres redis -d
   # Restart all services
   ```

3. **Verify installations:**
   ```powershell
   python --version  # Should be 3.12.x
   node --version    # Should be 18.x or higher
   podman --version  # or docker --version
   ```

Happy coding! 🚀
