"""
Celery worker for background IGDB data synchronization.

Beats:
    hourly  delta game sync
    daily   full game sync (2am)
    weekly  data cleanup   (Sunday 3am)
"""

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import CursorResult, delete, select

from app.db import sync_session_factory
from app.models import Company, Franchise, Game, Genre, Language, Platform, Region
from app.models.associations import (
    game_companies,
    game_franchises,
    game_genres,
    game_languages,
    game_platforms,
    game_regions,
)

from .celery_app import celery_app
from .igdb_client import IGDBService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real IGDB client (requires IGDB_CLIENT_ID / IGDB_CLIENT_SECRET env vars).
igdb_service = IGDBService(
    client_id=os.getenv("IGDB_CLIENT_ID"),
    client_secret=os.getenv("IGDB_CLIENT_SECRET"),
)

# --- reference data ---------------------------------------------------------


async def _upsert_by_igdb_id(db, model, data: dict, fields: tuple) -> object:
    """Update-or-create a reference row keyed by IGDB id."""
    existing = db.query(model).filter_by(igdb_id=data["id"]).first()
    obj = existing if existing else model(igdb_id=data["id"])
    for field in fields:
        setattr(obj, field, data.get(field))
    if obj not in db:
        db.add(obj)
    return obj


async def _sync_reference_data(db):
    logger.info("Syncing reference data (genres, platforms, companies)")
    for genre in await igdb_service.get_genres():
        await _upsert_by_igdb_id(db, Genre, genre, ("name", "slug", "url"))
    for platform in await igdb_service.get_platforms():
        await _upsert_by_igdb_id(
            db,
            Platform,
            platform,
            ("name", "abbreviation", "slug", "category", "generation", "summary", "url"),
        )
    for company in await igdb_service.get_companies():
        await _upsert_by_igdb_id(
            db, Company, company, ("name", "slug", "description", "country", "start_date")
        )
    db.commit()


# --- games ------------------------------------------------------------------


async def _process_game_data(db, game_data: dict) -> Game:
    game = db.query(Game).filter_by(igdb_id=game_data["id"]).first()
    if game is None:
        game = Game(igdb_id=game_data["id"])
        db.add(game)

    game.name = game_data.get("name", "")
    game.slug = game_data.get("slug", "")
    game.summary = game_data.get("summary")
    game.storyline = game_data.get("storyline")

    ts = game_data.get("first_release_date")
    game.first_release_date = datetime.fromtimestamp(ts, tz=UTC) if ts else None

    game.rating = game_data.get("rating")
    game.rating_count = game_data.get("rating_count")
    game.total_rating = game_data.get("total_rating")
    game.total_rating_count = game_data.get("total_rating_count")
    game.aggregated_rating = game_data.get("aggregated_rating")
    game.aggregated_rating_count = game_data.get("aggregated_rating_count")

    cover = game_data.get("cover") or {}
    if cover.get("url"):
        game.cover_url = cover["url"]

    screenshots = [s.get("url") for s in (game_data.get("screenshots") or []) if s.get("url")]
    game.screenshots = screenshots
    game.videos = game_data.get("videos") or []
    game.websites = game_data.get("websites") or []

    game.status = game_data.get("status")
    game.category = game_data.get("category")
    game.hypes = game_data.get("hypes")
    game.follows = game_data.get("follows")
    game.url = game_data.get("url")

    game.metadata_ = {"sync_timestamp": datetime.now(UTC).isoformat()}

    await _process_game_relationships(db, game, game_data)
    return cast(Game, game)


async def _lookup_or_create(db, model, igdb_id: int, defaults: dict):
    # Deduplicate within the current session/transaction: with SQLAlchemy's
    # batched (insertmanyvalues) flush, a pending object added for ``igdb_id``
    # is not yet visible to a follow-up ``query().filter_by().first()``, so two
    # games referencing the same (not-yet-committed) company/franchise would
    # each create a row and violate the unique ``igdb_id`` index. A session-
    # bound cache keyed by (model, igdb_id) makes the second reference reuse
    # the same in-flight object instead.
    cache: dict = db.info.setdefault("_sync_ref_cache", {})
    key = (model, igdb_id)
    if key in cache:
        return cache[key]

    obj = db.query(model).filter_by(igdb_id=igdb_id).first()
    if obj is None:
        obj = model(igdb_id=igdb_id, **defaults)
        db.add(obj)
    cache[key] = obj
    return obj


async def _process_game_relationships(db, game: Game, game_data: dict) -> None:
    game.genres.clear()
    game.platforms.clear()
    game.companies.clear()
    game.franchises.clear()
    game.languages.clear()
    game.regions.clear()

    def _add_unique(collection, obj) -> None:
        # A game can reference the same entity more than once (e.g. a studio
        # appearing in several involved-companies roles). Appending it twice
        # would emit a duplicate many-to-many row and trip the association
        # table's unique (game_id, ref_id) index, so skip anything already
        # present. The many-to-many collection is a list; `in` is an identity
        # check here (our models don't define __eq__).
        if obj not in collection:
            collection.append(obj)

    for g in game_data.get("genres") or []:
        obj = await _lookup_or_create(
            db, Genre, g["id"], {"name": g.get("name"), "slug": g.get("slug")}
        )
        _add_unique(game.genres, obj)
    for p in game_data.get("platforms") or []:
        obj = await _lookup_or_create(
            db,
            Platform,
            p["id"],
            {"name": p.get("name"), "abbreviation": p.get("abbreviation")},
        )
        _add_unique(game.platforms, obj)
    for ic in game_data.get("involved_companies") or []:
        comp = ic.get("company") or {}
        if comp.get("id"):
            obj = await _lookup_or_create(
                db,
                Company,
                comp["id"],
                {"name": comp.get("name"), "description": comp.get("description")},
            )
            _add_unique(game.companies, obj)
    for f in game_data.get("franchises") or []:
        obj = await _lookup_or_create(
            db, Franchise, f["id"], {"name": f.get("name"), "slug": f.get("slug")}
        )
        _add_unique(game.franchises, obj)
    for lang in game_data.get("languages") or []:
        obj = await _lookup_or_create(
            db,
            Language,
            lang["id"],
            {"name": lang.get("name"), "native_name": lang.get("native_name")},
        )
        _add_unique(game.languages, obj)
    for r in game_data.get("regions") or []:
        obj = await _lookup_or_create(
            db,
            Region,
            r["id"],
            {"identifier": r.get("identifier"), "name": r.get("name") or r.get("identifier")},
        )
        _add_unique(game.regions, obj)


# --- tasks ------------------------------------------------------------------


@celery_app.task(bind=True, name="data_sync.sync_games")
def sync_games(self, full_sync: bool = False):
    """Sync games from IGDB (full, or delta since last run)."""
    logger.info("Starting game sync (full_sync=%s)", full_sync)
    updated_after = None if full_sync else datetime.now(UTC).timestamp() - 3600
    try:
        return {"result": asyncio.run(_sync_games_async(updated_after)), "full_sync": full_sync}
    except Exception as exc:
        logger.exception("Game sync failed")
        raise self.retry(countdown=300, max_retries=3) from exc


async def _sync_games_async(updated_after: float | None):
    """Async implementation of game sync. Returns total synced count."""
    await igdb_service.authenticate()

    synced_count = 0
    offset = 0
    limit = 100

    with sync_session_factory() as db:
        await _sync_reference_data(db)
        while True:
            games_data = await igdb_service.get_games(
                limit=limit, offset=offset, updated_after=updated_after
            )
            if not games_data:
                break
            for gd in games_data:
                try:
                    await _process_game_data(db, gd)
                    synced_count += 1
                except Exception:
                    logger.exception("Failed to process game %s", gd.get("id"))
            db.commit()
            offset += limit
            if len(games_data) < limit:
                break

    logger.info("Game sync completed. Processed %s games", synced_count)
    return {"synced_count": synced_count, "full_sync": updated_after is None}


@celery_app.task(bind=True, name="data_sync.sync_single_game")
def sync_single_game(self, igdb_game_id: int):
    """Sync a single game by IGDB ID."""
    logger.info("Syncing single game: %s", igdb_game_id)
    try:
        return asyncio.run(_sync_single_game_async(igdb_game_id))
    except Exception as exc:
        logger.exception("Single game sync failed")
        raise self.retry(countdown=60, max_retries=3) from exc


async def _sync_single_game_async(igdb_game_id: int):
    await igdb_service.authenticate()
    game_data = await igdb_service.get_game_by_id(igdb_game_id)
    if game_data is None:
        msg = f"Game not found or no release date: {igdb_game_id}"
        raise ValueError(msg)

    with sync_session_factory() as db:
        await _sync_reference_data(db)
        game = await _process_game_data(db, game_data)
        db.commit()
        return {"game_id": game.id, "igdb_id": game.igdb_id, "name": game.name}


@celery_app.task(name="data_sync.cleanup_old_data")
def cleanup_old_data():
    """Remove stale/placeholder rows and orphaned association entries."""
    try:
        logger.info("Starting data cleanup")
        cutoff = datetime.now(UTC) - timedelta(days=30)

        with sync_session_factory() as db:
            removed_games = 0
            # Games that still have no real release date after a grace period.
            stale = (
                db.query(Game)
                .filter(Game.first_release_date.is_(None), Game.downloaded_at < cutoff)
                .all()
            )
            for game in stale:
                db.delete(game)
                removed_games += 1

            # Orphaned association rows whose parent game no longer exists.
            live_game_ids = select(Game.id)
            removed_rows = 0
            for table in (
                game_genres,
                game_platforms,
                game_companies,
                game_franchises,
                game_languages,
                game_regions,
            ):
                result = cast(
                    CursorResult,
                    db.execute(delete(table).where(table.c.game_id.not_in(live_game_ids))),
                )
                removed_rows += result.rowcount or 0

            db.commit()
            return {
                "stale_games_removed": removed_games,
                "orphaned_association_rows": removed_rows,
            }
    except Exception as exc:
        logger.error("Data cleanup failed: %s", exc, exc_info=True)
        raise


@celery_app.task(name="data_sync.health_check")
def health_check():
    """Health check task."""
    try:
        with sync_session_factory() as db:
            game_count = db.query(Game).count()
        return {
            "status": "healthy",
            "game_count": game_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        logger.exception("Health check failed")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        }


if __name__ == "__main__":
    celery_app.start()
