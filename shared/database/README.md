# Shared Database and Models Package

This package provides shared database utilities and SQLAlchemy models for the Video Game Calendar microservices architecture.

## Structure

```
shared/database/
├── __init__.py          # Database connection utilities
├── migrations.py        # Alembic migration helpers
└── README.md           # This file

shared/models/
├── __init__.py         # Model imports
├── base.py             # Base model with common fields
├── game.py            # Game model with JSONB optimization
├── genre.py           # Genre model with indexing
├── platform.py        # Platform model with metadata
├── language.py        # Language model
├── region.py          # Region model
├── company.py         # Company model with relationships
└── franchise.py       # Franchise model
```

## Features

### Database Connection
- PostgreSQL connection with connection pooling
- Async session support for FastAPI services
- Health check utilities
- Environment-based configuration

### Models
- PostgreSQL-optimized with JSONB fields
- GIN indexes for complex queries
- Trigram text search capabilities
- Timezone-aware timestamps
- Proper relationship management

### Migration Support
- Alembic integration for schema management
- Automatic migration discovery
- Environment-based database URL configuration

## Usage

### Database Connection

```python
from shared.database import get_db_session, async_session_factory

# Synchronous usage (for Celery workers)
with get_db_session() as session:
    games = session.query(Game).all()

# Asynchronous usage (for FastAPI)
async with async_session_factory() as session:
    games = await session.execute(select(Game))
```

### Models

```python
from shared.models import Game, Genre, Platform

# Create a new game with JSONB data
game = Game(
    name="The Legend of Zelda: Breath of the Wild",
    summary="Open world adventure game",
    metadata={
        "esrb_rating": "E10+",
        "user_score": 9.2,
        "developer": "Nintendo EPD"
    }
)
```

### Migrations

```python
from shared.database.migrations import run_migrations, create_migration

# Run all pending migrations
run_migrations()

# Create a new migration
create_migration("Add user ratings table")
```

## Dependencies

Required packages (install via requirements.txt):
- sqlalchemy[asyncio]
- asyncpg (for PostgreSQL async support)
- alembic (for migrations)
- psycopg2-binary (for PostgreSQL sync support)

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 20)