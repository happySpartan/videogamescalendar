from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

Base = declarative_base()

class TimestampedBase(object):
    """Base class that adds timestamp columns to models"""
    created_at = Column(Integer)
    updated_at = Column(Integer)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
