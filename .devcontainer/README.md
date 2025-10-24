# Dev Container Setup

This project includes a complete VS Code Dev Container configuration for a consistent development environment.

## Quick Start for GitHub Codespaces

If you're using GitHub Codespaces, the environment is automatically set up for you! Just:

1. Open this repository in Codespaces
2. Wait for the container to build and services to start
3. Update your `.env` file with IGDB API credentials
4. Start developing!

The setup automatically:
- Installs Python 3.11 and Node.js 20
- Installs all Python and npm dependencies
- Starts PostgreSQL and Redis containers
- Configures VS Code extensions

## What's Included

### Development Tools
- **Python 3.11** with common development packages (black, flake8, pytest, mypy)
- **Node.js 20** for frontend development
- **PostgreSQL Client** for database interactions
- **Redis CLI** for cache management
- **Docker-in-Docker** for container management
- **GitHub CLI** for repository management

### Services
- **PostgreSQL 15** - Main database
- **Redis 7** - Caching and message broker
- **Game API** - FastAPI service on port 8000
- **Admin API** - FastAPI service on port 8001
- **Frontend** - Vite dev server on port 3000

### VS Code Extensions
The devcontainer automatically installs:
- Python development tools (Pylance, Black formatter, Flake8)
- Frontend tools (ESLint, Prettier)
- Database tools (SQLTools with PostgreSQL driver)
- Git tools (GitLens, GitHub PR)
- Docker extension
- And more useful utilities

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

### Opening the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/happySpartan/videogamescalendar.git
   cd videogamescalendar
   ```

2. Copy `.env.example` to `.env` and update with your credentials:
   ```bash
   cp .env.example .env
   ```

3. Open in VS Code:
   ```bash
   code .
   ```

4. When prompted, click **"Reopen in Container"** or:
   - Press `F1` or `Ctrl+Shift+P`
   - Select "Dev Containers: Reopen in Container"

5. Wait for the container to build and the post-create script to complete.

## Development Workflow

### Running the Frontend
```bash
cd frontend
npm run dev
```
The frontend will be available at http://localhost:3000

### Running the Game API
```bash
cd services/game-api
uvicorn main:app --reload --host 0.0.0.0
```
The API will be available at http://localhost:8000

### Running the Admin API
```bash
cd services/admin-api
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
The Admin API will be available at http://localhost:8001

### Running All Services
```bash
docker-compose up
```

### Database Operations

Connect to PostgreSQL:
```bash
psql -h postgres -U gameuser -d gamecalendar
```

Run migrations:
```bash
python scripts/setup_migrations.py
```

### Testing

Run Python tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=services --cov-report=html
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
- Check the logs: `docker-compose logs postgres`

### Port conflicts
- Make sure ports 3000, 5432, 6379, 8000, and 8001 are not in use
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
pip install -r services/game-api/requirements.txt --force-reinstall
```

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)
