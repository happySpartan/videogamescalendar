# Virtual Environment Setup Guide

## What are Virtual Environments?

Virtual environments create **isolated Python installations** for each project. This means:

- ✅ **No conflicts** between project dependencies
- ✅ **Different Python versions** per project
- ✅ **Clean system Python** - won't pollute global packages
- ✅ **Easy cleanup** - just delete the `.venv` folder
- ✅ **Team consistency** - everyone uses same package versions

> **Project layout note:** the backend is **one consolidated app package** (`app/`), so the
> project needs **one root `.venv`**, not separate per-service environments. The old
> `services/{game-api,admin-api,data-sync}/.venv` layout no longer exists.

## Quick Setup (Automated)

### Step 1: Install Python 3.12

**Download:** https://www.python.org/downloads/release/python-31210/

During installation:
- ✅ Check "Add python.exe to PATH"
- ✅ Check "Install for all users" (optional)

Verify:
```powershell
py -3.12 --version
# Should show: Python 3.12.x
```

### Step 2: Create the venv and install the app

```powershell
# Navigate to project root
cd C:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar

# Create a root virtual environment
py -3.12 -m venv .venv

# Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install the app package + dev deps (ruff, mypy, bandit, ...) from pyproject.toml
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Step 3: Restart VS Code

```
File → Close Folder
File → Open Folder → Select videogamecalendar folder
```

VS Code will automatically detect the root `.venv`.

### Step 4: Start the backend

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Manual Setup (If the automated path fails)

```powershell
cd C:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip uninstall pip-system-certs -y   # only if you hit the ZScaler error
python -m pip install -e ".[dev]"
```

---

## How VS Code Uses the Virtual Environment

- `.vscode/launch.json` and the VS Code tasks reference the **root `.venv`** (backend runs
  `uvicorn app.main:app`, worker `celery -A app.sync.celery_app`).
- When you open a terminal in VS Code, it auto-activates the root `.venv`.

---

## Verifying It Works

### Check Virtual Environment is Active

When you open a terminal in VS Code, you should see:

```powershell
(.venv) PS C:\...\videogamecalendar>
```

The `(.venv)` prefix means the virtual environment is active!

### Check Python Version

```powershell
python --version
# Should show: Python 3.12.x (not 3.13!)
```

### Check Installed Packages

```powershell
pip list
# Should show: fastapi, uvicorn, celery, redis, sqlalchemy, ...
```

### Check Where Python Is

```powershell
where.exe python
# Should show: ...\videogamecalendar\.venv\Scripts\python.exe
```

---

## Common Issues & Solutions

### Issue: "py -3.12 is not recognized"
**Solution:** Python 3.12 is not installed.
Download and install: https://www.python.org/downloads/release/python-31210/

### Issue: "Cannot be loaded because running scripts is disabled"
**Solution:** PowerShell execution policy needs to be changed.
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Still using Python 3.13
**Solution:** VS Code hasn't picked up the virtual environment.
1. Restart VS Code
2. Press `Ctrl+Shift+P`
3. Select "Python: Select Interpreter"
4. Choose the one ending in `.venv\Scripts\python.exe`

### Issue: ModuleNotFoundError after creating venv
**Solution:** Dependencies weren't installed.
```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

---

## Managing the Virtual Environment

### Activate
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### Deactivate
```powershell
deactivate
```

### Delete and Recreate
```powershell
# Delete
Remove-Item -Recurse -Force .venv

# Recreate
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Update Dependencies
```powershell
.\.venv\Scripts\Activate.ps1
pip install --upgrade -e ".[dev]"
```

---

## Project Structure with the Virtual Environment

```
videogamecalendar/
├── .venv/                    # ← The single root virtual environment
│   ├── Scripts/
│   │   └── python.exe        # ← Python 3.12 for the whole project
│   └── Lib/
│       └── site-packages/    # ← All backend packages live here
├── app/                      # ← The consolidated backend package
│   ├── main.py               #     FastAPI entry (public + admin)
│   ├── api.py                #     public routes
│   ├── admin.py              #     admin routes
│   └── sync/                 #     IGDB sync + Celery
├── frontend/                 # React/Vite app (Node deps, not in .venv)
├── alembic/                  # Database migrations
├── .python-version           # ← Specifies Python 3.12 for this project
└── .gitignore                # ← .venv is ignored by git
```

---

## Benefits for This Project

One root venv gives you:
- ✅ All backend code runs against the same packages (FastAPI + admin + Celery together)
- ✅ Python 3.12 (not 3.13)
- ✅ No pip-system-certs issue
- ✅ Easy to delete and recreate

## Next Steps

1. ✅ **Create the venv:** `py -3.12 -m venv .venv`
2. ✅ **Install the app:** `pip install -e ".[dev]"`
3. ✅ **Restart VS Code**
4. ✅ **Start the backend:** `uvicorn app.main:app --reload --port 8000`

You're all set! 🚀