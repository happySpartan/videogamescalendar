"""Application entry point for the video game calendar API.

One FastAPI process serves the public game/release routes (``app.api``) and the
token-gated admin routes (``app.admin``). The lifespan wires the DB health check
and the shared Redis client. Run with::

    uvicorn app.main:app --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import deps
from .admin import router as admin_router
from .api import router as api_router
from .config import settings
from .db import test_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown: verify DB and open the Redis client."""
    logger.info("Starting Video Game Calendar API...")

    if test_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise RuntimeError("Cannot connect to database")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = aioredis.from_url(redis_url, decode_responses=True)
    try:
        await client.ping()
        logger.info("Redis connection successful")
        deps.set_redis_client(client)
    except Exception as exc:
        logger.error("Redis connection failed: %s", exc)
        await client.close()
        deps.set_redis_client(None)

    yield

    logger.info("Shutting down Video Game Calendar API...")
    current = deps.redis_client
    if current is not None:
        await current.close()
    deps.set_redis_client(None)


app = FastAPI(
    title="Video Game Calendar API",
    description="Public release calendar + token-gated admin API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check():
    """Liveness probe: reports DB and Redis connectivity."""
    health_status = {
        "status": "healthy",
        "service": "app",
        "database": "unknown",
        "redis": "unknown",
    }

    if test_connection():
        health_status["database"] = "connected"
    else:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"

    if deps.redis_client:
        try:
            await deps.redis_client.ping()
            health_status["redis"] = "connected"
        except Exception:
            health_status["redis"] = "error"
            health_status["status"] = "degraded"
    else:
        health_status["redis"] = "not configured"

    return health_status
