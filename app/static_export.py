"""Static JSON export of the release calendar (ADR-0004).

Pulls a window of games straight from IGDB (no Postgres/Redis), applies the
same normalization and EU release-date rule (ADR-0002) as the sync worker, and
writes plain JSON files the frontend reads in static mode:

    <out>/meta.json                  generation time, window, counts
    <out>/genres.json                [{id, name, slug, game_count}]
    <out>/platforms.json             [{id, name, abbreviation, game_count}]
    <out>/releases/YYYY-MM.json      {"releases": [...]} for that month
    <out>/games/<igdb_id>.json       game detail
    <out>/calendar.ics               iCalendar feed, all platforms
    <out>/calendars/platform-<id>.ics  iCalendar feed per platform

Game ids in the exported files are IGDB ids (there is no database id).

Run (needs IGDB_CLIENT_ID / IGDB_CLIENT_SECRET):
    python -m app.static_export --out frontend/public/data
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.ical import build_calendar
from app.sync.igdb_client import IGDBService

logger = logging.getLogger(__name__)

PAGE_SIZE = 100
# IGDB allows 4 requests/second; each page is 2+ requests (games + release_dates).
PAGE_DELAY_SECONDS = 0.6
# The canonical EU date can be later than IGDB's earliest worldwide
# first_release_date, so fetch a little before the window starts.
FETCH_PADDING_SECONDS = 60 * 86400
# Calendar feeds carry upcoming releases plus this much recent history.
FEED_HISTORY = timedelta(days=30)


def _month_start(year: int, month: int) -> datetime:
    # Normalize month overflow/underflow (e.g. month 14 -> Feb next year).
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return datetime(year, month, 1, tzinfo=UTC)


def export_window(now: datetime, months_back: int, months_ahead: int) -> tuple[datetime, datetime]:
    """Half-open ``[start, end)`` window of whole months around ``now``."""
    start = _month_start(now.year, now.month - months_back)
    end = _month_start(now.year, now.month + months_ahead + 1)
    return start, end


def _iso(ts: int | None) -> str | None:
    return datetime.fromtimestamp(ts, tz=UTC).isoformat() if ts else None


def _release(game: dict) -> dict[str, Any]:
    """Calendar entry, same shape as one item of ``GET /releases``."""
    cover = game.get("cover") or {}
    return {
        "id": game["id"],
        "name": game.get("name") or "",
        "slug": game.get("slug"),
        "release_date": _iso(game.get("first_release_date")),
        "cover_url": cover.get("url"),
        "rating": game.get("rating"),
        "genres": [{"id": g["id"], "name": g.get("name")} for g in game.get("genres") or []],
        "platforms": [
            {"id": p["id"], "name": p.get("name"), "abbreviation": p.get("abbreviation")}
            for p in game.get("platforms") or []
        ],
    }


def _detail(game: dict) -> dict[str, Any]:
    """Game detail, the ``GET /games/{id}`` shape plus ``release_date``."""
    release = _release(game)
    companies = [ic["company"] for ic in game.get("involved_companies") or []]
    return {
        **release,
        "igdb_id": game["id"],
        "first_release_date": release["release_date"],
        "summary": game.get("summary"),
        "storyline": game.get("storyline"),
        "rating_count": game.get("rating_count"),
        "total_rating": game.get("total_rating"),
        "total_rating_count": game.get("total_rating_count"),
        "aggregated_rating": game.get("aggregated_rating"),
        "aggregated_rating_count": game.get("aggregated_rating_count"),
        "screenshots": [s["url"] for s in game.get("screenshots") or [] if s.get("url")],
        "videos": game.get("videos") or [],
        "websites": game.get("websites") or [],
        "companies": [
            {"id": c["id"], "name": c.get("name"), "description": c.get("description")}
            for c in companies
        ],
        "franchises": [
            {"id": f["id"], "name": f.get("name")} for f in game.get("franchises") or []
        ],
        "regions": [
            {"id": r["id"], "code": r.get("identifier")} for r in game.get("regions") or []
        ],
        "url": game.get("url"),
    }


async def _get_page_with_retry(
    igdb: IGDBService, offset: int, window: tuple[int, int], attempts: int = 4
) -> list[dict]:
    for attempt in range(attempts):
        try:
            return await igdb.get_games(limit=PAGE_SIZE, offset=offset, released_between=window)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt == attempts - 1:
                raise
            await asyncio.sleep(2**attempt)
    return []


async def fetch_games(igdb: IGDBService, start: datetime, end: datetime) -> list[dict]:
    """All normalized games whose IGDB date falls in the (padded) window."""
    await igdb.authenticate()
    window = (int(start.timestamp()) - FETCH_PADDING_SECONDS, int(end.timestamp()))
    games: list[dict] = []
    offset = 0
    while True:
        page = await _get_page_with_retry(igdb, offset, window)
        games.extend(page)
        logger.info("Fetched %s games (offset %s)", len(games), offset)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        await asyncio.sleep(PAGE_DELAY_SECONDS)
    return games


def build_files(
    games: list[dict],
    start: datetime,
    end: datetime,
    now: datetime,
    site_url: str | None = None,
    platform_catalogue: list[dict] | None = None,
) -> dict[str, Any]:
    """Map of relative path -> payload (JSON value, or ``str`` for .ics) per file.

    ``platform_catalogue`` (IGDB's full platform list) gets a feed per platform
    even when none of its games is in the window, so a subscribed feed URL
    stays valid (an empty calendar) instead of turning into a 404.
    """
    start_ts, end_ts = start.timestamp(), end.timestamp()
    in_window = [
        g
        for g in games
        if g.get("id")
        and g.get("first_release_date")
        and start_ts <= g["first_release_date"] < end_ts
    ]
    in_window.sort(key=lambda g: (g["first_release_date"], g.get("name") or ""))

    files: dict[str, Any] = {}
    months: dict[str, list[dict]] = defaultdict(list)
    genres: dict[int, dict] = {}
    platforms: dict[int, dict] = {}
    genre_counts: dict[int, int] = defaultdict(int)
    platform_counts: dict[int, int] = defaultdict(int)

    for game in in_window:
        release = _release(game)
        months[release["release_date"][:7]].append(release)
        files[f"games/{game['id']}.json"] = _detail(game)
        for g in release["genres"]:
            genres[g["id"]] = g
            genre_counts[g["id"]] += 1
        for p in release["platforms"]:
            platforms[p["id"]] = p
            platform_counts[p["id"]] += 1

    # Every month in the window gets a file, so an empty month is an empty
    # list rather than a 404.
    cursor = start
    while cursor < end:
        key = cursor.strftime("%Y-%m")
        files[f"releases/{key}.json"] = {"releases": months.get(key, [])}
        cursor = _month_start(cursor.year, cursor.month + 1)

    files["genres.json"] = sorted(
        ({**g, "game_count": genre_counts[gid]} for gid, g in genres.items()),
        key=lambda g: g.get("name") or "",
    )
    files["platforms.json"] = sorted(
        ({**p, "game_count": platform_counts[pid]} for pid, p in platforms.items()),
        key=lambda p: p.get("name") or "",
    )
    # Calendar feeds: recent + upcoming releases, all platforms and per platform.
    feed_from = (now - FEED_HISTORY).date().isoformat()
    feed = [r for releases in months.values() for r in releases if r["release_date"] >= feed_from]
    files["calendar.ics"] = build_calendar(feed, "Video game releases", now, site_url)
    feed_platforms = {p["id"]: p for p in platform_catalogue or [] if p.get("id")}
    feed_platforms.update(platforms)
    for pid, platform in feed_platforms.items():
        on_platform = [r for r in feed if any(p["id"] == pid for p in r["platforms"])]
        files[f"calendars/platform-{pid}.ics"] = build_calendar(
            on_platform, f"Video game releases — {platform.get('name')}", now, site_url
        )

    files["meta.json"] = {
        "generated_at": now.isoformat(),
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "game_count": len(in_window),
        "months": {k: len(v) for k, v in sorted(months.items())},
        "feed_count": len(feed),
    }
    return files


def write_files(out: Path, files: dict[str, Any]) -> None:
    for rel, payload in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            # newline="" keeps the CRLF line endings iCalendar requires.
            path.write_text(payload, encoding="utf-8", newline="")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


async def run(
    out: Path, months_back: int, months_ahead: int, site_url: str | None = None
) -> dict[str, Any]:
    now = datetime.now(UTC)
    start, end = export_window(now, months_back, months_ahead)
    igdb = IGDBService(
        client_id=os.getenv("IGDB_CLIENT_ID"),
        client_secret=os.getenv("IGDB_CLIENT_SECRET"),
    )
    games = await fetch_games(igdb, start, end)
    platform_catalogue = await igdb.get_platforms()
    files = build_files(games, start, end, now, site_url, platform_catalogue)
    write_files(out, files)
    meta: dict[str, Any] = files["meta.json"]
    return meta


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=Path("frontend/public/data"))
    parser.add_argument("--months-back", type=int, default=2)
    parser.add_argument("--months-ahead", type=int, default=12)
    parser.add_argument("--site-url", help="Deployed site root, for game links in the feeds")
    args = parser.parse_args()
    meta = asyncio.run(run(args.out, args.months_back, args.months_ahead, args.site_url or None))
    logger.info("Exported %s games: %s", meta["game_count"], json.dumps(meta["months"]))


if __name__ == "__main__":
    main()
