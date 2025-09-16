# Video Game Calendar Microservices Architecture

## Overview

This document provides comprehensive documentation for the microservices architecture implementation of the Video Game Calendar application. The system has been transformed from a monolithic Flask application to a distributed microservices architecture using modern technologies and best practices.

## Architecture Overview

### System Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Game API      │    │   Admin API     │
│   (React/Vite)  │────│   (FastAPI)     │    │   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              │                        │
        ┌─────────────────────┼────────────────────────┘
        │                     │
        │     ┌─────────────────┐    ┌─────────────────┐
        │     │   Data Sync     │    │     Redis       │
        │     │   (Celery)      │────│   (Cache/MQ)    │
        │     │                 │    │   Port: 6379    │
        │     └─────────────────┘    └─────────────────┘
        │                     │
        │                     │
   ┌─────────────────────────────────────────┐
   │           PostgreSQL                    │
   │         (Primary Database)              │
   │           Port: 5432                    │
   └─────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite build tool
- Mantine UI components
- Enhanced service layer with microservices support

**Backend Services:**
- **Game API**: FastAPI with async support
- **Admin API**: FastAPI with administrative endpoints
- **Data Sync**: Celery workers for background processing

**Infrastructure:**
- **Database**: PostgreSQL 15 with JSONB optimization
- **Cache/Message Broker**: Redis 7
- **Orchestration**: Docker Compose
- **Migrations**: Alembic

## Services Documentation

### 1. Game API Service (Port 8000)

**Purpose**: Primary API for game-related operations

**Endpoints:**
- `GET /games` - Paginated game listing with filtering
- `GET /games/{id}` - Detailed game information
- `GET /games/search` - Full-text game search
- `GET /genres` - Genre reference data
- `GET /platforms` - Platform reference data
- `GET /health` - Service health check

**Features:**
- Async FastAPI with high performance
- Redis caching with configurable TTL
- PostgreSQL trigram search
- Comprehensive error handling
- API documentation at `/docs`

**Configuration:**
```bash
DATABASE_URL=postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=*
```

### 2. Admin API Service (Port 8001)

**Purpose**: Administrative interface for system management

**Endpoints:**
- `GET /stats/overview` - System statistics
- `GET /stats/database` - Database performance metrics
- `POST /sync/games` - Trigger data synchronization
- `GET /cache/stats` - Cache performance
- `DELETE /cache/clear` - Cache management

**Features:**
- Token-based authentication
- System monitoring capabilities
- Manual sync triggers
- Database performance insights

**Configuration:**
```bash
ADMIN_TOKEN=your_secure_admin_token
DATABASE_URL=postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar
REDIS_URL=redis://localhost:6379
```

### 3. Data Sync Service (Celery Workers)

**Purpose**: Background data synchronization with IGDB API

**Features:**
- Scheduled daily full sync (2 AM)
- Hourly delta sync for updates
- Weekly data cleanup
- Error handling with retry logic
- IGDB API integration

**Queues:**
- `data_sync`: Regular synchronization tasks
- `priority`: High-priority single game syncs
- `maintenance`: Cleanup and maintenance

**Configuration:**
```bash
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar
IGDB_CLIENT_ID=your_igdb_client_id
IGDB_CLIENT_SECRET=your_igdb_client_secret
```

## Database Schema

### PostgreSQL Optimization

The database has been optimized for the microservices architecture:

**Key Features:**
- JSONB fields for flexible metadata storage
- GIN indexes for JSON and text search
- Trigram indexes for fuzzy text search
- Connection pooling for performance
- Proper foreign key relationships

**Main Tables:**
- `games` - Core game information with JSONB metadata
- `genres` - Game genres with text indexing
- `platforms` - Gaming platforms
- `companies` - Game companies and developers
- `franchises` - Game franchises
- Association tables for many-to-many relationships

## Deployment Guide

### Prerequisites

**System Requirements:**
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

**Environment Setup:**
```bash
# Clone repository
git clone <repository-url>
cd videogamecalendar

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Development Deployment

**1. Infrastructure Setup:**
```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Verify services
docker-compose ps
```

**2. Database Migration:**
```bash
# Install migration dependencies
pip install -r scripts/requirements.txt

# Initialize Alembic
python scripts/setup_migrations.py init

# Create initial migration
python scripts/setup_migrations.py create-initial

# Apply migrations
python scripts/setup_migrations.py migrate

# Optional: Migrate existing SQLite data
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db
```

**3. Backend Services:**

**Game API:**
```bash
cd services/game-api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Admin API:**
```bash
cd services/admin-api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Data Sync Worker:**
```bash
cd services/data-sync
pip install -r requirements.txt

# Start worker
celery -A worker worker --loglevel=info

# Start scheduler (separate terminal)
celery -A worker beat --loglevel=info

# Optional: Start monitoring
celery -A worker flower
```

**4. Frontend:**
```bash
cd frontend
npm install

# Copy environment config
cp .env.example .env.development

# Start development server
npm run dev
```

### Production Deployment

**1. Docker Compose Production:**
```bash
# Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers as needed
docker-compose up --scale data-sync-worker=3
```

**2. Environment Configuration:**
```bash
# Production environment variables
DATABASE_URL=postgresql://gameuser:securepassword@postgres:5432/videogame_calendar
REDIS_URL=redis://redis:6379
IGDB_CLIENT_ID=your_production_client_id
IGDB_CLIENT_SECRET=your_production_client_secret
ADMIN_TOKEN=your_very_secure_admin_token
```

**3. SSL/TLS Setup:**
- Configure reverse proxy (nginx/traefik)
- Set up SSL certificates
- Update CORS origins for production domains

## Monitoring and Maintenance

### Health Checks

**Service Health:**
- Game API: `GET http://localhost:8000/health`
- Admin API: `GET http://localhost:8001/health`
- Celery: `celery -A worker inspect ping`

**Database Health:**
```sql
-- Check connection count
SELECT count(*) FROM pg_stat_activity;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public';
```

### Performance Monitoring

**Metrics to Monitor:**
- API response times
- Cache hit rates
- Database query performance
- Celery task completion rates
- System resource usage

**Tools:**
- Flower for Celery monitoring: `http://localhost:5555`
- FastAPI docs: `http://localhost:8000/docs`
- Admin dashboard: `http://localhost:8001/docs`

### Backup Strategy

**Database Backups:**
```bash
# Create backup
pg_dump -h localhost -U gameuser -d videogame_calendar > backup_$(date +%Y%m%d).sql

# Restore backup
psql -h localhost -U gameuser -d videogame_calendar < backup_20240101.sql
```

**Redis Backups:**
```bash
# Redis automatically saves to dump.rdb
# Copy dump.rdb for backup
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

## Migration from Legacy System

### Step-by-Step Migration

**1. Parallel Deployment:**
- Deploy microservices alongside existing Flask app
- Use feature flags to gradually migrate traffic
- Monitor performance and stability

**2. Data Migration:**
- Export SQLite data using migration scripts
- Validate data integrity in PostgreSQL
- Verify all relationships and indexes

**3. Frontend Migration:**
- Update API endpoints gradually
- Use enhanced service layer for new features
- Maintain backward compatibility during transition

**4. Legacy Deprecation:**
- Monitor usage of legacy endpoints
- Redirect traffic to new services
- Remove legacy code after full migration

### Rollback Plan

**If Issues Occur:**
1. **Traffic Rollback**: Route traffic back to legacy Flask app
2. **Data Rollback**: Restore from SQLite backup if needed
3. **Service Rollback**: Stop microservices and restart Flask app
4. **Investigation**: Analyze logs and fix issues before retry

## Security Considerations

### Authentication and Authorization
- Admin API requires token authentication
- Environment-based security configuration
- CORS properly configured for production

### Data Security
- PostgreSQL with proper user permissions
- Redis AUTH for cache security
- Sensitive data in environment variables only

### Network Security
- Internal service communication
- Proper firewall configuration
- SSL/TLS for external traffic

## Performance Optimization

### Caching Strategy
- **Game Lists**: 5-minute cache
- **Individual Games**: 10-minute cache
- **Reference Data**: 30-minute cache
- **Search Results**: 10-minute cache

### Database Optimization
- Connection pooling (10-20 connections)
- Proper indexing for common queries
- JSONB for flexible metadata
- Regular VACUUM and ANALYZE

### Service Optimization
- Async FastAPI for high concurrency
- Background processing for heavy operations
- Efficient pagination for large datasets
- Proper error handling and timeouts

## Troubleshooting

### Common Issues

**1. Database Connection Errors:**
```bash
# Check PostgreSQL status
docker-compose ps postgres
docker-compose logs postgres

# Verify connection
psql -h localhost -U gameuser -d videogame_calendar
```

**2. Redis Connection Issues:**
```bash
# Check Redis status
docker-compose ps redis
redis-cli ping
```

**3. Service Startup Problems:**
```bash
# Check service logs
docker-compose logs game-api
docker-compose logs admin-api
docker-compose logs data-sync-worker
```

**4. Migration Issues:**
```bash
# Check migration status
python scripts/setup_migrations.py history

# Force migration
python scripts/setup_migrations.py migrate
```

### Log Locations

**Development:**
- Service logs in terminal output
- Docker logs: `docker-compose logs [service-name]`

**Production:**
- Service logs in `/var/log/`
- Centralized logging recommended (ELK stack)

## Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Standards
- Python: Black formatting, type hints
- TypeScript: ESLint, Prettier
- API: OpenAPI documentation
- Tests: Unit and integration tests

## Support and Contacts

For issues, questions, or contributions:
- Create GitHub issues for bugs
- Use discussions for questions
- Follow contribution guidelines
- Check documentation first

---

This microservices architecture provides a scalable, maintainable foundation for the Video Game Calendar application with modern best practices and comprehensive tooling.