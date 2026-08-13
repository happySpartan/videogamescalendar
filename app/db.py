"""Database utilities for the video game calendar.

PostgreSQL-optimized connection and session management. Kept synchronous entry
points for the Celery worker and asynchronous ones for the FastAPI layer.
"""
import logging
import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .models.base import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gameuser:***@localhost:5432/gamecalendar")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))

# Sync engine (Celery worker / migrations / health checks)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
)

# Async engine (FastAPI)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
sync_session_factory = SessionLocal  # Alias kept for compatibility
async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)


def get_database_url() -> str:
    """Get the database URL."""
    return DATABASE_URL


def test_db_connection() -> bool:
    """Test the sync database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def test_connection() -> bool:
    """Alias for ``test_db_connection`` for compatibility."""
    return test_db_connection()


def init_db() -> None:
    """Create all tables. Prefer Alembic migrations over this in production."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """Get a synchronous database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a synchronous session for Celery tasks."""
    return SessionLocal()


class DatabaseManager:
    """Database manager for handling connections in different contexts."""

    @staticmethod
    def get_sync_session() -> Session:
        return SessionLocal()

    @staticmethod
    def close_session(session: Session) -> None:
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing database session: {e}")

    @staticmethod
    def health_check() -> dict:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "version": version,
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
