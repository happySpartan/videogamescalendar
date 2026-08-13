from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.orm import relationship

from .associations import game_regions
from .base import Base, TimestampedBase


class Region(Base, TimestampedBase):
    """Game regions based on IGDB API schema - PostgreSQL optimized"""
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)
    identifier = Column(String(50), unique=True, index=True)
    checksum = Column(String(255), unique=True)

    # Relationships
    games = relationship("Game", secondary=game_regions, back_populates="regions")

    # Table args for text search
    __table_args__ = (
        Index("ix_regions_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )

    def __repr__(self):
        return f"<Region(id={self.id}, name={self.name})>"
