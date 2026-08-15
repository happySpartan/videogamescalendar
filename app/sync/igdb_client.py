"""
Real IGDB (Twitch) API client.

Replaces the previous mock so the data-sync worker pulls genuine game data.

Auth flow (OAuth client-credentials):
  POST https://id.twitch.tv/oauth2/token
      ?client_id=...&client_secret=...&grant_type=client_credentials
  -> access_token (+ expires_in ~ 50 days). The token is cached and refreshed
     before it expires.

Data flow (Apicalypse):
  POST https://api.igdb.com/v4/<endpoint>
  Headers: Client-ID, Authorization: Bearer <token>
  Body: an Apicalypse query string, e.g.
      fields name,slug,first_release_date;
      where first_release_date != null & updated_at > 12345;
      sort first_release_date asc;
      limit 100; offset 0;

The get_games() method returns dicts normalized to the shape the sync worker
expects, so worker._process_game_data() can consume them with no mapping drift.
"""

from __future__ import annotations

import logging
import time
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

# IGDB region codes (see docs/adr/0002-eu-release-date-rule.md).
REGION_EUROPE = 1
REGION_WORLDWIDE = 8

# IGDB release_dates.status: 0=released, 2=rumored, 3=announced, 4=in development,
# 5=cancelled, 6=postponed. Entries that are cancelled/postponed are not candidates
# for the canonical date (they are stale or superseded dates, not the real one).
EXCLUDED_RELEASE_STATUS = {5, 6}

IMAGE_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"

AUTH_URL = "https://id.twitch.tv/oauth2/token"
API_URL = "https://api.igdb.com/v4"

# Fields requested for game endpoints (kept in one place so the list and
# single-game fetches stay in sync).
GAME_FIELDS: str = (
    "id,name,slug,summary,storyline,first_release_date,"
    "rating,rating_count,total_rating,total_rating_count,"
    "aggregated_rating,aggregated_rating_count,"
    "cover.image_id,screenshots.image_id,"
    "genres.id,genres.name,"
    "platforms.id,platforms.name,platforms.abbreviation,"
    "involved_companies.company.id,involved_companies.company.name,"
    "involved_companies.company.description,"
    "franchises.id,franchises.name,"
    "game_localizations.region.identifier,"
    "status,category,hypes,follows,url,updated_at"
)


# Fields for the release_dates endpoint (region + human label feed ADR-0002).
RELEASE_DATE_FIELDS: str = "id,game,date,release_region,human,m,y,platform,category,status,checksum"


def _image_url(image_id: str | None) -> str | None:
    if not image_id:
        return None
    return IMAGE_URL.format(image_id=image_id)


def _release_sort_key(entry: dict) -> tuple[int, int | float]:
    """Key used to pick the canonical date among a set of candidates.

    Prefers the date with the most humans/notes detail (a concrete label beats
    a bare ``m``/``y``), ties broken by earliest date. ``date`` may be None for
    TBA entries, which sort last via float('inf').
    """
    detail = 0 if entry.get("human") else 1
    date = entry.get("date") or float("inf")
    return (detail, date)


def select_release_date(release_dates: list[dict]) -> int | None:
    """Pick the single canonical unix-epoch release date for a game (ADR-0002).

    Order of preference:
      1. A Europe (region 1) dated entry whose status is not cancelled/postponed.
      2. A Worldwide (region 8) dated entry, same rule.
      3. Otherwise ``None`` (the game is TBA).

    Among several candidates for the same region we prefer the one carrying a
    human-readable label (the "announced date" signal) and, failing that, the
    earliest concrete date — never a blind cross-region "earliest wins".
    """
    if not release_dates:
        return None

    def _candidates(region: int) -> list[dict]:
        return [
            e
            for e in release_dates
            if e.get("release_region") == region
            and e.get("date") is not None
            and e.get("status") not in EXCLUDED_RELEASE_STATUS
        ]

    for region in (REGION_EUROPE, REGION_WORLDWIDE):
        candidates = _candidates(region)
        if not candidates:
            continue
        best = min(candidates, key=_release_sort_key)
        return int(best["date"])

    return None


class IGDBService:
    """Minimal, resilient client for the IGDB API."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_url: str = API_URL,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self.access_token: str | None = None
        self._token_expires_at: float = 0.0

    # -- auth ---------------------------------------------------------------
    async def authenticate(self) -> None:
        """Obtain (or refresh) an OAuth access token, caching it until expiry."""
        if (
            self.access_token and time.time() < self._token_expires_at - 60  # refresh 60s early
        ):
            return

        if not self.client_id or not self.client_secret:
            raise RuntimeError("IGDB_CLIENT_ID and IGDB_CLIENT_SECRET env vars are required")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                AUTH_URL,
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        self.access_token = data["access_token"]
        # Twitch client-credentials tokens are long-lived; default to 24h if the
        # API ever omits expires_in.
        expires_in = data.get("expires_in", 86400)
        self._token_expires_at = time.time() + expires_in
        logger.info("IGDB OAuth token acquired (expires in %ss)", expires_in)

    # -- low-level ----------------------------------------------------------
    async def _post(self, endpoint: str, query: str) -> list[dict[Any, Any]]:
        if not self.access_token:
            await self.authenticate()
        headers = {
            "Client-ID": self.client_id or "",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.api_url}/{endpoint}", headers=headers, content=query)
            resp.raise_for_status()
            return cast(list[dict[Any, Any]], resp.json())

    def _build_query(
        self,
        include: str,
        where: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "id asc",
    ) -> str:
        parts = [f"fields {include};"]
        if where:
            parts.append(f"where {where};")
        parts.append(f"limit {limit};")
        if offset:
            parts.append(f"offset {offset};")
        parts.append(f"sort {sort};")
        return "\n".join(parts)

    # -- reference data -----------------------------------------------------
    async def get_genres(self) -> list[dict]:
        query = self._build_query("id,name,slug", limit=500)
        return await self._post("genres", query)

    async def get_platforms(self) -> list[dict]:
        query = self._build_query(
            "id,name,abbreviation,slug,category,generation,summary,url", limit=500
        )
        return await self._post("platforms", query)

    async def get_companies(self) -> list[dict]:
        query = self._build_query("id,name,slug,description,country,start_date,url", limit=500)
        return await self._post("companies", query)

    # -- games --------------------------------------------------------------
    async def get_games(
        self,
        limit: int = 100,
        offset: int = 0,
        updated_after: float | None = None,
    ) -> list[dict]:
        """Fetch games, normalized to the shape the sync worker consumes.

        ``updated_after`` (unix seconds) turns the call into a delta sync
        (only games whose `updated_at` is newer are returned). Per-game
        ``release_dates`` are fetched so each normalized dict carries the
        canonical ADR-0002 ``first_release_date``.
        """
        include = GAME_FIELDS
        where = "first_release_date != null"
        if updated_after is not None:
            where += f" & updated_at > {int(updated_after)}"

        query = self._build_query(include, where=where, limit=limit, offset=offset, sort="id asc")
        raw = await self._post("games", query)
        if not raw:
            return []

        game_ids = [g["id"] for g in raw if g.get("id")]
        rd_by_game = await self.get_release_dates(game_ids) if game_ids else {}
        return [self._normalize_game(g, rd_by_game.get(int(g.get("id") or 0), [])) for g in raw]

    async def get_game_by_id(self, igdb_id: int) -> dict | None:
        """Fetch a single game by IGDB id (None if not found / no release date)."""
        query = self._build_query(
            GAME_FIELDS,
            where=f"id = {int(igdb_id)} & first_release_date != null",
            limit=1,
        )
        raw = await self._post("games", query)
        if not raw:
            return None
        rd = await self.get_release_dates([int(igdb_id)])
        return self._normalize_game(raw[0], rd.get(int(igdb_id), []))

    async def get_release_dates(self, game_ids: list[int]) -> dict[int, list[dict]]:
        """Fetch release_dates rows for the given game ids, grouped by game id.

        Used to pick the canonical EU release date (see ``select_release_date``).
        """
        if not game_ids:
            return {}
        ids = ",".join(str(int(i)) for i in game_ids)
        query = self._build_query(RELEASE_DATE_FIELDS, where=f"game = ({ids})", limit=500)
        raw = await self._post("release_dates", query)

        grouped: dict[int, list[dict]] = {}
        for row in raw:
            game_ref = row.get("game")
            gid = game_ref.get("id") if isinstance(game_ref, dict) else game_ref
            if gid is None:
                continue
            grouped.setdefault(int(gid), []).append(row)
        return grouped

    def _normalize_game(self, g: dict, release_dates: list[dict] | None = None) -> dict:
        def _ids(items: Any) -> list[dict]:
            if not items:
                return []
            return [
                {"id": it.get("id"), "name": it.get("name")}
                for it in items
                if isinstance(it, dict) and it.get("id")
            ]

        # involved_companies carries company objects nested under `company`.
        companies: list[dict] = []
        for ic in g.get("involved_companies") or []:
            comp = ic.get("company") if isinstance(ic, dict) else None
            if isinstance(comp, dict) and comp.get("id"):
                companies.append(
                    {
                        "id": comp["id"],
                        "name": comp.get("name"),
                        "description": comp.get("description"),
                    }
                )

        # languages / regions come from game_localizations.
        languages, regions = [], []
        for loc in g.get("game_localizations") or []:
            if isinstance(loc, dict):
                if loc.get("language", {}).get("id"):
                    lang = loc["language"]
                    languages.append({"id": lang["id"], "name": lang.get("name")})
                if loc.get("region", {}).get("id"):
                    reg = loc["region"]
                    regions.append({"id": reg["id"], "identifier": reg.get("identifier")})

        cover_image = (
            (g.get("cover") or {}).get("image_id") if isinstance(g.get("cover"), dict) else None
        )
        screenshots = [
            {"url": _image_url(s.get("image_id"))}
            for s in (g.get("screenshots") or [])
            if isinstance(s, dict) and s.get("image_id")
        ]

        # Canonical release date per ADR-0002: prefer a usable EU date, then
        # Worldwide, else TBA. When no release_dates rows were supplied (e.g.
        # callers that only need the game object), fall back to the raw
        # game-level date so the worker always has something to store.
        canonical_release = select_release_date(release_dates) if release_dates else None
        first_release_date = canonical_release
        if first_release_date is None and not release_dates:
            first_release_date = g.get("first_release_date")

        return {
            "id": g.get("id"),
            "name": g.get("name"),
            "slug": g.get("slug"),
            "summary": g.get("summary"),
            "storyline": g.get("storyline"),
            "first_release_date": first_release_date,  # unix int
            "release_date_source": "release_dates" if release_dates else "game",
            "rating": g.get("rating"),
            "rating_count": g.get("rating_count"),
            "total_rating": g.get("total_rating"),
            "total_rating_count": g.get("total_rating_count"),
            "aggregated_rating": g.get("aggregated_rating"),
            "aggregated_rating_count": g.get("aggregated_rating_count"),
            "cover": {"url": _image_url(cover_image)} if cover_image else None,
            "screenshots": screenshots,
            "genres": _ids(g.get("genres")),
            "platforms": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "abbreviation": p.get("abbreviation"),
                }
                for p in (g.get("platforms") or [])
                if isinstance(p, dict) and p.get("id")
            ],
            "involved_companies": [{"company": c} for c in companies],
            "franchises": _ids(g.get("franchises")),
            "languages": languages,
            "regions": regions,
            "status": g.get("status"),
            "category": g.get("category"),
            "hypes": g.get("hypes"),
            "follows": g.get("follows"),
            "url": g.get("url"),
            "updated_at": g.get("updated_at"),
        }
