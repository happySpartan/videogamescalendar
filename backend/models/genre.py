from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampedBase

class Genre(Base, TimestampedBase):
    """Game genres based on IGDB API schema"""
    __tablename__ = "genres"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100))
    url = Column(String(255))
    checksum = Column(String(255))

    # Relationships
    games = relationship("Game", back_populates="genre")

    def __repr__(self):
        return f"<Genre(id={self.id}, name={self.name})>"
