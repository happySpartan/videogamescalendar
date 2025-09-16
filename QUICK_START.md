# Quick Start Guide

## 🚀 Getting Started with Microservices Architecture

This guide will help you quickly set up and run the new microservices architecture for the Video Game Calendar application.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

## 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd videogamecalendar

# Copy environment files
cp frontend/.env.example frontend/.env.development
cp .env.example .env

# Edit .env files with your configuration
```

## 2. Infrastructure (Database & Cache)

```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Verify services are running
docker-compose ps
```

## 3. Database Setup

```bash
# Install migration dependencies
pip install -r scripts/requirements.txt

# Initialize database schema
python scripts/setup_migrations.py init
python scripts/setup_migrations.py create-initial
python scripts/setup_migrations.py migrate

# Optional: Migrate existing SQLite data
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db
```

## 4. Backend Services

### Terminal 1 - Game API
```bash
cd services/game-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Terminal 2 - Admin API
```bash
cd services/admin-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Terminal 3 - Data Sync Worker
```bash
cd services/data-sync
pip install -r requirements.txt
celery -A worker worker --loglevel=info
```

### Terminal 4 - Data Sync Scheduler (Optional)
```bash
cd services/data-sync
celery -A worker beat --loglevel=info
```

## 5. Frontend

### Terminal 5 - Frontend
```bash
cd frontend
npm install
npm run dev
```

## 6. Verify Installation

### Check Services
- Frontend: http://localhost:3000
- Game API: http://localhost:8000/docs
- Admin API: http://localhost:8001/docs
- Celery Monitor: `celery -A worker flower` (http://localhost:5555)

### Test Endpoints
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health

# API test
curl http://localhost:8000/games?limit=5
curl http://localhost:8000/genres
```

## Docker Compose Alternative

If you prefer to run everything with Docker:

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## Common Issues

### Database Connection Error
```bash
# Check PostgreSQL
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres redis -d
# Re-run migrations
```

### Port Conflicts
```bash
# Check what's using ports
netstat -tlnp | grep :8000
netstat -tlnp | grep :5432

# Kill processes or change ports in docker-compose.yml
```

### Cache Issues
```bash
# Clear Redis cache
redis-cli flushall

# Or restart Redis
docker-compose restart redis
```

## Next Steps

1. **Explore APIs**: Visit http://localhost:8000/docs and http://localhost:8001/docs
2. **Admin Features**: Set up admin token in .env to access admin endpoints
3. **Data Sync**: Configure IGDB API credentials for automatic data updates
4. **Monitoring**: Set up Flower for Celery monitoring
5. **Production**: Follow the production deployment guide in MICROSERVICES_ARCHITECTURE.md

## Architecture Overview

```
Frontend (3000) → Game API (8000) → PostgreSQL (5432)
                ↓
              Admin API (8001) → Redis (6379)
                ↓
              Data Sync (Celery)
```

## Useful Commands

```bash
# View all services
docker-compose ps

# Restart a service
docker-compose restart game-api

# View service logs
docker-compose logs -f data-sync-worker

# Stop all services
docker-compose down

# Clean everything (including data)
docker-compose down -v --remove-orphans
```

## Development Tips

- Use `--reload` flag for auto-restart during development
- Check service logs regularly for errors
- Use Redis CLI to inspect cache: `redis-cli`
- Monitor database with pgAdmin or command line tools
- Enable debug mode in .env for detailed logging

Need help? Check the full documentation in `MICROSERVICES_ARCHITECTURE.md` or create an issue!