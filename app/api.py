"""Public (non-admin) API routes for the video game calendar.

Serves the calendar-facing endpoints the frontend consumes: ``/releases`` for
the month/week window, ``/games`` + ``/games/{id}`` for detail, ``/genres`` and
``/platforms`` for filter reference data. Routes are registered as an
``APIRouter`` included by ``app.main``.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .deps import get_cached_or_fetch, get_db
from .models import Game, Genre, Platform

logger = logging.getLogger(__name__)

router = APIRouter(tags=["games"])


# Game endpoints -------------------------------------------------------------
@router.get("/games", response_model=dict[str, Any])
async def get_games(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search term"),
    genre_id: int | None = Query(None, description="Filter by genre ID"),
    platform_id: int | None = Query(None, description="Filter by platform ID"),
    release_year: int | None = Query(None, description="Filter by release year"),
):
    """Get a paginated list of games with optional filtering."""
    cache_key = (
        f"games:page:{page}:limit:{limit}:search:{search}:genre:{genre_id}:"
        f"platform:{platform_id}:year:{release_year}"
    )

    async def fetch_games():
        query = select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.platforms),
            selectinload(Game.companies),
        )

        filters: list[ColumnElement[bool]] = []
        if search:
            filters.append(Game.name.ilike(f"%{search}%"))
        if genre_id:
            filters.append(Game.genres.any(Genre.id == genre_id))
        if platform_id:
            filters.append(Game.platforms.any(Platform.id == platform_id))
        if release_year:
            filters.append(func.extract("year", Game.first_release_date) == release_year)

        if filters:
            query = query.where(and_(*filters))

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        games = result.scalars().all()

        count_query = select(func.count(Game.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        total_count = (await db.execute(count_query)).scalar() or 0

        games_data = []
        for game in games:
            games_data.append(
                {
                    "id": game.id,
                    "name": game.name,
                    "summary": game.summary,
                    "storyline": game.storyline,
                    "first_release_date": game.first_release_date.isoformat()
                    if game.first_release_date
                    else None,
                    "rating": game.rating,
                    "rating_count": game.rating_count,
                    "total_rating": game.total_rating,
                    "total_rating_count": game.total_rating_count,
                    "cover_url": game.cover_url,
                    "screenshots": game.screenshots,
                    "metadata": game.metadata_,
                    "genres": [{"id": g.id, "name": g.name} for g in game.genres],
                    "platforms": [{"id": p.id, "name": p.name} for p in game.platforms],
                    "companies": [{"id": c.id, "name": c.name} for c in game.companies],
                    "created_at": game.created_at.isoformat(),
                    "updated_at": game.updated_at.isoformat(),
                }
            )
        return {
            "games": games_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
            },
        }

    return await get_cached_or_fetch(cache_key, fetch_games, expiry=300)


@router.get("/games/{game_id}", response_model=dict[str, Any])
async def get_game_by_id(
    game_id: int = Path(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed game information by ID."""
    cache_key = f"game:{game_id}"

    async def fetch_game():
        query = (
            select(Game)
            .options(
                selectinload(Game.genres),
                selectinload(Game.platforms),
                selectinload(Game.companies),
                selectinload(Game.franchises),
                selectinload(Game.languages),
                selectinload(Game.regions),
            )
            .where(Game.id == game_id)
        )
        game = (await db.execute(query)).scalar_one_or_none()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        return {
            "id": game.id,
            "igdb_id": game.igdb_id,
            "name": game.name,
            "slug": game.slug,
            "summary": game.summary,
            "storyline": game.storyline,
            "first_release_date": game.first_release_date.isoformat()
            if game.first_release_date
            else None,
            "rating": game.rating,
            "rating_count": game.rating_count,
            "total_rating": game.total_rating,
            "total_rating_count": game.total_rating_count,
            "aggregated_rating": game.aggregated_rating,
            "aggregated_rating_count": game.aggregated_rating_count,
            "cover_url": game.cover_url,
            "screenshots": game.screenshots,
            "videos": game.videos,
            "websites": game.websites,
            "metadata": game.metadata_,
            "genres": [{"id": g.id, "name": g.name, "slug": g.slug} for g in game.genres],
            "platforms": [
                {"id": p.id, "name": p.name, "abbreviation": p.abbreviation} for p in game.platforms
            ],
            "companies": [
                {"id": c.id, "name": c.name, "description": c.description} for c in game.companies
            ],
            "franchises": [{"id": f.id, "name": f.name, "slug": f.slug} for f in game.franchises],
            "languages": [
                {"id": lang.id, "name": lang.name, "native_name": lang.native_name}
                for lang in game.languages
            ],
            "regions": [{"id": r.id, "name": r.name, "code": r.code} for r in game.regions],
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
        }

    return await get_cached_or_fetch(cache_key, fetch_game, expiry=600)


@router.get("/games/search", response_model=dict[str, Any])
async def search_games(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Full-text search for games."""
    cache_key = f"search:games:{q}:{limit}"

    async def fetch_search_results():
        query = (
            select(Game)
            .options(selectinload(Game.genres), selectinload(Game.platforms))
            .where(
                or_(
                    Game.name.ilike(f"%{q}%"),
                    Game.summary.ilike(f"%{q}%"),
                    func.similarity(Game.name, q) > 0.1,
                )
            )
            .order_by(
                func.similarity(Game.name, q).desc(),
                Game.total_rating_count.desc().nullslast(),
            )
            .limit(limit)
        )
        games = (await db.execute(query)).scalars().all()

        return {
            "query": q,
            "count": len(games),
            "results": [
                {
                    "id": g.id,
                    "name": g.name,
                    "summary": g.summary,
                    "first_release_date": g.first_release_date.isoformat()
                    if g.first_release_date
                    else None,
                    "rating": g.rating,
                    "cover_url": g.cover_url,
                    "genres": [gen.name for gen in g.genres[:3]],
                    "platforms": [p.name for p in g.platforms[:3]],
                }
                for g in games
            ],
        }

    return await get_cached_or_fetch(cache_key, fetch_search_results, expiry=600)


# Release calendar endpoint --------------------------------------------------
@router.get("/releases", response_model=dict[str, Any])
async def get_releases(
    db: AsyncSession = Depends(get_db),
    from_date: date | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    genre_id: int | None = Query(None, description="Filter by genre ID"),
    platform_id: int | None = Query(None, description="Filter by platform ID"),
    status: str | None = Query(None, description="released | upcoming | tba"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
):
    """Get calendar releases within an optional date range.

    This is the primary endpoint the frontend calendar uses to fill a month
    view (``from``/``to``) or the "upcoming" list (``status=upcoming``). The
    limit is allowed up to 500 so a single request can cover a busy month and be
    bucketed by day client-side.
    """
    cache_key = (
        f"releases:from:{from_date}:to:{to_date}:genre:{genre_id}:"
        f"platform:{platform_id}:status:{status}:page:{page}:limit:{limit}"
    )

    async def fetch_releases():
        now = datetime.now(UTC)

        start_dt = None
        end_dt = None
        if from_date:
            start_dt = datetime.combine(from_date, time.min, tzinfo=UTC)
        if to_date:
            end_dt = datetime.combine(to_date, time.max, tzinfo=UTC)

        query = select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.platforms),
            selectinload(Game.companies),
        )

        filters: list[ColumnElement[bool]] = []
        if status == "released":
            filters.append(Game.first_release_date.isnot(None))
            filters.append(Game.first_release_date <= now)
        elif status == "upcoming":
            filters.append(Game.first_release_date.isnot(None))
            filters.append(Game.first_release_date > now)
        elif status == "tba":
            filters.append(Game.first_release_date.is_(None))

        if start_dt is not None:
            filters.append(Game.first_release_date >= start_dt)
        if end_dt is not None:
            filters.append(Game.first_release_date <= end_dt)
        if genre_id:
            filters.append(Game.genres.any(Genre.id == genre_id))
        if platform_id:
            filters.append(Game.platforms.any(Platform.id == platform_id))

        if filters:
            query = query.where(and_(*filters))

        offset = (page - 1) * limit
        base_count = select(func.count(Game.id))
        total_count = (
            await db.execute(base_count.where(and_(*filters)) if filters else base_count)
        ).scalar()

        result = await db.execute(
            query.order_by(Game.first_release_date.asc()).offset(offset).limit(limit)
        )
        games = result.scalars().all()

        releases = []
        for game in games:
            releases.append(
                {
                    "id": game.id,
                    "name": game.name,
                    "slug": game.slug,
                    "release_date": game.first_release_date.isoformat()
                    if game.first_release_date
                    else None,
                    "cover_url": game.cover_url,
                    "rating": game.rating,
                    "genres": [{"id": g.id, "name": g.name} for g in game.genres],
                    "platforms": [
                        {"id": p.id, "name": p.name, "abbreviation": p.abbreviation}
                        for p in game.platforms
                    ],
                }
            )

        return {
            "releases": releases,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit if total_count else 0,
            },
        }

    return await get_cached_or_fetch(cache_key, fetch_releases, expiry=300)


# Genre endpoints ------------------------------------------------------------
@router.get("/genres", response_model=list[dict[str, Any]])
async def get_genres(db: AsyncSession = Depends(get_db)):
    """Get all genres."""
    cache_key = "genres:all"

    async def fetch_genres():
        genres = (await db.execute(select(Genre).order_by(Genre.name))).scalars().all()
        return [
            {
                "id": genre.id,
                "name": genre.name,
                "slug": genre.slug,
                "description": genre.description,
                "game_count": len(genre.games) if hasattr(genre, "games") else 0,
            }
            for genre in genres
        ]

    return await get_cached_or_fetch(cache_key, fetch_genres, expiry=1800)


# Platform endpoints ---------------------------------------------------------
@router.get("/platforms", response_model=list[dict[str, Any]])
async def get_platforms(db: AsyncSession = Depends(get_db)):
    """Get all platforms."""
    cache_key = "platforms:all"

    async def fetch_platforms():
        platforms = (await db.execute(select(Platform).order_by(Platform.name))).scalars().all()
        return [
            {
                "id": platform.id,
                "name": platform.name,
                "abbreviation": platform.abbreviation,
                "alternative_names": platform.alternative_names,
                "generation": platform.generation,
                "platform_family": platform.platform_family,
                "game_count": len(platform.games) if hasattr(platform, "games") else 0,
            }
            for platform in platforms
        ]

    return await get_cached_or_fetch(cache_key, fetch_platforms, expiry=1800)
