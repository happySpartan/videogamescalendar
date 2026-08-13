from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .associations import (
    game_companies,
    game_franchises,
    game_genres,
    game_languages,
    game_platforms,
    game_regions,
)
from .base import Base, TimestampedBase


class Game(Base, TimestampedBase):
    """Video games based on the IGDB API schema - PostgreSQL optimized.

    A game has ONE canonical release timestamp (``first_release_date``) and
    many-to-many relationships to genres, platforms, companies, franchises,
    languages and regions.
    """
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), index=True)
    summary = Column(Text)
    storyline = Column(Text)

    # Single source of truth for the release date (timezone-aware).
    first_release_date = Column(DateTime(timezone=True), index=True)

    # Ratings
    rating = Column(Float)
    rating_count = Column(Integer)
    aggregated_rating = Column(Float)
    aggregated_rating_count = Column(Integer)
    total_rating = Column(Float)
    total_rating_count = Column(Integer)

    # Media / metadata
    cover_url = Column(String(512))
    screenshots = Column(JSONB)
    videos = Column(JSONB)
    websites = Column(JSONB)
    status = Column(Integer, index=True)
    category = Column(Integer, index=True)
    hypes = Column(Integer)
    follows = Column(Integer)
    url = Column(String(512))
    checksum = Column(String(255), unique=True)

    # Reserved name "metadata" cannot be a mapped attribute under the
    # declarative API, so the attribute is `metadata_` mapped to column `metadata`.
    metadata_ = Column("metadata", JSONB)

    # Many-to-many relationships
    genres = relationship("Genre", secondary=game_genres, back_populates="games")
    platforms = relationship("Platform", secondary=game_platforms, back_populates="games")
    companies = relationship("Company", secondary=game_companies, back_populates="games")
    franchises = relationship("Franchise", secondary=game_franchises, back_populates="games")
    languages = relationship("Language", secondary=game_languages, back_populates="games")
    regions = relationship("Region", secondary=game_regions, back_populates="games")

    __table_args__ = (
        Index("ix_games_release_date_status", "first_release_date", "status"),
        Index(
            "ix_games_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, name={self.name})>"
