from sqlalchemy import Column, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .associations import game_companies
from .base import Base, TimestampedBase


class Company(Base, TimestampedBase):
    """Video game companies based on IGDB API schema - PostgreSQL optimized"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), unique=True, index=True)
    description = Column(Text)
    country = Column(Integer, index=True)
    websites = Column(JSONB)  # Store as JSONB for better querying
    start_date = Column(Integer)
    checksum = Column(String(255), unique=True)

    # Relationships
    games = relationship("Game", secondary=game_companies, back_populates="companies")

    # Table args for text search
    __table_args__ = (
        Index(
            "ix_companies_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index("ix_companies_websites_gin", "websites", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"
