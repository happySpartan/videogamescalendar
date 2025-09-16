from sqlalchemy import Column, Integer, String, Index
from .base import Base, TimestampedBase

class Language(Base, TimestampedBase):
    """Game languages based on IGDB API schema - PostgreSQL optimized"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    igdb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    native_name = Column(String(100))
    locale = Column(String(10), index=True)
    checksum = Column(String(255), unique=True)
    
    # Table args for text search
    __table_args__ = (
        Index('ix_languages_name_trgm', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
    )
    
    def __repr__(self):
        return f"<Language(id={self.id}, name={self.name})>"