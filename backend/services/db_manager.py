import logging
import time
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path to enable imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal

logger = logging.getLogger(__name__)

@contextmanager
def get_db_session():
    """Context manager to ensure DB sessions are properly closed"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error with database session: {str(e)}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")

def execute_with_retry(func, max_retries=3, retry_delay=1):
    """Execute a database function with retry logic"""
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            with get_db_session() as session:
                result = func(session)
                return result
        except Exception as e:
            last_error = e
            logger.warning(f"Database operation failed (attempt {retries+1}/{max_retries}): {str(e)}")
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)
    
    logger.error(f"Database operation failed after {max_retries} attempts: {str(last_error)}")
    raise last_error
