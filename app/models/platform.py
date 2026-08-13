from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.orm import relationship

from .associations import game_platforms
from .base import Base, TimestampedBase


class Platform(Base, TimestampedBase):
    """Gaming platforms based on IGDB API schema - PostgreSQL optimized"""
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    abbreviation = Column(String(50), index=True)
    category = Column(Integer, index=True)
    generation = Column(Integer, index=True)
    slug = Column(String(100), unique=True, index=True)
    summary = Column(String(2000))
    url = Column(String(512))
    checksum = Column(String(255), unique=True)

    # Relationships
    games = relationship("Game", secondary=game_platforms, back_populates="platforms")

    # Table args for text search
    __table_args__ = (
        Index("ix_platforms_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )

    def __repr__(self):
        return f"<Platform(id={self.id}, name={self.name})>"
