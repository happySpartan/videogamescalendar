"""
Many-to-many association tables for the video game calendar.

A game belongs to many genres, platforms, companies, franchises, languages and
regions. These association tables model those relationships so a game can be
filtered by any of them (e.g. "all games on PS5" or "all RPGs releasing this
month"). Using real relational tables instead of JSONB keeps filtering correct
and indexable.
"""
from sqlalchemy import Column, ForeignKey, Index, Integer, Table

from .base import Base

game_genres = Table(
    "game_genres",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_genres_genre_id", "genre_id"),
)

game_platforms = Table(
    "game_platforms",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("platform_id", Integer, ForeignKey("platforms.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_platforms_platform_id", "platform_id"),
)

game_companies = Table(
    "game_companies",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("company_id", Integer, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_companies_company_id", "company_id"),
)

game_franchises = Table(
    "game_franchises",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("franchise_id", Integer, ForeignKey("franchises.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_franchises_franchise_id", "franchise_id"),
)

game_languages = Table(
    "game_languages",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", Integer, ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_languages_language_id", "language_id"),
)

game_regions = Table(
    "game_regions",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("region_id", Integer, ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_game_regions_region_id", "region_id"),
)
