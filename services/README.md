# Video Game Calendar - Microservices Architecture

## Project Structure

```
videogamecalendar/
├── services/                  # Microservices
│   ├── game-api/             # Game API Service (FastAPI)
│   ├── data-sync/            # Data Synchronization Service (Celery)
│   └── admin-api/            # Admin API Service (FastAPI)
├── shared/                   # Shared components
│   ├── models/               # SQLAlchemy models
│   ├── database/             # Database utilities
│   └── utils/                # Common utilities
├── infrastructure/           # Infrastructure as code
│   ├── docker-compose.yml    # Development environment
│   └── docker-compose.prod.yml # Production environment
├── frontend/                 # React frontend (existing)
├── backend/                  # Legacy backend (to be phased out)
└── migrations/               # Database migrations (Alembic)
```

## Architecture Overview

This microservices architecture separates concerns into distinct services:

1. **Game API Service**: Serves game data to frontend clients
2. **Data Sync Service**: Background tasks for IGDB data synchronization
3. **Admin API Service**: Administrative operations and monitoring
4. **Shared Components**: Common models, database utilities, and helpers

## Technology Stack

- **API Services**: FastAPI (Python)
- **Background Jobs**: Celery + Redis
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker + Docker Compose
- **Migrations**: Alembic

## Getting Started

See individual service READMEs for specific setup instructions.