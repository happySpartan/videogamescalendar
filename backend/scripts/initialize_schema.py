"""
Database Schema Initialization Script for Video Game Calendar

This script:
1. Purges all existing tables from the database
2. Creates new tables with proper schema based on IGDB API documentation
3. Adds downloaded_at timestamp column to support caching

Tables created:
- genres
- languages
- platforms
- regions
- companies
- franchises
"""
import os
import sys
import logging
from datetime import datetime
import sqlite3

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_connection():
    """Get a connection to the SQLite database"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def purge_tables():
    """Drop all existing tables from the database"""
    tables_to_drop = [
        'genres',
        'languages',
        'platforms',
        'regions',
        'companies',
        'franchises',
        'games'
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info("Purging existing tables...")
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        logger.info(f"Dropped table '{table}' if it existed")
    
    conn.commit()
    conn.close()
    logger.info("All tables purged successfully")

def create_schema():
    """Create new tables with proper schema based on IGDB API"""
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info("Creating new schema...")
    
    # Create genres table
    cursor.execute("""
    CREATE TABLE genres (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        slug TEXT,
        url TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created genres table")
    
    # Create languages table
    cursor.execute("""
    CREATE TABLE languages (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        native_name TEXT,
        locale TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created languages table")
    
    # Create platforms table
    cursor.execute("""
    CREATE TABLE platforms (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        abbreviation TEXT,
        alternative_name TEXT,
        category INTEGER,
        generation INTEGER,
        slug TEXT,
        summary TEXT,
        url TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created platforms table")
    
    # Create regions table
    cursor.execute("""
    CREATE TABLE regions (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        category TEXT,
        identifier TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created regions table")
    
    # Create companies table
    cursor.execute("""
    CREATE TABLE companies (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        slug TEXT,
        description TEXT,
        country INTEGER,
        websites TEXT,
        start_date INTEGER,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created companies table")
    
    # Create franchises table
    cursor.execute("""
    CREATE TABLE franchises (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        slug TEXT,
        url TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT
    )
    """)
    logger.info("Created franchises table")
    
    # Create games table with relationships to all entities
    cursor.execute("""
    CREATE TABLE games (
        id INTEGER PRIMARY KEY,
        igdb_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        slug TEXT,
        summary TEXT,
        storyline TEXT,
        release_date TIMESTAMP,
        rating REAL,
        rating_count INTEGER,
        aggregated_rating REAL,
        aggregated_rating_count INTEGER,
        total_rating REAL,
        total_rating_count INTEGER,
        cover_url TEXT,
        status INTEGER,
        category INTEGER,
        first_release_date INTEGER,
        hypes INTEGER,
        follows INTEGER,
        url TEXT,
        game_engines TEXT,
        alternative_names TEXT,
        videos TEXT,
        websites TEXT,
        keywords TEXT,
        themes TEXT,
        player_perspectives TEXT,
        game_modes TEXT,
        is_cached BOOLEAN DEFAULT 0,
        video_id TEXT,
        franchise_id INTEGER,
        genre_id INTEGER,
        developer_id INTEGER,
        language_id INTEGER,
        created_at INTEGER,
        updated_at INTEGER,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum TEXT,
        FOREIGN KEY (franchise_id) REFERENCES franchises (id),
        FOREIGN KEY (genre_id) REFERENCES genres (id),
        FOREIGN KEY (developer_id) REFERENCES companies (id),
        FOREIGN KEY (language_id) REFERENCES languages (id)
    )
    """)
    logger.info("Created games table")
    
    conn.commit()
    conn.close()
    logger.info("Schema creation completed successfully")

def main():
    """Main function to initialize the database schema"""
    try:
        logger.info("Starting schema initialization...")
        purge_tables()
        create_schema()
        logger.info("Schema initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during schema initialization: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
