# Game API Service

FastAPI-based microservice for handling game-related API requests in the Video Game Calendar application.

## Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Async Support**: Full asynchronous operation for high performance
- **Redis Caching**: Intelligent caching with configurable expiry times
- **PostgreSQL Integration**: Optimized queries with relationship loading
- **Full-Text Search**: PostgreSQL trigram similarity search
- **Pagination**: Efficient pagination for large datasets
- **Health Checks**: Built-in health monitoring endpoints
- **CORS Support**: Configurable cross-origin resource sharing
- **Error Handling**: Comprehensive error handling and logging

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Games
- `GET /games` - Paginated game list with filtering
  - Query parameters: `page`, `limit`, `search`, `genre_id`, `platform_id`, `release_year`
- `GET /games/{game_id}` - Detailed game information
- `GET /games/search` - Full-text search for games

### Reference Data
- `GET /genres` - All genres with game counts
- `GET /platforms` - All platforms with game counts

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (optional)
- `DB_POOL_SIZE`: Database connection pool size
- `DB_MAX_OVERFLOW`: Maximum overflow connections

### Docker Configuration
The service runs on port 8000 and is configured via docker-compose.yml in the infrastructure directory.

## Caching Strategy

- **Game Lists**: 5 minutes (300 seconds)
- **Individual Games**: 10 minutes (600 seconds)
- **Search Results**: 10 minutes (600 seconds)
- **Reference Data**: 30 minutes (1800 seconds)

## Performance Optimizations

1. **Async Database Operations**: All database queries are asynchronous
2. **Eager Loading**: Relationships are loaded efficiently using `selectinload`
3. **Connection Pooling**: PostgreSQL connections are pooled and reused
4. **Redis Caching**: Frequently accessed data is cached
5. **Query Optimization**: Indexes and trigram search for fast text queries

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar"
export REDIS_URL="redis://localhost:6379"

# Run the service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
When running, visit:
- `http://localhost:8000/docs` - Interactive Swagger UI
- `http://localhost:8000/redoc` - ReDoc documentation

## Error Handling

The service includes comprehensive error handling:
- HTTP exceptions with proper status codes
- Database connection error handling
- Redis fallback when caching is unavailable
- Detailed logging for debugging

## Health Monitoring

The `/health` endpoint provides status for:
- Overall service health
- Database connection status
- Redis connection status

Example response:
```json
{
  "status": "healthy",
  "service": "game-api",
  "database": "connected",
  "redis": "connected"
}
```