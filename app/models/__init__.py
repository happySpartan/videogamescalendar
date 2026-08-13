"""
Shared database models for the Video Game Calendar microservices.
These models are used across all services.
"""
from .base import Base, TimestampedBase
from .company import Company
from .franchise import Franchise
from .game import Game
from .genre import Genre
from .language import Language
from .platform import Platform
from .region import Region

__all__ = [
    "Base",
    "Company",
    "Franchise",
    "Game",
    "Genre",
    "Language",
    "Platform",
    "Region",
    "TimestampedBase"
]
