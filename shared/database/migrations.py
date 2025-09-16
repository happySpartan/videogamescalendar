"""
Database migration utilities using Alembic
"""
import os
import logging
from alembic.config import Config
from alembic import command
from pathlib import Path

logger = logging.getLogger(__name__)

def get_alembic_config() -> Config:
    """Get Alembic configuration"""
    # Find the alembic.ini file in the project root
    project_root = Path(__file__).parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")
    
    alembic_cfg = Config(str(alembic_ini_path))
    
    # Set the database URL
    database_url = os.getenv("DATABASE_URL", "postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    return alembic_cfg

def run_migrations():
    """Run database migrations"""
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise

def create_migration(message: str):
    """Create a new migration"""
    try:
        alembic_cfg = get_alembic_config()
        command.revision(alembic_cfg, message=message, autogenerate=True)
        logger.info(f"Migration created: {message}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise