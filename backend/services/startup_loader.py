import logging
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database-related functionality
from database import init_db, get_db, test_db_connection, engine
from models import Platform, Genre, Language, Region, Game, Company, Franchise
from config import Config
from services.igdb_service import IGDBService

logger = logging.getLogger(__name__)

class StartupLoader:
    @staticmethod
    def should_refresh_data(db: Session, model_class, cache_hours=168):  # Changed from 24 to 168 (7 days)
        """
        Determine if data needs to be refreshed based on:
        1. If the table is empty 
        2. If the most recent downloaded_at timestamp is older than cache_hours
        """
        # Check if table is empty
        count = db.query(func.count(model_class.id)).scalar()
        if count == 0:
            logger.info(f"{model_class.__name__} table is empty, will populate")
            return True
            
        # Check if data is stale based on downloaded_at timestamp
        try:
            most_recent = db.query(func.max(model_class.downloaded_at)).scalar()
            if most_recent is None:
                logger.info(f"No downloaded_at timestamp found in {model_class.__name__}, will refresh")
                return True
                
            # Calculate refresh threshold
            refresh_threshold = datetime.utcnow() - timedelta(hours=cache_hours)
            
            if most_recent < refresh_threshold:
                logger.info(f"{model_class.__name__} data is stale (last download: {most_recent}), will refresh")
                return True
            
            # Add logging to show timestamp when deciding not to update
            logger.info(f"{model_class.__name__} data is recent enough (last download: {most_recent}), skipping refresh")
            # Add logging to show actual number of records in the table 
            logger.info(f"{model_class.__name__} table has {count} records")
            return False
                
        except Exception as e:
            logger.warning(f"Error checking refresh status for {model_class.__name__}: {str(e)}")
            # When in doubt, refresh
            return True

    @staticmethod
    def load_initial_data(db: Session, cache_hours=168):  # Changed from 24 to 168 (7 days)
        """Load essential initial data if missing or stale."""
        logger.info(f"Checking data freshness with cache threshold of {cache_hours} hours (7 days)")
        
        # Check and refresh platforms
        if StartupLoader.should_refresh_data(db, Platform, cache_hours):
            logger.info("Loading platforms data from IGDB API")
            IGDBService.fetch_platforms(db)
        
        # Check and refresh genres
        if StartupLoader.should_refresh_data(db, Genre, cache_hours):
            logger.info("Loading genres data from IGDB API")
            IGDBService.fetch_genres(db)
        
        # Check and refresh languages
        if StartupLoader.should_refresh_data(db, Language, cache_hours):
            logger.info("Loading languages data from IGDB API")
            IGDBService.fetch_languages(db)
        
        # Check and refresh regions
        if StartupLoader.should_refresh_data(db, Region, cache_hours):
            logger.info("Loading regions data from IGDB API")
            IGDBService.fetch_regions(db)
        
        # TEMPORARILY DISABLED: Companies loading
        # logger.info("SKIPPING companies data loading - temporarily disabled due to data volume")
        
        # Check and refresh franchises
        if StartupLoader.should_refresh_data(db, Franchise, cache_hours):
            logger.info("Loading franchises data from IGDB API")
            IGDBService.fetch_franchises(db)
        
        # Games follow a different logic - check latest years
        current_year = datetime.now().year
        target_years = [current_year, current_year + 1]  # Current and next year
        
        for year in target_years:
            # Check if games for this year exist and are fresh
            game_count = db.query(func.count(Game.id)).filter(
                extract('year', Game.release_date) == year
            ).scalar()
            
            if game_count == 0:
                logger.info(f"No games found for {year}, will fetch them")
                IGDBService.fetch_games_for_year(db, year)
            else:
                # Check if games for this year need refresh (use 12 hours for more frequent updates)
                most_recent = db.query(func.max(Game.downloaded_at)).filter(
                    extract('year', Game.release_date) == year
                ).scalar()
                
                if most_recent:
                    refresh_threshold = datetime.utcnow() - timedelta(hours=Config.GAMES_REFRESH_HOURS)  # More frequent refresh for games
                    
                    if most_recent < refresh_threshold:
                        logger.info(f"Games for {year} are stale (last download: {most_recent}), will refresh")
                        IGDBService.fetch_games_for_year(db, year)
                    else:
                        logger.info(f"Games for {year} are recent enough (last download: {most_recent}), skipping refresh")
                else:
                    # If we can't determine last update time, refresh to be safe
                    logger.info(f"Cannot determine freshness for {year} games, will refresh")
                    IGDBService.fetch_games_for_year(db, year)

    @staticmethod
    def initialize_backend():
        """Initialize database and load essential data."""
        logger.info("Initializing backend...")
        
        # Initialize database and schema
        init_db()

        if not test_db_connection(engine):
            logger.error("Database connection failed. Exiting.")
            return False

        # Get cache hours from Config
        cache_hours = Config.CACHE_REFRESH_HOURS
        logger.info(f"Using cache refresh interval of {cache_hours} hours")

        # Load essential data if needed
        db = next(get_db())
        try:
            # Load initial data from API if needed
            logger.info("Checking if initial data load is needed...")
            StartupLoader.load_initial_data(db, cache_hours)
            
            logger.info("Backend initialization complete.")
            return True
        except Exception as e:
            logger.exception(f"Error during backend initialization: {str(e)}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def run_flask_app(app):
        """Run the Flask application with proper settings"""
        try:
            # Initialize backend first
            success = StartupLoader.initialize_backend()
            if not success:
                logger.error("Backend initialization failed.")
                sys.exit(1)

            # Start Flask app
            port = int(os.environ.get('PORT', 5050))
            debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
            
            logger.info(f"Starting Flask app on port {port} with debug={debug_mode}")
            app.run(
                host='0.0.0.0', 
                port=port, 
                debug=debug_mode, 
                use_reloader=False  # Disable reloader to prevent duplicate initialization
            )
        except Exception as e:
            logger.exception(f"Error starting Flask app: {str(e)}")
            sys.exit(1)
