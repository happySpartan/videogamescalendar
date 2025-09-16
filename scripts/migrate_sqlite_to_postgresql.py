"""
Data Migration Script: SQLite to PostgreSQL
Migrates existing SQLite data to the new PostgreSQL microservices architecture
"""
import os
import sys
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from shared.database import sync_session_factory
from shared.models import Game, Genre, Platform, Company, Franchise, Language, Region

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLiteToPostgreSQLMigrator:
    """Migrate data from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None
        self.stats = {
            'games': {'processed': 0, 'migrated': 0, 'errors': 0},
            'genres': {'processed': 0, 'migrated': 0, 'errors': 0},
            'platforms': {'processed': 0, 'migrated': 0, 'errors': 0},
            'companies': {'processed': 0, 'migrated': 0, 'errors': 0},
            'franchises': {'processed': 0, 'migrated': 0, 'errors': 0},
            'languages': {'processed': 0, 'migrated': 0, 'errors': 0},
            'regions': {'processed': 0, 'migrated': 0, 'errors': 0},
        }
    
    def connect_sqlite(self):
        """Connect to SQLite database"""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
        logger.info(f"Connected to SQLite database: {self.sqlite_path}")
    
    def disconnect_sqlite(self):
        """Disconnect from SQLite database"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None
            logger.info("Disconnected from SQLite database")
    
    def get_sqlite_tables(self) -> List[str]:
        """Get list of tables in SQLite database"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def migrate_genres(self):
        """Migrate genres from SQLite to PostgreSQL"""
        logger.info("Starting genre migration...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Check if genres table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='genres'")
        if not cursor.fetchone():
            logger.warning("No genres table found in SQLite database")
            return
        
        # Get genres from SQLite
        cursor.execute("SELECT * FROM genres")
        sqlite_genres = cursor.fetchall()
        
        with sync_session_factory() as pg_session:
            for sqlite_genre in sqlite_genres:
                self.stats['genres']['processed'] += 1
                
                try:
                    # Check if genre already exists (by name)
                    existing = pg_session.query(Genre).filter_by(name=sqlite_genre['name']).first()
                    
                    if existing:
                        logger.debug(f"Genre already exists: {sqlite_genre['name']}")
                        continue
                    
                    # Create new genre
                    genre = Genre(
                        igdb_id=sqlite_genre.get('igdb_id'),
                        name=sqlite_genre['name'],
                        slug=sqlite_genre.get('slug', ''),
                        description=sqlite_genre.get('description', ''),
                        metadata={'migrated_from_sqlite': True, 'sqlite_id': sqlite_genre['id']}
                    )
                    
                    pg_session.add(genre)
                    self.stats['genres']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate genre {sqlite_genre['name']}: {e}")
                    self.stats['genres']['errors'] += 1
                    pg_session.rollback()
                    continue
            
            # Commit all genres
            try:
                pg_session.commit()
                logger.info(f"Genre migration completed. Migrated: {self.stats['genres']['migrated']}")
            except Exception as e:
                logger.error(f"Failed to commit genres: {e}")
                pg_session.rollback()
    
    def migrate_platforms(self):
        """Migrate platforms from SQLite to PostgreSQL"""
        logger.info("Starting platform migration...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Check if platforms table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='platforms'")
        if not cursor.fetchone():
            logger.warning("No platforms table found in SQLite database")
            return
        
        cursor.execute("SELECT * FROM platforms")
        sqlite_platforms = cursor.fetchall()
        
        with sync_session_factory() as pg_session:
            for sqlite_platform in sqlite_platforms:
                self.stats['platforms']['processed'] += 1
                
                try:
                    # Check if platform already exists
                    existing = pg_session.query(Platform).filter_by(name=sqlite_platform['name']).first()
                    
                    if existing:
                        logger.debug(f"Platform already exists: {sqlite_platform['name']}")
                        continue
                    
                    platform = Platform(
                        igdb_id=sqlite_platform.get('igdb_id'),
                        name=sqlite_platform['name'],
                        abbreviation=sqlite_platform.get('abbreviation', ''),
                        alternative_names=sqlite_platform.get('alternative_names', []),
                        generation=sqlite_platform.get('generation'),
                        platform_family=sqlite_platform.get('platform_family', ''),
                        metadata={'migrated_from_sqlite': True, 'sqlite_id': sqlite_platform['id']}
                    )
                    
                    pg_session.add(platform)
                    self.stats['platforms']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate platform {sqlite_platform['name']}: {e}")
                    self.stats['platforms']['errors'] += 1
                    pg_session.rollback()
                    continue
            
            try:
                pg_session.commit()
                logger.info(f"Platform migration completed. Migrated: {self.stats['platforms']['migrated']}")
            except Exception as e:
                logger.error(f"Failed to commit platforms: {e}")
                pg_session.rollback()
    
    def migrate_companies(self):
        """Migrate companies from SQLite to PostgreSQL"""
        logger.info("Starting company migration...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
        if not cursor.fetchone():
            logger.warning("No companies table found in SQLite database")
            return
        
        cursor.execute("SELECT * FROM companies")
        sqlite_companies = cursor.fetchall()
        
        with sync_session_factory() as pg_session:
            for sqlite_company in sqlite_companies:
                self.stats['companies']['processed'] += 1
                
                try:
                    existing = pg_session.query(Company).filter_by(name=sqlite_company['name']).first()
                    
                    if existing:
                        logger.debug(f"Company already exists: {sqlite_company['name']}")
                        continue
                    
                    company = Company(
                        igdb_id=sqlite_company.get('igdb_id'),
                        name=sqlite_company['name'],
                        description=sqlite_company.get('description', ''),
                        country=sqlite_company.get('country', ''),
                        start_date=self._parse_date(sqlite_company.get('start_date')),
                        metadata={'migrated_from_sqlite': True, 'sqlite_id': sqlite_company['id']}
                    )
                    
                    pg_session.add(company)
                    self.stats['companies']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate company {sqlite_company['name']}: {e}")
                    self.stats['companies']['errors'] += 1
                    pg_session.rollback()
                    continue
            
            try:
                pg_session.commit()
                logger.info(f"Company migration completed. Migrated: {self.stats['companies']['migrated']}")
            except Exception as e:
                logger.error(f"Failed to commit companies: {e}")
                pg_session.rollback()
    
    def migrate_games(self):
        """Migrate games from SQLite to PostgreSQL"""
        logger.info("Starting game migration...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='games'")
        if not cursor.fetchone():
            logger.warning("No games table found in SQLite database")
            return
        
        cursor.execute("SELECT * FROM games")
        sqlite_games = cursor.fetchall()
        
        with sync_session_factory() as pg_session:
            for sqlite_game in sqlite_games:
                self.stats['games']['processed'] += 1
                
                try:
                    # Check if game already exists
                    existing = None
                    if sqlite_game.get('igdb_id'):
                        existing = pg_session.query(Game).filter_by(igdb_id=sqlite_game['igdb_id']).first()
                    
                    if not existing:
                        existing = pg_session.query(Game).filter_by(name=sqlite_game['name']).first()
                    
                    if existing:
                        logger.debug(f"Game already exists: {sqlite_game['name']}")
                        continue
                    
                    game = Game(
                        igdb_id=sqlite_game.get('igdb_id'),
                        name=sqlite_game['name'],
                        slug=sqlite_game.get('slug', ''),
                        summary=sqlite_game.get('summary', ''),
                        storyline=sqlite_game.get('storyline', ''),
                        first_release_date=self._parse_date(sqlite_game.get('first_release_date')),
                        rating=sqlite_game.get('rating'),
                        rating_count=sqlite_game.get('rating_count'),
                        total_rating=sqlite_game.get('total_rating'),
                        total_rating_count=sqlite_game.get('total_rating_count'),
                        cover_url=sqlite_game.get('cover_url', ''),
                        screenshots=self._parse_json_field(sqlite_game.get('screenshots')),
                        videos=self._parse_json_field(sqlite_game.get('videos')),
                        websites=self._parse_json_field(sqlite_game.get('websites')),
                        metadata={
                            'migrated_from_sqlite': True,
                            'sqlite_id': sqlite_game['id'],
                            'migration_timestamp': datetime.utcnow().isoformat()
                        }
                    )
                    
                    pg_session.add(game)
                    pg_session.flush()  # Get the ID
                    
                    # Migrate relationships
                    self._migrate_game_relationships(pg_session, game, sqlite_game['id'])
                    
                    self.stats['games']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate game {sqlite_game['name']}: {e}")
                    self.stats['games']['errors'] += 1
                    pg_session.rollback()
                    continue
            
            try:
                pg_session.commit()
                logger.info(f"Game migration completed. Migrated: {self.stats['games']['migrated']}")
            except Exception as e:
                logger.error(f"Failed to commit games: {e}")
                pg_session.rollback()
    
    def _migrate_game_relationships(self, pg_session, pg_game: Game, sqlite_game_id: int):
        """Migrate game relationships (genres, platforms, companies)"""
        cursor = self.sqlite_conn.cursor()
        
        # Migrate game-genre relationships
        try:
            cursor.execute("""
                SELECT g.name FROM genres g 
                INNER JOIN game_genres gg ON g.id = gg.genre_id 
                WHERE gg.game_id = ?
            """, (sqlite_game_id,))
            
            genre_names = [row[0] for row in cursor.fetchall()]
            for genre_name in genre_names:
                genre = pg_session.query(Genre).filter_by(name=genre_name).first()
                if genre:
                    pg_game.genres.append(genre)
        except Exception as e:
            logger.warning(f"Failed to migrate genres for game {pg_game.name}: {e}")
        
        # Migrate game-platform relationships
        try:
            cursor.execute("""
                SELECT p.name FROM platforms p 
                INNER JOIN game_platforms gp ON p.id = gp.platform_id 
                WHERE gp.game_id = ?
            """, (sqlite_game_id,))
            
            platform_names = [row[0] for row in cursor.fetchall()]
            for platform_name in platform_names:
                platform = pg_session.query(Platform).filter_by(name=platform_name).first()
                if platform:
                    pg_game.platforms.append(platform)
        except Exception as e:
            logger.warning(f"Failed to migrate platforms for game {pg_game.name}: {e}")
        
        # Migrate game-company relationships
        try:
            cursor.execute("""
                SELECT c.name FROM companies c 
                INNER JOIN game_companies gc ON c.id = gc.company_id 
                WHERE gc.game_id = ?
            """, (sqlite_game_id,))
            
            company_names = [row[0] for row in cursor.fetchall()]
            for company_name in company_names:
                company = pg_session.query(Company).filter_by(name=company_name).first()
                if company:
                    pg_game.companies.append(company)
        except Exception as e:
            logger.warning(f"Failed to migrate companies for game {pg_game.name}: {e}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S.%f"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, try parsing as timestamp
            try:
                timestamp = float(date_str)
                return datetime.fromtimestamp(timestamp)
            except (ValueError, TypeError):
                pass
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Date parsing error for '{date_str}': {e}")
            return None
    
    def _parse_json_field(self, json_str: Optional[str]) -> List[str]:
        """Parse JSON string field to list"""
        if not json_str:
            return []
        
        try:
            import json
            parsed = json.loads(json_str)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def run_migration(self):
        """Run complete migration process"""
        try:
            logger.info("Starting SQLite to PostgreSQL migration...")
            
            # Connect to SQLite
            self.connect_sqlite()
            
            # Show available tables
            tables = self.get_sqlite_tables()
            logger.info(f"Found SQLite tables: {tables}")
            
            # Run migrations in order (reference data first)
            self.migrate_genres()
            self.migrate_platforms()
            self.migrate_companies()
            
            # Migrate other reference data if tables exist
            if 'franchises' in tables:
                logger.info("Franchises table found but migration not implemented")
            if 'languages' in tables:
                logger.info("Languages table found but migration not implemented")
            if 'regions' in tables:
                logger.info("Regions table found but migration not implemented")
            
            # Finally migrate games
            self.migrate_games()
            
            # Print final statistics
            self.print_migration_stats()
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise
        finally:
            self.disconnect_sqlite()
    
    def print_migration_stats(self):
        """Print migration statistics"""
        logger.info("=== Migration Statistics ===")
        for table, stats in self.stats.items():
            if stats['processed'] > 0:
                success_rate = ((stats['migrated']) / stats['processed']) * 100
                logger.info(f"{table.capitalize()}: {stats['migrated']}/{stats['processed']} "
                          f"migrated ({success_rate:.1f}% success), {stats['errors']} errors")

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate SQLite data to PostgreSQL')
    parser.add_argument('sqlite_path', help='Path to SQLite database file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually doing it')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual migration will be performed")
        return
    
    # Verify PostgreSQL connection
    try:
        with sync_session_factory() as session:
            logger.info("PostgreSQL connection verified")
    except Exception as e:
        logger.error(f"Cannot connect to PostgreSQL: {e}")
        return
    
    # Run migration
    migrator = SQLiteToPostgreSQLMigrator(args.sqlite_path)
    migrator.run_migration()

if __name__ == "__main__":
    main()