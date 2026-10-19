"""Offline unit verification of the static JSON export (ADR-0004).

Run:  .venv/bin/python tests/test_static_export.py
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.static_export import build_files, export_window
from app.sync.igdb_client import IGDBService


def ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=UTC).timestamp())


def mk(igdb_id, name, release_dates, genres=(), platforms=()):
    raw = {
        "id": igdb_id,
        "name": name,
        "slug": name.lower(),
        "cover": {"image_id": f"co{igdb_id}"},
        "genres": [{"id": g, "name": f"Genre {g}"} for g in genres],
        "platforms": [
            {"id": p, "name": f"Platform {p}", "abbreviation": f"P{p}"} for p in platforms
        ],
    }
    return IGDBService()._normalize_game(raw, release_dates)


passed = 0


def check(name, got, want):
    global passed
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}: {name} (got={got}, want={want})")
    if not ok:
        sys.exit(1)
    passed += 1


now = datetime(2026, 10, 19, tzinfo=UTC)

# 1. Window covers whole months, crossing the year boundary.
start, end = export_window(now, months_back=2, months_ahead=3)
check("Window start", start, datetime(2026, 8, 1, tzinfo=UTC))
check("Window end (exclusive)", end, datetime(2027, 2, 1, tzinfo=UTC))

games = [
    # EU date wins over the earlier Worldwide one (ADR-0002) -> November.
    mk(
        1,
        "Alpha",
        [
            {"date": ts(2026, 10, 1), "release_region": 8, "status": 0},
            {"date": ts(2026, 11, 5), "release_region": 1, "status": 0},
        ],
        genres=[10],
        platforms=[48],
    ),
    mk(2, "Beta", [{"date": ts(2026, 11, 2), "release_region": 8}], genres=[10, 12]),
    # Outside the window -> not exported.
    mk(3, "Gamma", [{"date": ts(2027, 6, 1), "release_region": 1}], genres=[12]),
    # TBA (only a JP date) -> not exported.
    mk(4, "Delta", [{"date": ts(2026, 11, 1), "release_region": 5}]),
]
files = build_files(games, start, end, now)

nov = files["releases/2026-11.json"]["releases"]
# 2. Month bucket holds in-window games, sorted by date.
check("November ids sorted by date", [r["id"] for r in nov], [2, 1])
check("EU date used", nov[1]["release_date"], "2026-11-05T00:00:00+00:00")
check("Cover URL carried", nov[0]["cover_url"].endswith("/co2.jpg"), True)

# 3. Every month in the window has a file, empty ones included.
check(
    "Month files",
    sorted(k for k in files if k.startswith("releases/")),
    [
        f"releases/{m}.json"
        for m in ("2026-08", "2026-09", "2026-10", "2026-11", "2026-12", "2027-01")
    ],
)
check("Empty month is an empty list", files["releases/2026-10.json"], {"releases": []})

# 4. Detail files only for exported games, with both date keys.
check(
    "Detail files",
    sorted(k for k in files if k.startswith("games/")),
    ["games/1.json", "games/2.json"],
)
check(
    "Detail release_date",
    files["games/1.json"]["release_date"],
    files["games/1.json"]["first_release_date"],
)

# 5. Reference data counts only exported games.
check(
    "Genre counts",
    [(g["id"], g["game_count"]) for g in files["genres.json"]],
    [(10, 2), (12, 1)],
)
check("Platform counts", [(p["id"], p["game_count"]) for p in files["platforms.json"]], [(48, 1)])
check("Meta month counts", files["meta.json"]["months"], {"2026-11": 2})

print(f"\nAll {passed} checks passed.")
