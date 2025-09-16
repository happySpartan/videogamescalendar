import logging
from functools import wraps
from flask import request
import json
from sqlalchemy import extract
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def log_api_call(func):
    """Decorator to log API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"API call to {request.path}")
        return func(*args, **kwargs)
    return wrapper

class FallbackCacheService:
    """Improved fallback service that uses the games table directly instead of cached_games"""
    @staticmethod
    def get_cached_data(db, cache_key):
        """Get cached data directly from games table"""
        from models import Game
        try:
            logger.debug(f"Using built-in cache to get: {cache_key}")
            
            # Parse cache_key to determine what data to return
            if cache_key.startswith('games_year_'):
                year = int(cache_key.split('_')[-1])
                games = db.query(Game).filter(
                    extract('year', Game.release_date) == year,
                    Game.is_cached == True
                ).all()
                
                # Convert games to simple dict for caching
                return [
                    {
                        "id": game.id,
                        "name": game.name,
                        "release_date": game.release_date.isoformat() if game.release_date else None,
                        "cover_url": game.cover_url,
                        "summary": game.summary,
                        "video_id": game.video_id,
                        "developer": {"id": game.developer.id, "name": game.developer.name} if game.developer else None,
                        "franchise": {"id": game.franchise.id, "name": game.franchise.name} if game.franchise else None,
                        "genre": {"id": game.genre.id, "name": game.genre.name} if game.genre else None
                    }
                    for game in games
                ]
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached data: {str(e)}")
            return None
            
    @staticmethod
    def cache_data(db, cache_key, data, expires_in_hours=24):
        """Store cache data directly in games table"""
        from models import Game
        try:
            logger.debug(f"Using built-in cache to store: {cache_key}")
            
            # For now, we just mark existing games as cached
            # Future implementation could store serialized data in a different way
            if cache_key.startswith('games_year_'):
                # Get IDs from data if it's a list of games
                if isinstance(data, list) and len(data) > 0 and 'id' in data[0]:
                    game_ids = [game['id'] for game in data]
                    
                    # Mark these games as cached
                    games_to_cache = db.query(Game).filter(Game.id.in_(game_ids)).all()
                    for game in games_to_cache:
                        game.is_cached = True
                        game.updated_at = int(datetime.utcnow().timestamp())
                    
                    db.commit()
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            db.rollback()
            return False
