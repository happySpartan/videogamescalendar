from sqlalchemy import Column, Integer, String
from .base import Base, TimestampedBase

class Language(Base, TimestampedBase):
    """Supported languages based on IGDB API schema"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    locale = Column(String(20))
    native_name = Column(String(100))
    checksum = Column(String(255))

    def __repr__(self):
        return f"<Language(id={self.id}, name={self.name})>"
