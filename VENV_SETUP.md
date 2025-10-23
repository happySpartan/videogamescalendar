# Virtual Environment Setup Guide

## What are Virtual Environments?

Virtual environments create **isolated Python installations** for each project. This means:

- ✅ **No conflicts** between project dependencies
- ✅ **Different Python versions** per project
- ✅ **Clean system Python** - won't pollute global packages
- ✅ **Easy cleanup** - just delete the `.venv` folder
- ✅ **Team consistency** - everyone uses same package versions

---

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

### Step 2: Run the Setup Script

```powershell
# Navigate to project root
cd C:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar

# Run the automated setup script
.\setup-venv.ps1
```

This script will:
1. ✅ Check for Python 3.12
2. ✅ Create `.venv` folder in each service
3. ✅ Remove `pip-system-certs` (ZScaler issue)
4. ✅ Install all dependencies from `requirements.txt`
5. ✅ Set up isolated environments for:
   - `services/game-api/.venv`
   - `services/admin-api/.venv`
   - `services/data-sync/.venv`

### Step 3: Restart VS Code

```
File → Close Folder
File → Open Folder → Select videogamecalendar folder
```

VS Code will automatically detect the virtual environments!

### Step 4: Start Debugging

```
Press F5 → Select "🎮 Debug Game API"
```

VS Code will now use the virtual environment automatically.

---

## Manual Setup (If Script Fails)

### Game API

```powershell
cd services\game-api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip uninstall pip-system-certs -y
python -m pip install -r requirements.txt
deactivate
```

### Admin API

```powershell
cd services\admin-api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip uninstall pip-system-certs -y
python -m pip install -r requirements.txt
deactivate
```

### Data Sync

```powershell
cd services\data-sync
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip uninstall pip-system-certs -y
python -m pip install -r requirements.txt
deactivate
```

---

## How VS Code Uses Virtual Environments

### Debug Configurations

Each debug configuration in `.vscode/launch.json` will automatically use the corresponding virtual environment:

- **🎮 Debug Game API** → Uses `services/game-api/.venv`
- **⚙️ Debug Admin API** → Uses `services/admin-api/.venv`
- **🔄 Debug Data Sync Worker** → Uses `services/data-sync/.venv`

### Tasks

VS Code tasks will also use the virtual environments automatically.

### Terminal

When you open a terminal in VS Code, it should auto-activate the virtual environment for the folder you're in.

---

## Verifying It Works

### Check Virtual Environment is Active

When you open a terminal in VS Code, you should see:

```powershell
(.venv) PS C:\...\videogamecalendar\services\game-api>
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
# Should show: redis, fastapi, uvicorn, etc.
```

### Check Where Python Is

```powershell
where.exe python
# Should show: ...\services\game-api\.venv\Scripts\python.exe
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

**Solution:** VS Code hasn't picked up the new virtual environment.

1. Restart VS Code
2. Press `Ctrl+Shift+P`
3. Select "Python: Select Interpreter"
4. Choose the one ending in `.venv\Scripts\python.exe`

### Issue: ModuleNotFoundError after creating venv

**Solution:** Dependencies weren't installed.

```powershell
cd services\game-api
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Managing Virtual Environments

### Activate a Virtual Environment

```powershell
# Windows PowerShell
cd services\game-api
.\.venv\Scripts\Activate.ps1

# Windows CMD
cd services\game-api
.venv\Scripts\activate.bat
```

### Deactivate

```powershell
deactivate
```

### Delete and Recreate

```powershell
# Delete
Remove-Item -Recurse -Force services\game-api\.venv

# Recreate
cd services\game-api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Update Dependencies

```powershell
cd services\game-api
.\.venv\Scripts\Activate.ps1
pip install --upgrade -r requirements.txt
```

### Add New Package

```powershell
cd services\game-api
.\.venv\Scripts\Activate.ps1

# Install package
pip install new-package-name

# Update requirements.txt
pip freeze > requirements.txt
```

---

## Project Structure with Virtual Environments

```
videogamecalendar/
├── services/
│   ├── game-api/
│   │   ├── .venv/              # ← Virtual environment (isolated)
│   │   │   ├── Scripts/
│   │   │   │   └── python.exe  # ← Python 3.12 for this service
│   │   │   └── Lib/
│   │   │       └── site-packages/  # ← Packages for this service only
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   ├── admin-api/
│   │   ├── .venv/              # ← Separate virtual environment
│   │   │   └── ...
│   │   └── requirements.txt
│   │
│   └── data-sync/
│       ├── .venv/              # ← Another separate virtual environment
│       │   └── ...
│       └── requirements.txt
│
├── .python-version             # ← Specifies Python 3.12 for this project
├── setup-venv.ps1              # ← Automated setup script
└── .gitignore                  # ← .venv folders are ignored by git
```

---

## Benefits for This Project

### Before (System-wide Python)

```
C:\Python313\
├── python.exe
└── Lib/site-packages/
    ├── redis (version X)
    ├── fastapi (version Y)
    ├── uvicorn (version Z)
    └── pip-system-certs (broken!)
```

**Problems:**
- ❌ All projects share same packages
- ❌ Can't use different Python versions
- ❌ Broken packages affect everything
- ❌ Hard to clean up

### After (Virtual Environments)

```
services/game-api/.venv/
├── Scripts/python.exe (Python 3.12)
└── Lib/site-packages/
    ├── redis (specific version for this project)
    ├── fastapi (specific version)
    └── NO pip-system-certs!

services/admin-api/.venv/
├── Scripts/python.exe (Python 3.12)
└── Lib/site-packages/
    └── ... (separate packages)
```

**Benefits:**
- ✅ Each service has its own packages
- ✅ Using Python 3.12 (not 3.13)
- ✅ No pip-system-certs issue
- ✅ Easy to delete and recreate

---

## Next Steps

1. ✅ **Run the setup script:** `.\setup-venv.ps1`
2. ✅ **Restart VS Code**
3. ✅ **Press F5** to start debugging
4. ✅ **Check the terminal** - should show `(.venv)`
5. ✅ **Verify Python version** - should be 3.12.x

You're all set! 🚀
