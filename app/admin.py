"""Admin API routes for the video game calendar.

Token-gated operational surface: system stats, cache management and data-sync
triggering. Mounted under ``/admin`` by ``app.main`` and guarded by
``deps.verify_admin_token``. Sync tasks are enqueued through the shared
``app.sync.celery_app`` so they land on the same broker the worker consumes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from . import deps
from .models import Company, Franchise, Game, Genre, Platform
from .sync.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# System statistics ----------------------------------------------------------
@router.get("/stats/overview")
async def get_system_overview(
    db: AsyncSession = Depends(deps.get_db),
    token: str = Depends(deps.verify_admin_token),
):
    """Get system overview statistics."""
    stats_queries = {
        "games": select(func.count(Game.id)),
        "genres": select(func.count(Genre.id)),
        "platforms": select(func.count(Platform.id)),
        "companies": select(func.count(Company.id)),
        "franchises": select(func.count(Franchise.id)),
    }

    stats = {}
    for key, query in stats_queries.items():
        stats[key] = (await db.execute(query)).scalar()

    yesterday = datetime.utcnow() - timedelta(days=1)
    stats["games_added_24h"] = (
        await db.execute(select(func.count(Game.id)).where(Game.created_at >= yesterday))
    ).scalar()
    stats["games_updated_24h"] = (
        await db.execute(select(func.count(Game.id)).where(Game.updated_at >= yesterday))
    ).scalar()

    return {"overview": stats, "timestamp": _now_iso()}


@router.get("/stats/database")
async def get_database_stats(
    db: AsyncSession = Depends(deps.get_db),
    token: str = Depends(deps.verify_admin_token),
):
    """Get database performance statistics."""
    try:
        table_sizes_query = text(
            """
            SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """
        )
        table_sizes = [
            {"table": row.tablename, "size": row.size, "size_bytes": row.size_bytes}
            for row in (await db.execute(table_sizes_query))
        ]

        index_stats_query = text(
            """
            SELECT indexrelname as index_name, relname as table_name, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes ORDER BY idx_tup_read DESC LIMIT 10;
            """
        )
        index_stats = [
            {
                "index": row.index_name,
                "table": row.table_name,
                "reads": row.idx_tup_read,
                "fetches": row.idx_tup_fetch,
            }
            for row in (await db.execute(index_stats_query))
        ]

        return {"table_sizes": table_sizes, "index_usage": index_stats, "timestamp": _now_iso()}
    except Exception as e:
        logger.warning("Could not get detailed database stats: %s", e)
        return {
            "message": "Database statistics not available",
            "error": str(e),
            "timestamp": _now_iso(),
        }


# Cache management -----------------------------------------------------------
@router.get("/cache/stats")
async def get_cache_stats(token: str = Depends(deps.verify_admin_token)):
    """Get Redis cache statistics."""
    if not deps.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    info = await deps.redis_client.info()
    return {
        "connected_clients": info.get("connected_clients", 0),
        "used_memory_human": info.get("used_memory_human", "N/A"),
        "used_memory": info.get("used_memory", 0),
        "keyspace_hits": info.get("keyspace_hits", 0),
        "keyspace_misses": info.get("keyspace_misses", 0),
        "total_commands_processed": info.get("total_commands_processed", 0),
        "uptime_in_seconds": info.get("uptime_in_seconds", 0),
        "timestamp": _now_iso(),
    }


@router.delete("/cache/clear")
async def clear_cache(
    pattern: str | None = Query(None, description="Cache key pattern to clear"),
    token: str = Depends(deps.verify_admin_token),
):
    """Clear Redis cache entries."""
    if not deps.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    if pattern:
        keys = await deps.redis_client.keys(pattern)
        if keys:
            deleted = await deps.redis_client.delete(*keys)
            return {"message": f"Cleared {deleted} cache entries matching '{pattern}'"}
        return {"message": f"No cache entries found matching '{pattern}'"}
    await deps.redis_client.flushdb()
    return {"message": "Cleared all cache entries"}


# Data sync management -------------------------------------------------------
@router.post("/sync/games")
async def trigger_game_sync(
    full_sync: bool = Body(False, description="Perform full sync instead of delta"),
    token: str = Depends(deps.verify_admin_token),
):
    """Trigger a manual game sync via the shared Celery app."""
    if not deps.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")

    result = celery_app.send_task("data_sync.sync_games", kwargs={"full_sync": full_sync})
    return {
        "message": f"{'Full' if full_sync else 'Delta'} sync task queued",
        "task_id": result.id,
        "timestamp": _now_iso(),
    }


@router.post("/sync/games/{igdb_id}")
async def trigger_single_game_sync(
    igdb_id: int,
    token: str = Depends(deps.verify_admin_token),
):
    """Trigger sync for a specific game by IGDB ID."""
    if not deps.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")

    result = celery_app.send_task("data_sync.sync_single_game", args=[igdb_id])
    return {
        "message": f"Single game sync queued for IGDB ID {igdb_id}",
        "task_id": result.id,
        "timestamp": _now_iso(),
    }


# Data management ------------------------------------------------------------
@router.get("/data/games/recent")
async def get_recent_games(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of games"),
    db: AsyncSession = Depends(deps.get_db),
    token: str = Depends(deps.verify_admin_token),
):
    """Get recently added or updated games."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = (
        select(Game)
        .where((Game.created_at >= cutoff_date) | (Game.updated_at >= cutoff_date))
        .order_by(Game.updated_at.desc())
        .limit(limit)
    )
    games = (await db.execute(query)).scalars().all()

    return {
        "days": days,
        "count": len(games),
        "timestamp": _now_iso(),
        "games": [
            {
                "id": g.id,
                "igdb_id": g.igdb_id,
                "name": g.name,
                "created_at": g.created_at.isoformat(),
                "updated_at": g.updated_at.isoformat(),
                "rating": g.rating,
                "total_rating": g.total_rating,
            }
            for g in games
        ],
    }


@router.get("/data/games/problematic")
async def get_problematic_games(
    db: AsyncSession = Depends(deps.get_db),
    token: str = Depends(deps.verify_admin_token),
):
    """Get games with missing or problematic data."""
    issues = []

    no_name_games = (
        (await db.execute(select(Game).where((Game.name == "") | (Game.name.is_(None))).limit(10)))
        .scalars()
        .all()
    )
    if no_name_games:
        issues.append(
            {
                "type": "missing_name",
                "count": len(no_name_games),
                "games": [{"id": g.id, "igdb_id": g.igdb_id} for g in no_name_games],
            }
        )

    no_date_games = (
        (await db.execute(select(Game).where(Game.first_release_date.is_(None)).limit(10)))
        .scalars()
        .all()
    )
    if no_date_games:
        issues.append(
            {
                "type": "missing_release_date",
                "count": len(no_date_games),
                "games": [
                    {"id": g.id, "igdb_id": g.igdb_id, "name": g.name} for g in no_date_games
                ],
            }
        )

    no_relations_query = (
        select(Game)
        .outerjoin(Game.genres)
        .outerjoin(Game.platforms)
        .group_by(Game.id)
        .having((func.count(Genre.id) == 0) & (func.count(Platform.id) == 0))
        .limit(10)
    )
    no_relations_games = (await db.execute(no_relations_query)).scalars().all()
    if no_relations_games:
        issues.append(
            {
                "type": "missing_relations",
                "count": len(no_relations_games),
                "games": [
                    {"id": g.id, "igdb_id": g.igdb_id, "name": g.name} for g in no_relations_games
                ],
            }
        )

    return {"issues": issues, "timestamp": _now_iso()}


# System maintenance ---------------------------------------------------------
@router.post("/maintenance/cleanup")
async def trigger_cleanup(token: str = Depends(deps.verify_admin_token)):
    """Trigger the data cleanup task."""
    if not deps.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for task queue")

    result = celery_app.send_task("data_sync.cleanup_old_data")
    return {
        "message": "Cleanup task queued",
        "task_id": result.id,
        "timestamp": _now_iso(),
    }
