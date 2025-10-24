# Video Game Calendar - Complete Documentation

## Overview

The Video Game Calendar is a modern web application that displays upcoming video game releases. It has evolved from a monolithic Flask application to a scalable microservices architecture using React frontend, FastAPI services, PostgreSQL database, and Redis caching.

## Architecture

### Microservices Architecture
```
Frontend (React/Vite) → Game API (FastAPI) → PostgreSQL
        ↓                   ↓                   ↑
    Admin API (FastAPI) → Redis Cache ←→ Data Sync (Celery)
```

### Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Mantine UI
- **Backend Services**: FastAPI with async support
- **Database**: PostgreSQL 15 with JSONB optimization
- **Cache/Message Queue**: Redis 7
- **Background Jobs**: Celery workers
- **Containerization**: Docker & Docker Compose
- **Migrations**: Alembic

## Project Structure

```
videogamecalendar/
├── services/
│   ├── game-api/          # Primary game data API (Port 8000)
│   ├── admin-api/         # Administrative interface (Port 8001)
│   └── data-sync/         # Background IGDB synchronization (Celery)
├── shared/
│   ├── models/            # PostgreSQL SQLAlchemy models
│   ├── database/          # Database utilities and connection pooling
│   └── utils/             # Common utilities
├── frontend/              # React application (Port 3000)
├── infrastructure/        # Docker Compose configurations
├── scripts/              # Migration and setup scripts
└── backend/              # Legacy Flask app (being phased out)
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd videogamecalendar

# Copy environment files
cp .env.example .env
# Edit .env with your IGDB API credentials
```

### 2. Infrastructure (Recommended: Docker)
```bash
# Start all services with Docker
docker-compose up --build -d

# Or start infrastructure only
docker-compose up postgres redis -d
```

### 3. Manual Development Setup (Alternative)

#### Database Setup
```bash
# Install migration dependencies
pip install -r scripts/requirements.txt

# Initialize database
python scripts/setup_migrations.py init
python scripts/setup_migrations.py create-initial
python scripts/setup_migrations.py migrate

# Optional: Migrate existing SQLite data
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db
```

#### Backend Services (3 terminals)
```bash
# Terminal 1 - Game API
cd services/game-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 - Admin API
cd services/admin-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Terminal 3 - Data Sync Worker
cd services/data-sync
pip install -r requirements.txt
celery -A worker worker --loglevel=info
```

#### Frontend
```bash
# Terminal 4 - Frontend
cd frontend
npm install
npm run dev
```

## Service Documentation

### Game API Service (Port 8000)
**Purpose**: Primary API for game data operations

**Key Endpoints**:
- `GET /games` - Paginated game listing with filtering
- `GET /games/{id}` - Detailed game information
- `GET /games/search` - Full-text search
- `GET /genres` - Genre reference data
- `GET /platforms` - Platform reference data
- `GET /health` - Service health check

**Features**:
- Redis caching with configurable TTL
- PostgreSQL trigram search
- Async FastAPI for high performance
- API documentation at `/docs`

### Admin API Service (Port 8001)
**Purpose**: Administrative interface and system management

**Key Endpoints**:
- `GET /stats/overview` - System statistics
- `POST /sync/games` - Trigger data synchronization
- `DELETE /cache/clear` - Cache management
- `GET /stats/database` - Database metrics

**Features**:
- Token-based authentication
- System monitoring capabilities
- Manual sync triggers

### Data Sync Service (Celery)
**Purpose**: Background data synchronization with IGDB API

**Features**:
- Scheduled daily full sync (2 AM)
- Hourly delta sync for updates
- Weekly data cleanup
- IGDB API integration with retry logic

**Queues**:
- `data_sync` - Regular synchronization
- `priority` - High-priority tasks
- `maintenance` - Cleanup operations

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar

# Redis
REDIS_URL=redis://localhost:6379

# IGDB API (Required for data sync)
IGDB_CLIENT_ID=your_igdb_client_id
IGDB_CLIENT_SECRET=your_igdb_client_secret

# Admin Authentication
ADMIN_TOKEN=your_secure_admin_token

# CORS (for production)
CORS_ORIGINS=https://yourdomain.com
```

## Verification & Testing

### Service Health Checks
```bash
# Check all services
curl http://localhost:8000/health  # Game API
curl http://localhost:8001/health  # Admin API

# Test endpoints
curl http://localhost:8000/games?limit=5
curl http://localhost:8000/genres
```

### Access Points
- **Frontend**: http://localhost:3000
- **Game API Docs**: http://localhost:8000/docs
- **Admin API Docs**: http://localhost:8001/docs
- **Celery Monitor**: `celery -A worker flower` (http://localhost:5555)

## SSL Support (Legacy)

For environments requiring SSL (e.g., ZScaler):

### Windows
```powershell
# Run with SSL support
.\run_backend.ps1

# Run without SSL
.\run_backend.ps1 -NoSSL
```

### Linux/Mac
```bash
chmod +x run_backend_ssl.sh
./run_backend_ssl.sh
```

The SSL implementation automatically detects ZScaler Root.pem certificates and configures appropriate SSL settings.

## Database Features

### PostgreSQL Optimizations
- **JSONB fields** for flexible metadata storage
- **GIN indexes** for JSON and text search
- **Trigram indexes** for fuzzy text search
- **Connection pooling** for performance
- **Foreign key relationships** for data integrity

### Main Tables
- `games` - Core game information with JSONB metadata
- `genres` - Game genres with text indexing
- `platforms` - Gaming platforms
- `companies` - Game developers/publishers
- `franchises` - Game series

## Performance & Caching

### Caching Strategy
- **Game Lists**: 5-minute cache
- **Individual Games**: 10-minute cache
- **Reference Data**: 30-minute cache
- **Search Results**: 10-minute cache

### Database Performance
- Connection pooling (10-20 connections)
- Proper indexing for common queries
- JSONB for flexible metadata
- Regular VACUUM and ANALYZE

## Monitoring & Maintenance

### Useful Commands
```bash
# Docker operations
docker-compose ps                    # View all services
docker-compose logs -f game-api      # View service logs
docker-compose restart redis        # Restart specific service
docker-compose down -v              # Clean shutdown with volumes

# Database operations
psql -h localhost -U gameuser -d videogame_calendar
redis-cli ping

# Celery monitoring
celery -A worker inspect ping       # Check workers
celery -A worker flower             # Web monitoring interface
```

### Backup Strategy
```bash
# Database backup
pg_dump -h localhost -U gameuser -d videogame_calendar > backup_$(date +%Y%m%d).sql

# Redis backup (automatic to dump.rdb)
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Check PostgreSQL
docker-compose logs postgres
psql -h localhost -U gameuser -d videogame_calendar
```

**Redis Connection Issues**:
```bash
docker-compose ps redis
redis-cli ping
```

**Port Conflicts**:
```bash
# Check what's using ports
netstat -tlnp | grep :8000
netstat -tlnp | grep :5432
```

**Service Startup Problems**:
```bash
# Check service logs
docker-compose logs game-api
docker-compose logs admin-api
docker-compose logs data-sync-worker
```

## Migration from Legacy

### Data Migration Options

**Option 1: Fresh Start (Recommended)**
1. Follow Quick Start guide
2. Use Admin API to trigger initial IGDB sync
3. Start with clean, optimized database

**Option 2: Migrate Existing Data**
1. Run SQLite migration script:
   ```bash
   python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db
   ```
2. Verify data integrity
3. Gradually transition to new services

### Rollback Plan
If issues occur during migration:
1. Route traffic back to legacy Flask app
2. Restore from SQLite backup if needed
3. Stop microservices and restart Flask app
4. Analyze logs and fix issues before retry

## Security

### Authentication & Authorization
- Admin API requires token authentication
- Environment-based security configuration
- CORS properly configured for production

### Data Security
- PostgreSQL with proper user permissions
- Redis AUTH for cache security
- Sensitive data in environment variables only

### Network Security
- Internal service communication
- SSL/TLS for external traffic
- Proper firewall configuration

## Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Standards
- **Python**: Black formatting, type hints
- **TypeScript**: ESLint, Prettier
- **API**: OpenAPI documentation
- **Tests**: Unit and integration tests

## Support

For issues, questions, or contributions:
- Create GitHub issues for bugs
- Use discussions for questions
- Follow contribution guidelines
- Check this documentation first

---

This documentation covers the complete Video Game Calendar application with its modern microservices architecture, providing a scalable and maintainable foundation for future development.