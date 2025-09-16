from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampedBase

class Game(Base, TimestampedBase):
    """Video games based on IGDB API schema"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    igdb_id = Column(Integer, unique=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200))
    summary = Column(Text)
    storyline = Column(Text)
    release_date = Column(DateTime)
    rating = Column(Float)
    rating_count = Column(Integer)
    aggregated_rating = Column(Float)
    aggregated_rating_count = Column(Integer)
    total_rating = Column(Float)
    total_rating_count = Column(Integer)
    cover_url = Column(String(255))
    status = Column(Integer)
    category = Column(Integer)  # main_game, dlc, expansion, etc.
    first_release_date = Column(Integer)  # UNIX timestamp from IGDB
    hypes = Column(Integer)  # Hype count
    follows = Column(Integer)  # Follow count
    url = Column(String(255))  # URL on IGDB website
    game_engines = Column(String(255))  # Comma-separated list of game engines
    alternative_names = Column(Text)  # JSON list of alternative names
    videos = Column(Text)  # JSON list of video IDs
    websites = Column(Text)  # JSON list of websites
    keywords = Column(Text)  # JSON list of keywords
    themes = Column(Text)  # JSON list of themes
    player_perspectives = Column(Text)  # JSON list of player perspectives
    game_modes = Column(Text)  # JSON list of game modes
    is_cached = Column(Boolean, default=False)
    video_id = Column(String(100))  # Primary video ID for quick access
    checksum = Column(String(255))  # IGDB checksum
    
    # Foreign keys
    developer_id = Column(Integer, ForeignKey('companies.id'))
    franchise_id = Column(Integer, ForeignKey('franchises.id'))
    genre_id = Column(Integer, ForeignKey('genres.id'))
    language_id = Column(Integer, ForeignKey('languages.id'))
    
    # Relationships
    developer = relationship("Company", back_populates="games")
    franchise = relationship("Franchise", back_populates="games")
    genre = relationship("Genre", back_populates="games")
    language = relationship("Language")

    def __repr__(self):
        return f"<Game(id={self.id}, name={self.name})>"
