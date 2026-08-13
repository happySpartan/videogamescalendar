# Dev Container Setup

This project includes a complete VS Code Dev Container configuration for a consistent development environment.

## Quick Start for GitHub Codespaces

If you're using GitHub Codespaces, the environment is automatically set up for you! Just:

1. Open this repository in Codespaces
2. Wait for the container to build and services to start
3. Update your `.env` file with IGDB API credentials
4. Start developing!

The setup automatically:
- Installs Python 3.12 and Node.js 20
- Installs all Python and npm dependencies
- Starts PostgreSQL 17 and Redis 7 containers
- Configures VS Code extensions

## What's Included

### Development Tools
- **Python 3.12** with the app package + dev deps installed from `pyproject.toml`
- **Node.js 20** for the React/Vite frontend
- **PostgreSQL Client** for database interactions
- **Redis CLI** for cache management
- **Docker-in-Docker** for container management
- **GitHub CLI** for repository management

### Services
- **PostgreSQL 17** - Main database (port 5432)
- **Redis 7** - Cache and Celery broker/backend (port 6379)
- **Backend** - ONE FastAPI process for public + admin routes (port 8000)
- **Frontend** - Vite dev server (port 3000)

## Architecture (one app)

The backend is a **single consolidated app** (`app/`), not three microservices:
- `app/main.py` — FastAPI entry (`uvicorn app.main:app`), serves public + admin routes
- `app/api.py` — public routes (`/games`, `/releases`, `/genres`, `/platforms`, `/games/search`)
- `app/admin.py` — token-gated admin routes (`/admin/*`)
- `app/sync/` — IGDB sync logic, Celery `celery_app.py`, worker
- `alembic/` — database migrations

## Getting Started

### For GitHub Codespaces (Recommended)

1. Click "Code" → "Open with Codespaces" → "New codespace"
2. Wait for the environment to set up (about 2-3 minutes)
3. Update `.env` with your IGDB API credentials
4. Start coding!

### For Local Development

#### Prerequisites
- [Visual Studio Code](https://code.visualstudio.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Opening the Project

```bash
git clone https://github.com/happySpartan/videogamescalendar.git
cd videogamescalendar
cp .env.example .env   # then add your IGDB credentials
code .
```

When prompted, click **"Reopen in Container"** (or `F1` → "Dev Containers: Reopen in Container") and wait for the post-create script to complete.

## Development Workflow

### Running the Backend
```bash
# One process for public + admin API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker (consumes IGDB sync tasks)
celery -A app.sync.celery_app worker --loglevel=info

# Celery beat (scheduled syncs)
celery -A app.sync.celery_app beat --loglevel=info
```
The API is available at http://localhost:8000 (Swagger UI at `/docs`).

### Running the Frontend
```bash
cd frontend
npm run dev
```
The frontend will be available at http://localhost:3000.

### Running Everything in Docker
```bash
docker compose up --build
```

### Database Operations

Connect to PostgreSQL:
```bash
psql -h postgres -U gameuser -d gamecalendar
```

Run migrations:
```bash
alembic upgrade head
```

### Testing

Verify the EU release-date rule (standalone, no pytest needed):
```bash
python tests/test_release_date_rule.py
```

## Environment Variables

Make sure to set these in your `.env` file:

```env
# Required for IGDB API integration
IGDB_CLIENT_ID=your_client_id_here
IGDB_CLIENT_SECRET=your_client_secret_here

# Security (change in production!)
ADMIN_TOKEN=your_secure_token_here
```

## Troubleshooting

### Container won't start
- Make sure Docker Desktop is running
- Try rebuilding: `F1` → "Dev Containers: Rebuild Container"

### Database connection issues
- Check if PostgreSQL is running: `pg_isready -h postgres -U gameuser -d gamecalendar`
- Check the logs: `docker compose logs postgres`

### Port conflicts
- Make sure ports 3000, 5432, 6379, and 8000 are not in use
- Stop other services using these ports

### Node modules issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Python dependency issues
```bash
pip install --upgrade pip
pip install -e ".[dev]" --force-reinstall
```

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)