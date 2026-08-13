"""Shared FastAPI dependencies for the video game calendar app.

A single process serves both the public game/release API and the token-gated
admin API, so the DB session dependency, the Redis cache client and the admin
auth dependency live here instead of being duplicated per router.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .db import async_session_factory

logger = logging.getLogger(__name__)

# Bearer-token scheme used by the admin routes.
security = HTTPBearer(auto_error=True)

# Redis client, initialised by the app lifespan in ``app.main``.
redis_client: aioredis.Redis | None = None


def set_redis_client(client: aioredis.Redis | None) -> None:
    """Set the process-global Redis client (called from the app lifespan)."""
    global redis_client
    redis_client = client


async def get_db() -> AsyncSession:
    """Yield an async DB session to a route handler."""
    async with async_session_factory() as session:
        yield session


async def get_redis() -> aioredis.Redis | None:
    """Return the process-global Redis client (may be None if unavailable)."""
    return redis_client


async def get_cached_or_fetch(cache_key: str, fetch_func: Any, expiry: int = 300) -> Any:
    """Return cached data or fetch-and-cache it. Best-effort: never raises."""
    if not redis_client:
        return await fetch_func()

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as exc:
        logger.warning("Cache read error for %s: %s", cache_key, exc)

    data = await fetch_func()

    try:
        await redis_client.setex(cache_key, expiry, json.dumps(data, default=str))
    except Exception as exc:
        logger.warning("Cache write error for %s: %s", cache_key, exc)

    return data


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Reject requests that do not present the configured admin token."""
    expected = os.getenv("ADMIN_TOKEN", "admin_secret_token")
    if credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials
