from sqlalchemy import Column, Integer, String
from .base import Base, TimestampedBase

class Region(Base, TimestampedBase):
    """Game regions based on IGDB API schema"""
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    identifier = Column(String(50))
    checksum = Column(String(255))
    
    def __repr__(self):
        return f"<Region(id={self.id}, name={self.name})>"
