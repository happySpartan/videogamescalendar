"""
Celery worker for background data synchronization tasks
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from shared.database import get_db_session, sync_session_factory
from shared.models import Game, Genre, Platform, Company, Franchise, Language, Region

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery(
    'data_sync',
    broker=redis_url,
    backend=redis_url,
    include=['worker']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'data_sync.sync_games': {'queue': 'data_sync'},
        'data_sync.sync_single_game': {'queue': 'priority'},
        'data_sync.cleanup_old_data': {'queue': 'maintenance'},
    },
    beat_schedule={
        'daily-full-sync': {
            'task': 'data_sync.sync_games',
            'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
            'kwargs': {'full_sync': True}
        },
        'hourly-delta-sync': {
            'task': 'data_sync.sync_games',
            'schedule': crontab(minute=0),  # Every hour
            'kwargs': {'full_sync': False}
        },
        'weekly-cleanup': {
            'task': 'data_sync.cleanup_old_data',
            'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
        },
    }
)

# Mock IGDB Service (replace with actual implementation)
class IGDBService:
    """Mock IGDB service for demonstration"""
    
    def __init__(self):
        self.client_id = os.getenv("IGDB_CLIENT_ID")
        self.client_secret = os.getenv("IGDB_CLIENT_SECRET")
        self.access_token = None
        self.token_expires_at = None
    
    async def authenticate(self):
        """Authenticate with IGDB API"""
        # Mock implementation - replace with actual IGDB authentication
        logger.info("Mock IGDB authentication")
        self.access_token = "mock_token"
        self.token_expires_at = datetime.utcnow() + timedelta(days=30)
    
    async def get_games(self, limit: int = 100, offset: int = 0, updated_after: Optional[datetime] = None) -> List[Dict]:
        """Get games from IGDB API"""
        # Mock implementation - replace with actual IGDB API calls
        logger.info(f"Mock fetching games: limit={limit}, offset={offset}, updated_after={updated_after}")
        
        # Return mock game data
        mock_games = []
        for i in range(min(limit, 10)):  # Return up to 10 mock games
            mock_games.append({
                "id": 1000 + i + offset,
                "name": f"Mock Game {1000 + i + offset}",
                "slug": f"mock-game-{1000 + i + offset}",
                "summary": f"This is a mock game {1000 + i + offset} for testing",
                "storyline": f"Extended storyline for game {1000 + i + offset}",
                "first_release_date": int(datetime(2023, 1, 1).timestamp()),
                "rating": 75.5 + (i * 2),
                "rating_count": 100 + (i * 10),
                "total_rating": 80.0 + (i * 1.5),
                "total_rating_count": 200 + (i * 15),
                "cover": {"url": f"//example.com/cover_{1000 + i + offset}.jpg"},
                "screenshots": [{"url": f"//example.com/screenshot_{1000 + i + offset}_{j}.jpg"} for j in range(3)],
                "genres": [{"id": 10 + (i % 5), "name": f"Genre {10 + (i % 5)}"}],
                "platforms": [{"id": 20 + (i % 3), "name": f"Platform {20 + (i % 3)}"}],
                "involved_companies": [{"company": {"id": 30 + i, "name": f"Company {30 + i}"}}],
                "updated_at": int(datetime.utcnow().timestamp())
            })
        
        return mock_games
    
    async def get_genres(self) -> List[Dict]:
        """Get genres from IGDB API"""
        logger.info("Mock fetching genres")
        return [
            {"id": 10, "name": "Action", "slug": "action"},
            {"id": 11, "name": "Adventure", "slug": "adventure"},
            {"id": 12, "name": "RPG", "slug": "rpg"},
            {"id": 13, "name": "Strategy", "slug": "strategy"},
            {"id": 14, "name": "Sports", "slug": "sports"}
        ]
    
    async def get_platforms(self) -> List[Dict]:
        """Get platforms from IGDB API"""
        logger.info("Mock fetching platforms")
        return [
            {"id": 20, "name": "PC", "abbreviation": "PC"},
            {"id": 21, "name": "PlayStation 5", "abbreviation": "PS5"},
            {"id": 22, "name": "Xbox Series X/S", "abbreviation": "XBSX"}
        ]
    
    async def get_companies(self) -> List[Dict]:
        """Get companies from IGDB API"""
        logger.info("Mock fetching companies")
        return [
            {"id": 30, "name": "Nintendo", "description": "Japanese video game company"},
            {"id": 31, "name": "Sony Interactive Entertainment", "description": "PlayStation maker"},
            {"id": 32, "name": "Microsoft", "description": "Xbox maker"}
        ]

# Initialize IGDB service
igdb_service = IGDBService()

@celery_app.task(bind=True)
def sync_games(self, full_sync: bool = False):
    """Sync games from IGDB API"""
    try:
        logger.info(f"Starting game sync (full_sync={full_sync})")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_sync_games_async(full_sync))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Game sync failed: {e}", exc_info=True)
        raise self.retry(countdown=300, max_retries=3)

async def _sync_games_async(full_sync: bool = False):
    """Async implementation of game sync"""
    
    # Authenticate with IGDB
    await igdb_service.authenticate()
    
    # Determine sync parameters
    updated_after = None
    if not full_sync:
        # Delta sync: only get games updated in last hour
        updated_after = datetime.utcnow() - timedelta(hours=1)
    
    synced_count = 0
    offset = 0
    limit = 100
    
    with sync_session_factory() as db:
        # First sync reference data
        await _sync_reference_data(db)
        
        while True:
            # Fetch games from IGDB
            games_data = await igdb_service.get_games(
                limit=limit,
                offset=offset,
                updated_after=updated_after
            )
            
            if not games_data:
                break
            
            # Process each game
            for game_data in games_data:
                try:
                    await _process_game_data(db, game_data)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to process game {game_data.get('id', 'unknown')}: {e}")
            
            # Commit batch
            db.commit()
            
            offset += limit
            
            # Stop if we got fewer results than requested (end of data)
            if len(games_data) < limit:
                break
    
    logger.info(f"Game sync completed. Processed {synced_count} games")
    return {"synced_count": synced_count, "full_sync": full_sync}

async def _sync_reference_data(db):
    """Sync reference data (genres, platforms, companies)"""
    logger.info("Syncing reference data")
    
    # Sync genres
    genres_data = await igdb_service.get_genres()
    for genre_data in genres_data:
        existing = db.query(Genre).filter_by(igdb_id=genre_data["id"]).first()
        if existing:
            existing.name = genre_data["name"]
            existing.slug = genre_data["slug"]
        else:
            genre = Genre(
                igdb_id=genre_data["id"],
                name=genre_data["name"],
                slug=genre_data["slug"]
            )
            db.add(genre)
    
    # Sync platforms
    platforms_data = await igdb_service.get_platforms()
    for platform_data in platforms_data:
        existing = db.query(Platform).filter_by(igdb_id=platform_data["id"]).first()
        if existing:
            existing.name = platform_data["name"]
            existing.abbreviation = platform_data.get("abbreviation")
        else:
            platform = Platform(
                igdb_id=platform_data["id"],
                name=platform_data["name"],
                abbreviation=platform_data.get("abbreviation")
            )
            db.add(platform)
    
    # Sync companies
    companies_data = await igdb_service.get_companies()
    for company_data in companies_data:
        existing = db.query(Company).filter_by(igdb_id=company_data["id"]).first()
        if existing:
            existing.name = company_data["name"]
            existing.description = company_data.get("description")
        else:
            company = Company(
                igdb_id=company_data["id"],
                name=company_data["name"],
                description=company_data.get("description")
            )
            db.add(company)
    
    db.commit()

async def _process_game_data(db, game_data: Dict):
    """Process individual game data"""
    
    # Check if game exists
    existing_game = db.query(Game).filter_by(igdb_id=game_data["id"]).first()
    
    if existing_game:
        # Update existing game
        game = existing_game
    else:
        # Create new game
        game = Game(igdb_id=game_data["id"])
        db.add(game)
    
    # Update game fields
    game.name = game_data.get("name", "")
    game.slug = game_data.get("slug", "")
    game.summary = game_data.get("summary")
    game.storyline = game_data.get("storyline")
    
    # Handle release date
    if "first_release_date" in game_data:
        game.first_release_date = datetime.fromtimestamp(game_data["first_release_date"])
    
    # Handle ratings
    game.rating = game_data.get("rating")
    game.rating_count = game_data.get("rating_count")
    game.total_rating = game_data.get("total_rating")
    game.total_rating_count = game_data.get("total_rating_count")
    
    # Handle cover image
    if "cover" in game_data and game_data["cover"]:
        cover_url = game_data["cover"].get("url", "")
        if cover_url:
            game.cover_url = f"https:{cover_url}" if not cover_url.startswith("http") else cover_url
    
    # Handle screenshots
    if "screenshots" in game_data:
        screenshots = []
        for screenshot in game_data["screenshots"]:
            url = screenshot.get("url", "")
            if url:
                screenshots.append(f"https:{url}" if not url.startswith("http") else url)
        game.screenshots = screenshots
    
    # Store additional metadata as JSONB
    game.metadata = {
        "igdb_data": {
            key: value for key, value in game_data.items()
            if key not in ["id", "name", "slug", "summary", "storyline", "first_release_date",
                          "rating", "rating_count", "total_rating", "total_rating_count",
                          "cover", "screenshots", "genres", "platforms", "involved_companies"]
        },
        "sync_timestamp": datetime.utcnow().isoformat()
    }
    
    # Handle relationships
    await _process_game_relationships(db, game, game_data)
    
    return game

async def _process_game_relationships(db, game: Game, game_data: Dict):
    """Process game relationships (genres, platforms, companies)"""
    
    # Clear existing relationships
    game.genres.clear()
    game.platforms.clear()
    game.companies.clear()
    
    # Add genres
    if "genres" in game_data:
        for genre_data in game_data["genres"]:
            genre = db.query(Genre).filter_by(igdb_id=genre_data["id"]).first()
            if genre:
                game.genres.append(genre)
    
    # Add platforms
    if "platforms" in game_data:
        for platform_data in game_data["platforms"]:
            platform = db.query(Platform).filter_by(igdb_id=platform_data["id"]).first()
            if platform:
                game.platforms.append(platform)
    
    # Add companies
    if "involved_companies" in game_data:
        for involved_company in game_data["involved_companies"]:
            company_data = involved_company.get("company", {})
            if company_data:
                company = db.query(Company).filter_by(igdb_id=company_data["id"]).first()
                if company:
                    game.companies.append(company)

@celery_app.task(bind=True)
def sync_single_game(self, igdb_game_id: int):
    """Sync a single game by IGDB ID"""
    try:
        logger.info(f"Syncing single game: {igdb_game_id}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_sync_single_game_async(igdb_game_id))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Single game sync failed: {e}", exc_info=True)
        raise self.retry(countdown=60, max_retries=3)

async def _sync_single_game_async(igdb_game_id: int):
    """Async implementation of single game sync"""
    await igdb_service.authenticate()
    
    # Mock single game fetch - replace with actual IGDB API call
    games_data = await igdb_service.get_games(limit=1, offset=igdb_game_id - 1000)
    
    if not games_data:
        raise ValueError(f"Game not found: {igdb_game_id}")
    
    game_data = games_data[0]
    
    with sync_session_factory() as db:
        await _sync_reference_data(db)
        game = await _process_game_data(db, game_data)
        db.commit()
        
        return {
            "game_id": game.id,
            "igdb_id": game.igdb_id,
            "name": game.name
        }

@celery_app.task
def cleanup_old_data():
    """Clean up old or orphaned data"""
    try:
        logger.info("Starting data cleanup")
        
        with sync_session_factory() as db:
            # Remove games that haven't been updated in 30 days (mock logic)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_games = db.query(Game).filter(Game.updated_at < cutoff_date).count()
            
            logger.info(f"Found {old_games} old games (cleanup disabled in mock)")
            
            # In real implementation, you might:
            # - Remove orphaned relationships
            # - Clean up unused media files
            # - Archive old data
            # - Optimize database indexes
            
            return {"old_games_found": old_games, "cleanup_performed": False}
            
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}", exc_info=True)
        raise

@celery_app.task
def health_check():
    """Health check task"""
    try:
        with sync_session_factory() as db:
            # Simple database query
            game_count = db.query(Game).count()
            
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "game_count": game_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()