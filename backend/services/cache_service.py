import sys
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logger
logger = logging.getLogger(__name__)

# Import database models with error handling
try:
    from database import CachedGames
except ImportError as e:
    logger.error(f"Failed to import database models: {str(e)}")
    # Define a minimal CachedGames class for type checking
    class CachedGames:
        pass

class CacheService:
    @staticmethod
    def get_cached_data(db: Session, cache_key: str):
        """Get cached data for a specific key if not expired"""
        try:
            cached = db.query(CachedGames).filter(
                CachedGames.cache_key == cache_key,
                CachedGames.expires_at > datetime.utcnow()
            ).first()
            
            return cached.data if cached else None
        except Exception as e:
            logger.error(f"Error retrieving cached data: {str(e)}")
            # Make sure to rollback in case of errors to free up the connection
            try:
                db.rollback()
            except:
                pass
            return None

    @staticmethod
    def cache_data(db: Session, cache_key: str, data, expires_in_hours=24):
        """Cache data with expiration time"""
        try:
            cached = db.query(CachedGames).filter(
                CachedGames.cache_key == cache_key
            ).first()
            
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            if cached:
                cached.data = data
                cached.cached_at = datetime.utcnow()
                cached.expires_at = expires_at
            else:
                cached = CachedGames(
                    cache_key=cache_key,
                    data=data,
                    expires_at=expires_at
                )
                db.add(cached)
                
            db.commit()
            return cached
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            # Always rollback in case of errors to free up the connection
            try:
                db.rollback()
            except:
                pass
            return None