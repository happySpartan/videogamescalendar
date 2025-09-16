"""
Database utilities for the Video Game Calendar microservices.
PostgreSQL-optimized database connection and session management.
"""
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from ..models.base import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar")

# Create engine with connection pooling optimized for microservices
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_url() -> str:
    """Get the database URL"""
    return DATABASE_URL

def test_db_connection() -> bool:
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def init_db() -> None:
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db() -> Generator[Session, None, None]:
    """Get database session - dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session - for use in Celery tasks"""
    return SessionLocal()

class DatabaseManager:
    """Database manager for handling connections in different contexts"""
    
    @staticmethod
    def get_sync_session() -> Session:
        """Get synchronous database session"""
        return SessionLocal()
    
    @staticmethod
    def close_session(session: Session) -> None:
        """Close database session"""
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing database session: {e}")
    
    @staticmethod
    def health_check() -> dict:
        """Database health check"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "version": version,
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }