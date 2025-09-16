"""
Admin API Service
FastAPI-based administrative interface for the Video Game Calendar system
"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as aioredis
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.database import async_session_factory, test_connection
from shared.models import Game, Genre, Platform, Company, Franchise, Language, Region

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Redis connection
redis_client: Optional[aioredis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    global redis_client
    
    # Startup
    logger.info("Starting Admin API service...")
    
    # Test database connection
    if await test_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise RuntimeError("Cannot connect to database")
    
    # Initialize Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    
    try:
        await redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Admin API service...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Video Game Calendar Admin API",
    description="Administrative interface for the Video Game Calendar system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

# Simple authentication check (replace with proper auth)
async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    expected_token = os.getenv("ADMIN_TOKEN", "admin_secret_token")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "admin-api",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database
    try:
        if await test_connection():
            health_status["database"] = "connected"
        else:
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "not configured"
    
    return health_status

# System statistics endpoints
@app.get("/stats/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Get system overview statistics"""
    
    # Get counts for all main entities
    stats_queries = {
        "games": select(func.count(Game.id)),
        "genres": select(func.count(Genre.id)),
        "platforms": select(func.count(Platform.id)),
        "companies": select(func.count(Company.id)),
        "franchises": select(func.count(Franchise.id)),
    }
    
    stats = {}
    for key, query in stats_queries.items():
        result = await db.execute(query)
        stats[key] = result.scalar()
    
    # Get recent activity (games added/updated in last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    recent_games_query = select(func.count(Game.id)).where(Game.created_at >= yesterday)
    recent_result = await db.execute(recent_games_query)
    stats["games_added_24h"] = recent_result.scalar()
    
    updated_games_query = select(func.count(Game.id)).where(Game.updated_at >= yesterday)
    updated_result = await db.execute(updated_games_query)
    stats["games_updated_24h"] = updated_result.scalar()
    
    return {
        "overview": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/stats/database")
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Get database performance statistics"""
    
    try:
        # Get table sizes (PostgreSQL specific)
        table_sizes_query = text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)
        
        result = await db.execute(table_sizes_query)
        table_sizes = [
            {
                "table": row.tablename,
                "size": row.size,
                "size_bytes": row.size_bytes
            }
            for row in result
        ]
        
        # Get index usage statistics
        index_stats_query = text("""
            SELECT 
                indexrelname as index_name,
                relname as table_name,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_tup_read DESC
            LIMIT 10;
        """)
        
        index_result = await db.execute(index_stats_query)
        index_stats = [
            {
                "index": row.index_name,
                "table": row.table_name,
                "reads": row.idx_tup_read,
                "fetches": row.idx_tup_fetch
            }
            for row in index_result
        ]
        
        return {
            "table_sizes": table_sizes,
            "index_usage": index_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        # Fallback for non-PostgreSQL databases
        logger.warning(f"Could not get detailed database stats: {e}")
        return {
            "message": "Database statistics not available",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Cache management endpoints
@app.get("/cache/stats")
async def get_cache_stats(token: str = Depends(verify_admin_token)):
    """Get Redis cache statistics"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        info = await redis_client.info()
        
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "used_memory": info.get("used_memory", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.delete("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear"),
    token: str = Depends(verify_admin_token)
):
    """Clear cache entries"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        if pattern:
            # Clear specific pattern
            keys = await redis_client.keys(pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                return {"message": f"Cleared {deleted} cache entries matching '{pattern}'"}
            else:
                return {"message": f"No cache entries found matching '{pattern}'"}
        else:
            # Clear all cache
            await redis_client.flushdb()
            return {"message": "Cleared all cache entries"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# Data sync management endpoints
@app.post("/sync/games")
async def trigger_game_sync(
    full_sync: bool = Body(False, description="Perform full sync instead of delta"),
    token: str = Depends(verify_admin_token)
):
    """Trigger manual game synchronization"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")
    
    try:
        # Import here to avoid circular dependencies
        from celery import Celery
        
        # Create Celery client
        celery_app = Celery('admin_client', broker=redis_client.connection_pool.connection_kwargs.get('host', 'redis://localhost:6379'))
        
        # Queue sync task
        result = celery_app.send_task('data_sync.sync_games', kwargs={'full_sync': full_sync})
        
        return {
            "message": f"{'Full' if full_sync else 'Delta'} sync task queued",
            "task_id": result.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue sync task: {str(e)}")

@app.post("/sync/games/{igdb_id}")
async def trigger_single_game_sync(
    igdb_id: int,
    token: str = Depends(verify_admin_token)
):
    """Trigger sync for a specific game by IGDB ID"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")
    
    try:
        from celery import Celery
        
        celery_app = Celery('admin_client', broker=redis_client.connection_pool.connection_kwargs.get('host', 'redis://localhost:6379'))
        result = celery_app.send_task('data_sync.sync_single_game', args=[igdb_id])
        
        return {
            "message": f"Single game sync queued for IGDB ID {igdb_id}",
            "task_id": result.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue single game sync: {str(e)}")

# Data management endpoints
@app.get("/data/games/recent")
async def get_recent_games(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of games"),
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Get recently added or updated games"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(Game).where(
        (Game.created_at >= cutoff_date) | (Game.updated_at >= cutoff_date)
    ).order_by(Game.updated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    games = result.scalars().all()
    
    games_data = []
    for game in games:
        games_data.append({
            "id": game.id,
            "igdb_id": game.igdb_id,
            "name": game.name,
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
            "rating": game.rating,
            "total_rating": game.total_rating
        })
    
    return {
        "games": games_data,
        "count": len(games_data),
        "days": days,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/data/games/problematic")
async def get_problematic_games(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Get games with missing or problematic data"""
    
    # Find games with potential issues
    issues = []
    
    # Games without names
    no_name_query = select(Game).where((Game.name == "") | (Game.name.is_(None)))
    no_name_result = await db.execute(no_name_query.limit(10))
    no_name_games = no_name_result.scalars().all()
    
    if no_name_games:
        issues.append({
            "type": "missing_name",
            "count": len(no_name_games),
            "games": [{"id": g.id, "igdb_id": g.igdb_id} for g in no_name_games]
        })
    
    # Games without release dates
    no_date_query = select(Game).where(Game.first_release_date.is_(None))
    no_date_result = await db.execute(no_date_query.limit(10))
    no_date_games = no_date_result.scalars().all()
    
    if no_date_games:
        issues.append({
            "type": "missing_release_date",
            "count": len(no_date_games),
            "games": [{"id": g.id, "igdb_id": g.igdb_id, "name": g.name} for g in no_date_games]
        })
    
    # Games without genres or platforms
    no_relations_query = select(Game).outerjoin(Game.genres).outerjoin(Game.platforms).group_by(Game.id).having(
        (func.count(Genre.id) == 0) & (func.count(Platform.id) == 0)
    )
    no_relations_result = await db.execute(no_relations_query.limit(10))
    no_relations_games = no_relations_result.scalars().all()
    
    if no_relations_games:
        issues.append({
            "type": "missing_relations",
            "count": len(no_relations_games),
            "games": [{"id": g.id, "igdb_id": g.igdb_id, "name": g.name} for g in no_relations_games]
        })
    
    return {
        "issues": issues,
        "timestamp": datetime.utcnow().isoformat()
    }

# System maintenance endpoints
@app.post("/maintenance/cleanup")
async def trigger_cleanup(token: str = Depends(verify_admin_token)):
    """Trigger data cleanup task"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")
    
    try:
        from celery import Celery
        
        celery_app = Celery('admin_client', broker=redis_client.connection_pool.connection_kwargs.get('host', 'redis://localhost:6379'))
        result = celery_app.send_task('data_sync.cleanup_old_data')
        
        return {
            "message": "Cleanup task queued",
            "task_id": result.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue cleanup task: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )