# Data Sync Service

Celery-based background service for synchronizing data from the IGDB API to the PostgreSQL database.

## Features

- **Background Processing**: Celery workers for non-blocking data synchronization
- **Scheduled Tasks**: Automatic daily full sync and hourly delta sync
- **Delta Synchronization**: Only sync data that has changed since last update
- **Error Handling**: Retry logic with exponential backoff
- **Reference Data Management**: Automatic sync of genres, platforms, and companies
- **Single Game Sync**: On-demand synchronization of individual games
- **Data Cleanup**: Weekly maintenance tasks for data hygiene
- **Health Monitoring**: Built-in health check tasks

## Task Types

### Scheduled Tasks
- **Daily Full Sync**: Complete synchronization of all games (2 AM daily)
- **Hourly Delta Sync**: Sync only games updated in the last hour
- **Weekly Cleanup**: Data maintenance and cleanup (Sunday 3 AM)

### On-Demand Tasks
- **Single Game Sync**: Sync specific game by IGDB ID
- **Reference Data Sync**: Sync genres, platforms, and companies
- **Health Check**: Service status monitoring

## Queue Management

- `data_sync`: Regular synchronization tasks
- `priority`: High-priority single game syncs
- `maintenance`: Cleanup and maintenance tasks

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis broker and backend URL
- `IGDB_CLIENT_ID`: IGDB API client ID
- `IGDB_CLIENT_SECRET`: IGDB API client secret

### IGDB API Integration
The service integrates with the IGDB (Internet Game Database) API to fetch:
- Game information and metadata
- Genres and categories
- Gaming platforms
- Company information
- Release dates and ratings
- Media assets (covers, screenshots)

## Data Processing

### Game Sync Process
1. Authenticate with IGDB API
2. Sync reference data (genres, platforms, companies)
3. Fetch games in batches
4. Process relationships and metadata
5. Store optimized data in PostgreSQL with JSONB fields
6. Update search indexes

### Delta Sync Strategy
- Track last sync timestamps
- Only fetch games modified since last sync
- Efficient processing of incremental changes
- Fallback to full sync if delta sync fails

## Running the Service

### Docker (Recommended)
```bash
# Start worker
docker-compose up data-sync-worker

# Start beat scheduler
docker-compose up data-sync-beat
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start worker
celery -A worker worker --loglevel=info

# Start beat scheduler (separate terminal)
celery -A worker beat --loglevel=info

# Monitor tasks (separate terminal)
celery -A worker flower
```

## Monitoring

### Flower Web UI
Access Celery Flower at `http://localhost:5555` for:
- Task monitoring and management
- Worker status and statistics
- Queue management
- Task history and results

### Health Checks
The service provides health check tasks that can be called periodically:
```python
from worker import health_check
result = health_check.delay()
```

## Error Handling

- **Retry Logic**: Failed tasks are retried with exponential backoff
- **Dead Letter Queue**: Failed tasks after max retries are logged
- **Circuit Breaker**: API failures trigger fallback behavior
- **Monitoring**: All errors are logged with full context

## Data Integrity

- **Transaction Management**: Database operations use proper transactions
- **Relationship Integrity**: Foreign key constraints are maintained
- **Duplicate Prevention**: IGDB IDs ensure uniqueness
- **Cleanup Tasks**: Regular maintenance prevents data bloat

## Performance Optimization

- **Batch Processing**: Games are processed in configurable batches
- **Connection Pooling**: Database connections are pooled and reused
- **Async Processing**: Non-blocking I/O where possible
- **Selective Updates**: Only changed fields are updated

## Security

- **API Key Management**: Secure storage of IGDB credentials
- **Input Validation**: All external data is validated
- **SQL Injection Prevention**: Parameterized queries only
- **Rate Limiting**: Respect IGDB API rate limits