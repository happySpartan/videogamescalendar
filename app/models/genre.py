from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.orm import relationship

from .associations import game_genres
from .base import Base, TimestampedBase


class Genre(Base, TimestampedBase):
    """Game genres based on IGDB API schema - PostgreSQL optimized"""

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), unique=True, index=True)
    url = Column(String(512))
    checksum = Column(String(255), unique=True)

    # Relationships
    games = relationship("Game", secondary=game_genres, back_populates="genres")

    # Table args for text search
    __table_args__ = (
        Index(
            "ix_genres_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name={self.name})>"
