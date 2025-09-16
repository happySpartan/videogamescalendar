"""
Shared database models for the Video Game Calendar microservices.
These models are used across all services.
"""
from .base import Base, TimestampedBase
from .game import Game
from .genre import Genre
from .platform import Platform
from .language import Language
from .region import Region
from .company import Company
from .franchise import Franchise

__all__ = [
    'Base',
    'TimestampedBase',
    'Game',
    'Genre',
    'Platform',
    'Language',
    'Region',
    'Company',
    'Franchise'
]