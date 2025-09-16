from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base, TimestampedBase

class Franchise(Base, TimestampedBase):
    """Game franchises based on IGDB API schema"""
    __tablename__ = "franchises"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100))
    url = Column(String(255))
    checksum = Column(String(255))
    
    # Relationships
    games = relationship("Game", back_populates="franchise")
    
    def __repr__(self):
        return f"<Franchise(id={self.id}, name={self.name})>"
