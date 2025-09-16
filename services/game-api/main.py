"""
FastAPI Game API Service
Main application entry point for the Game API microservice
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import asyncio

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import shared models and database utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database import async_session_factory, test_connection
from shared.models import Game, Genre, Platform, Company, Franchise, Language, Region

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_client: Optional[aioredis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    global redis_client
    
    # Startup
    logger.info("Starting Game API service...")
    
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
    logger.info("Shutting down Game API service...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Video Game Calendar API",
    description="Game API microservice for video game calendar application",
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

# Dependency to get Redis client
async def get_redis():
    if redis_client:
        return redis_client
    return None

# Utility function for caching
async def get_cached_or_fetch(cache_key: str, fetch_func, expiry: int = 300):
    """Get data from cache or fetch and cache it"""
    if not redis_client:
        return await fetch_func()
    
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            import json
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Cache read error for {cache_key}: {e}")
    
    # Fetch fresh data
    data = await fetch_func()
    
    # Cache the result
    try:
        import json
        await redis_client.setex(cache_key, expiry, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Cache write error for {cache_key}: {e}")
    
    return data

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "game-api",
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

# Game endpoints
@app.get("/games", response_model=Dict[str, Any])
async def get_games(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    genre_id: Optional[int] = Query(None, description="Filter by genre ID"),
    platform_id: Optional[int] = Query(None, description="Filter by platform ID"),
    release_year: Optional[int] = Query(None, description="Filter by release year")
):
    """Get paginated list of games with optional filtering"""
    
    cache_key = f"games:page:{page}:limit:{limit}:search:{search}:genre:{genre_id}:platform:{platform_id}:year:{release_year}"
    
    async def fetch_games():
        # Build query
        query = select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.platforms),
            selectinload(Game.companies)
        )
        
        # Apply filters
        filters = []
        if search:
            filters.append(Game.name.ilike(f"%{search}%"))
        
        if genre_id:
            filters.append(Game.genres.any(Genre.id == genre_id))
        
        if platform_id:
            filters.append(Game.platforms.any(Platform.id == platform_id))
        
        if release_year:
            filters.append(func.extract('year', Game.first_release_date) == release_year)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Add pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        games = result.scalars().all()
        
        # Get total count for pagination
        count_query = select(func.count(Game.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # Format response
        games_data = []
        for game in games:
            game_dict = {
                "id": game.id,
                "name": game.name,
                "summary": game.summary,
                "storyline": game.storyline,
                "first_release_date": game.first_release_date.isoformat() if game.first_release_date else None,
                "rating": game.rating,
                "rating_count": game.rating_count,
                "total_rating": game.total_rating,
                "total_rating_count": game.total_rating_count,
                "cover_url": game.cover_url,
                "screenshots": game.screenshots,
                "metadata": game.metadata,
                "genres": [{"id": g.id, "name": g.name} for g in game.genres],
                "platforms": [{"id": p.id, "name": p.name} for p in game.platforms],
                "companies": [{"id": c.id, "name": c.name} for c in game.companies],
                "created_at": game.created_at.isoformat(),
                "updated_at": game.updated_at.isoformat()
            }
            games_data.append(game_dict)
        
        return {
            "games": games_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
    
    return await get_cached_or_fetch(cache_key, fetch_games, expiry=300)

@app.get("/games/{game_id}", response_model=Dict[str, Any])
async def get_game_by_id(
    game_id: int = Path(..., description="Game ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed game information by ID"""
    
    cache_key = f"game:{game_id}"
    
    async def fetch_game():
        query = select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.platforms),
            selectinload(Game.companies),
            selectinload(Game.franchises),
            selectinload(Game.languages),
            selectinload(Game.regions)
        ).where(Game.id == game_id)
        
        result = await db.execute(query)
        game = result.scalar_one_or_none()
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Format detailed response
        return {
            "id": game.id,
            "igdb_id": game.igdb_id,
            "name": game.name,
            "slug": game.slug,
            "summary": game.summary,
            "storyline": game.storyline,
            "first_release_date": game.first_release_date.isoformat() if game.first_release_date else None,
            "rating": game.rating,
            "rating_count": game.rating_count,
            "total_rating": game.total_rating,
            "total_rating_count": game.total_rating_count,
            "aggregated_rating": game.aggregated_rating,
            "aggregated_rating_count": game.aggregated_rating_count,
            "cover_url": game.cover_url,
            "screenshots": game.screenshots,
            "videos": game.videos,
            "websites": game.websites,
            "metadata": game.metadata,
            "genres": [{"id": g.id, "name": g.name, "slug": g.slug} for g in game.genres],
            "platforms": [{"id": p.id, "name": p.name, "abbreviation": p.abbreviation} for p in game.platforms],
            "companies": [{"id": c.id, "name": c.name, "description": c.description} for c in game.companies],
            "franchises": [{"id": f.id, "name": f.name, "slug": f.slug} for f in game.franchises],
            "languages": [{"id": l.id, "name": l.name, "native_name": l.native_name} for l in game.languages],
            "regions": [{"id": r.id, "name": r.name, "code": r.code} for r in game.regions],
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat()
        }
    
    return await get_cached_or_fetch(cache_key, fetch_game, expiry=600)

@app.get("/games/search", response_model=Dict[str, Any])
async def search_games(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """Full-text search for games"""
    
    cache_key = f"search:games:{q}:{limit}"
    
    async def fetch_search_results():
        # Use PostgreSQL full-text search with trigram similarity
        query = select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.platforms)
        ).where(
            or_(
                Game.name.ilike(f"%{q}%"),
                Game.summary.ilike(f"%{q}%"),
                func.similarity(Game.name, q) > 0.1
            )
        ).order_by(
            func.similarity(Game.name, q).desc(),
            Game.total_rating_count.desc().nullslast()
        ).limit(limit)
        
        result = await db.execute(query)
        games = result.scalars().all()
        
        games_data = []
        for game in games:
            games_data.append({
                "id": game.id,
                "name": game.name,
                "summary": game.summary,
                "first_release_date": game.first_release_date.isoformat() if game.first_release_date else None,
                "rating": game.rating,
                "cover_url": game.cover_url,
                "genres": [g.name for g in game.genres[:3]],  # Limit to top 3 genres
                "platforms": [p.name for p in game.platforms[:3]]  # Limit to top 3 platforms
            })
        
        return {
            "query": q,
            "results": games_data,
            "count": len(games_data)
        }
    
    return await get_cached_or_fetch(cache_key, fetch_search_results, expiry=600)

# Genre endpoints
@app.get("/genres", response_model=List[Dict[str, Any]])
async def get_genres(db: AsyncSession = Depends(get_db)):
    """Get all genres"""
    
    cache_key = "genres:all"
    
    async def fetch_genres():
        query = select(Genre).order_by(Genre.name)
        result = await db.execute(query)
        genres = result.scalars().all()
        
        return [
            {
                "id": genre.id,
                "name": genre.name,
                "slug": genre.slug,
                "description": genre.description,
                "game_count": len(genre.games) if hasattr(genre, 'games') else 0
            }
            for genre in genres
        ]
    
    return await get_cached_or_fetch(cache_key, fetch_genres, expiry=1800)

# Platform endpoints
@app.get("/platforms", response_model=List[Dict[str, Any]])
async def get_platforms(db: AsyncSession = Depends(get_db)):
    """Get all platforms"""
    
    cache_key = "platforms:all"
    
    async def fetch_platforms():
        query = select(Platform).order_by(Platform.name)
        result = await db.execute(query)
        platforms = result.scalars().all()
        
        return [
            {
                "id": platform.id,
                "name": platform.name,
                "abbreviation": platform.abbreviation,
                "alternative_names": platform.alternative_names,
                "generation": platform.generation,
                "platform_family": platform.platform_family,
                "game_count": len(platform.games) if hasattr(platform, 'games') else 0
            }
            for platform in platforms
        ]
    
    return await get_cached_or_fetch(cache_key, fetch_platforms, expiry=1800)

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
        port=8000,
        reload=True,
        log_level="info"
    )