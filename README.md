# Video Game Releases Calendar

A modern, microservices-based web application that displays a comprehensive calendar of video game releases using the IGDB API. Built with FastAPI, React, and PostgreSQL.

## 🚀 Quick Start with GitHub Codespaces (Recommended)

**Zero setup required!** Open this project directly in GitHub Codespaces for a complete cloud development environment:

1. Click the green **"Code"** button on GitHub
2. Select **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. Wait 2-3 minutes for automatic setup
5. Start coding!

📖 **[Read the complete Codespaces guide →](./CODESPACES.md)**

---

## Features

- **Calendar Views**: Month, week, and day views for game releases
- **Advanced Filters**: Filter by platform, genre, language, and more
- **Real-time Search**: Instant search across game library
- **Video Previews**: Hover to watch game trailers
- **Data Sync**: Automated background sync with IGDB API
- **Export**: Download calendar as ICS file
- **Responsive Design**: Beautiful UI powered by Mantine

## Architecture

```
Frontend (React + Vite)
    ↓ (Port 3000)
Game API (FastAPI) ← Redis Cache
    ↓ (Port 8000)
PostgreSQL Database
    ↑
Data Sync Worker (Celery) ← IGDB API
    ↑ (Port 8001)
Admin API (FastAPI)
```

### Services

- **Game API** (Port 8000): Public-facing API for games, genres, platforms
- **Admin API** (Port 8001): Administrative operations and data sync triggers
- **Data Sync Worker**: Background Celery worker for IGDB data synchronization
- **Frontend**: React 18 + TypeScript + Mantine UI components
- **PostgreSQL 17**: Primary database
- **Redis 7**: Caching and message broker

## Prerequisites

- **Docker** or **Podman** (for infrastructure)
- **Python 3.12+**
- **Node.js 18+**
- **Git**
- **IGDB API Credentials** ([Get them here](https://api-docs.igdb.com/#account-creation))

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd videogamecalendar

# Copy and configure environment files
cp .env.example .env
cp frontend/.env.example frontend/.env.development

# Edit .env with your IGDB credentials:
# IGDB_CLIENT_ID=your_client_id
# IGDB_CLIENT_SECRET=your_client_secret
# ADMIN_TOKEN=your_secure_token
```

### 2. Start Infrastructure

```bash
# Using Docker
docker-compose up postgres redis -d

# Using Podman
podman compose up postgres redis -d

# Verify services
docker-compose ps  # or: podman compose ps
```

### 3. Install Dependencies

```bash
# Frontend
cd frontend
npm install

# Backend Services
cd ../services/game-api && pip install -r requirements.txt
cd ../admin-api && pip install -r requirements.txt
cd ../data-sync && pip install -r requirements.txt
```

### 4. Run Services

**Option A: VS Code Tasks (Recommended)**

1. Open project in VS Code
2. Press `Ctrl+Shift+P` → "Tasks: Run Task"
3. Select **"🚀 Start All Services"**

**Option B: Manual Start**

```bash
# Terminal 1 - Game API
cd services/game-api
uvicorn main:app --reload --port 8000

# Terminal 2 - Admin API
cd services/admin-api
uvicorn main:app --reload --port 8001

# Terminal 3 - Data Sync Worker
cd services/data-sync
celery -A worker worker --loglevel=info --pool=solo

# Terminal 4 - Frontend
cd frontend
npm run dev
```

**Option C: Docker Compose (Everything)**

```bash
docker-compose up --build
# or with Podman:
podman compose up --build
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **Game API Docs**: http://localhost:8000/docs
- **Admin API Docs**: http://localhost:8001/docs

## Development Guide

### VS Code Integration

This project includes comprehensive VS Code integration for optimal development experience.

#### Available Tasks

Press `Ctrl+Shift+P` → "Tasks: Run Task":

**Main Tasks:**
- 🚀 Start All Services - Start everything with hot reload
- 🐋 Start Infrastructure - PostgreSQL & Redis (auto-detects Docker/Podman)
- 🎮 Start Game API - Game API with hot reload
- ⚙️ Start Admin API - Admin API with hot reload
- ⚛️ Start Frontend - React with hot reload
- 🔄 Start Data Sync Worker - Celery worker with auto-reload

**Setup Tasks:**
- 🛠️ Setup Dev Environment - Install all dependencies
- 📦 Install Frontend Dependencies
- 🐍 Install Backend Dependencies

**Cleanup:**
- ⏹️ Stop All Services
- 🧽 Clean All - Remove containers and volumes

#### Debug Configurations

Press `F5` to start debugging:

- **🎮 Debug Game API** - Debug Game API with breakpoints
- **⚙️ Debug Admin API** - Debug Admin API with breakpoints
- **🔄 Debug Data Sync Worker** - Debug Celery tasks
- **⚛️ Debug Frontend** - React debugging in Chrome
- **🚀 Debug All APIs** - Debug both APIs simultaneously
- **🌟 Debug Full Stack** - Debug everything at once

### Hot Reload

All services support hot reload during development:

- **Frontend**: Instant HMR (Hot Module Replacement)
- **Python APIs**: Auto-restart on file changes (`--reload`)
- **Celery Worker**: Use `--pool=solo` for auto-reload
- **Shared Models**: Changes trigger API restart

### Project Structure

```
videogamecalendar/
├── services/
│   ├── game-api/           # Public game data API
│   ├── admin-api/          # Admin operations API
│   └── data-sync/          # Background IGDB sync worker
├── shared/
│   ├── models/             # SQLAlchemy database models
│   ├── database/           # Database utilities
│   └── utils/              # Shared utilities
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API integration
│   │   ├── hooks/          # Custom React hooks
│   │   ├── context/        # State management
│   │   └── types/          # TypeScript types
│   └── package.json
├── infrastructure/
│   └── init.sql            # Database initialization
├── .vscode/
│   ├── tasks.json          # VS Code tasks
│   └── launch.json         # Debug configurations
├── docker-compose.yml      # Container orchestration
├── .env.example            # Environment template
└── README.md
```

## Configuration

### Environment Variables

**Backend (.env in root):**

```env
# Database
DATABASE_URL=postgresql://gameuser:gamepass@localhost:5432/gamecalendar

# Redis
REDIS_URL=redis://localhost:6379/0

# IGDB API (required)
IGDB_CLIENT_ID=your_twitch_client_id
IGDB_CLIENT_SECRET=your_twitch_client_secret

# Security
ADMIN_TOKEN=your_secure_random_token
```

**Frontend (frontend/.env.development):**

```env
VITE_GAME_API_URL=http://localhost:8000
VITE_ADMIN_API_URL=http://localhost:8001
VITE_USE_MICROSERVICES=true
VITE_ENABLE_CACHING=true
VITE_PAGE_SIZE=20
```

## Python Code Quality

This project uses modern Python linting and security tools:

### Tools

- **Ruff**: Fast Python linter and formatter
- **Mypy**: Static type checker
- **Bandit**: Security vulnerability scanner

### Configuration Files

All Python services include:
- `pyproject.toml` - Ruff and tool configuration
- `mypy.ini` - Type checking rules
- `.bandit` - Security scan configuration

### Running Checks

```bash
# Ruff - Lint and format
cd services/game-api
ruff check .
ruff format .

# Mypy - Type checking
mypy .

# Bandit - Security scan
bandit -r . -c pyproject.toml
```

## API Endpoints

### Game API (Port 8000)

- `GET /games` - List games with filters and pagination
- `GET /games/{id}` - Get game details
- `GET /games/search` - Search games
- `GET /genres` - List all genres
- `GET /platforms` - List all platforms
- `GET /languages` - List all languages
- `GET /companies` - List all companies
- `GET /franchises` - List all franchises
- `GET /health` - Health check

### Admin API (Port 8001)

- `POST /sync/games` - Trigger game data sync
- `POST /sync/full` - Full database sync
- `GET /stats` - Get sync statistics
- `GET /health` - Health check

## Common Issues

### Port Already in Use

```bash
# Find and kill process using port
npx kill-port 8000 8001 3000

# Or change ports in docker-compose.yml
```

### Database Connection Error

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres redis -d
```

### Podman Issues

```bash
# Ensure podman is in PATH
podman --version

# Use 'podman compose' (no hyphen)
podman compose up -d

# For HEALTHCHECK support, build with:
podman build --format docker -f services/game-api/Dockerfile .
```

### Redis Connection Error

```bash
# Restart Redis
docker-compose restart redis

# Clear cache
redis-cli flushall
```

### Python Import Errors

```bash
# Ensure dependencies are installed
pip install -r services/game-api/requirements.txt
pip install -r services/admin-api/requirements.txt
pip install -r services/data-sync/requirements.txt
```

## Production Deployment

### Using Docker Compose

```bash
# Build all services
docker-compose build

# Start in production mode
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers (if needed)
docker-compose up -d --scale data-sync-worker=3
```

### Environment Considerations

- Use strong `ADMIN_TOKEN`
- Enable HTTPS for APIs
- Configure CORS properly
- Set up monitoring (Flower for Celery)
- Regular database backups
- Use production-grade PostgreSQL config

## Monitoring

### Celery Flower

Monitor Celery tasks:

```bash
cd services/data-sync
celery -A worker flower --port=5555
```

Access at: http://localhost:5555

### Health Checks

```bash
# Game API
curl http://localhost:8000/health

# Admin API
curl http://localhost:8001/health

# PostgreSQL
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

## Testing

```bash
# Backend tests
cd services/game-api
pytest

# Frontend tests
cd frontend
npm test

# Run all tests
npm run test:all  # (if configured)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run linters (Ruff, Mypy, Bandit)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database
- **Celery** - Distributed task queue
- **Redis** - Caching and message broker
- **PostgreSQL 17** - Primary database
- **Uvicorn** - ASGI server
- **Python 3.12** - Programming language

### Frontend
- **React 18** - UI framework
- **TypeScript 5** - Type-safe JavaScript
- **Vite 6** - Build tool and dev server
- **Mantine 7** - UI component library
- **Tabler Icons** - Icon set

### DevOps
- **Docker/Podman** - Containerization
- **Docker Compose** - Multi-container orchestration
- **VS Code** - Integrated development
- **Git** - Version control

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the `/docs` endpoint on each API
- **IGDB API**: https://api-docs.igdb.com/

## Acknowledgments

- **IGDB** for providing comprehensive video game data
- **Mantine** for the beautiful UI components
- **FastAPI** for the excellent Python web framework
