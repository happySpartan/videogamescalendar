from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, TimestampedBase
import uuid

class Game(Base, TimestampedBase):
    """Video games based on IGDB API schema - PostgreSQL optimized"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), index=True)
    summary = Column(Text)
    storyline = Column(Text)
    release_date = Column(DateTime(timezone=True), index=True)
    rating = Column(Float)
    rating_count = Column(Integer)
    aggregated_rating = Column(Float)
    aggregated_rating_count = Column(Integer)
    total_rating = Column(Float)
    total_rating_count = Column(Integer)
    cover_url = Column(String(512))
    status = Column(Integer, index=True)  # Index for filtering by status
    category = Column(Integer, index=True)  # Index for filtering by category
    first_release_date = Column(Integer)  # UNIX timestamp from IGDB
    hypes = Column(Integer)
    follows = Column(Integer)
    url = Column(String(512))
    
    # JSON fields for complex data - using PostgreSQL JSONB for better performance
    game_engines = Column(JSONB)
    alternative_names = Column(JSONB)
    videos = Column(JSONB)
    websites = Column(JSONB)
    keywords = Column(JSONB)
    themes = Column(JSONB)
    player_perspectives = Column(JSONB)
    game_modes = Column(JSONB)
    platforms = Column(JSONB)  # Store platform data as JSONB for better querying
    
    is_cached = Column(Boolean, default=False, index=True)
    video_id = Column(String(100))
    checksum = Column(String(255), unique=True)
    
    # Foreign keys with indexes
    developer_id = Column(Integer, ForeignKey('companies.id'), index=True)
    franchise_id = Column(Integer, ForeignKey('franchises.id'), index=True)
    genre_id = Column(Integer, ForeignKey('genres.id'), index=True)
    language_id = Column(Integer, ForeignKey('languages.id'), index=True)
    
    # Relationships
    developer = relationship("Company", back_populates="games")
    franchise = relationship("Franchise", back_populates="games")
    genre = relationship("Genre", back_populates="games")
    language = relationship("Language")
    
    # Table args for additional indexes
    __table_args__ = (
        Index('ix_games_release_date_status', 'release_date', 'status'),
        Index('ix_games_name_trgm', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('ix_games_platforms_gin', 'platforms', postgresql_using='gin'),
        Index('ix_games_keywords_gin', 'keywords', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Game(id={self.id}, name={self.name})>"