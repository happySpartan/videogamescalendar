from sqlalchemy import Column, Integer, String
from .base import Base, TimestampedBase

class Platform(Base, TimestampedBase):
    """Gaming platforms based on IGDB API schema"""
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(50))
    category = Column(Integer)
    generation = Column(Integer)
    slug = Column(String(100))
    summary = Column(String(1000))
    url = Column(String(255))
    checksum = Column(String(255))
    
    def __repr__(self):
        return f"<Platform(id={self.id}, name={self.name})>"
