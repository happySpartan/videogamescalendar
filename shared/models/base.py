from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Index
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class TimestampedBase(object):
    """Base class that adds timestamp columns to models"""
    created_at = Column(Integer, nullable=True, index=True)
    updated_at = Column(Integer, nullable=True, index=True)
    downloaded_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Add composite index on timestamp columns for better query performance
        if hasattr(cls, '__tablename__'):
            cls.__table_args__ = getattr(cls, '__table_args__', ()) + (
                Index(f'ix_{cls.__tablename__}_timestamps', 'created_at', 'updated_at', 'downloaded_at'),
            )