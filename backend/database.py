"""
Database module - re-exports database models and utilities for backward compatibility
"""
# Re-export from models
from models import (
    Base, TimestampedBase, Game, Genre, Platform, Language, 
    Region, Company, Franchise
)

# Re-export from utils.db_utils
from utils.db_utils import (
    get_db_path, get_database_url, test_db_connection, 
    engine, SessionLocal, init_db, get_db
)

# Export everything for backward compatibility
__all__ = [
    'Base', 'TimestampedBase', 'Game', 'Genre', 'Platform', 'Language',
    'Region', 'Company', 'Franchise',
    'get_db_path', 'get_database_url', 'test_db_connection',
    'engine', 'SessionLocal', 'init_db', 'get_db'
]