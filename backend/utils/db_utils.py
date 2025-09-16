import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_db_path():
    """Get the physical path to the SQLite database file"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gamecalendar.db')

def get_database_url():
    """Get SQLite database URL using the database path"""
    return f"sqlite:///{get_db_path()}"

def test_db_connection(engine):
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT sqlite_version()"))
            version = result.scalar()
            logger.info(f"Successfully connected to SQLite. Version: {version}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

# Create engine for SQLite
try:
    engine = create_engine(
        get_database_url(),
        echo=True,
        connect_args={"check_same_thread": False},  # SQLite specific
        # Add explicit pool settings to handle connection issues
        pool_size=20,
        max_overflow=20,
        pool_timeout=60,
        pool_pre_ping=True,
        pool_recycle=1800
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables"""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_db():
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
