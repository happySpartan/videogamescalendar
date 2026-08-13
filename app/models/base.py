from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base


def _utcnow() -> datetime:
    return datetime.now(UTC)


Base = declarative_base()


class TimestampedBase:
    """Base class that adds timestamp columns to models.

    created_at / updated_at / downloaded_at are timezone-aware datetimes so they
    can be serialized with ``.isoformat()`` by the API layer.
    """
    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, index=True)
    downloaded_at = Column(DateTime(timezone=True), default=_utcnow, index=True)
