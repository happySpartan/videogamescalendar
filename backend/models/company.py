from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampedBase

class Company(Base, TimestampedBase):
    """Video game companies based on IGDB API schema"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100))
    description = Column(String(5000))
    country = Column(Integer)
    websites = Column(Text)  # Changed from website to websites as it's an array in JSON format
    start_date = Column(Integer)
    checksum = Column(String(255))
    
    # Relationships
    games = relationship("Game", back_populates="developer")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"
