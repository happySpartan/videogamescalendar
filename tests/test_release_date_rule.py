"""Offline unit verification of the ADR-0002 EU release-date rule.

Run:  .venv/bin/python tests/test_release_date_rule.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sync.igdb_client import select_release_date


def mk(date=None, region=None, human=None, status=0, category=None):
    e = {}
    if category is not None:
        e["category"] = category
    if date is not None:
        e["date"] = date
    if region is not None:
        e["release_region"] = region
    if human is not None:
        e["human"] = human
    e["status"] = status
    return e


passed = 0


def check(name, got, want):
    global passed
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}: {name} (got={got}, want={want})")
    if not ok:
        sys.exit(1)
    passed += 1


# 1. Prefers a usable EU date over a Worldwide one.
check(
    "EU preferred over Worldwide",
    select_release_date(
        [mk(100, region=8, human="Nov 2024"), mk(200, region=1, human="18 Nov 2024")]
    ),
    200,
)

# 2. Falls back to Worldwide when no EU entry.
check(
    "Worldwide fallback when no EU",
    select_release_date([mk(100, region=2, human="NA"), mk(300, region=8, human="Mar 1, 2024")]),
    300,
)

# 3. TBA (None) when only non-EU/non-WW regions exist.
check(
    "TBA when no EU/WW",
    select_release_date([mk(100, region=2, human="NA"), mk(150, region=5, human="JP")]),
    None,
)

# 4. Empty input -> None.
check("Empty input is TBA", select_release_date([]), None)

# 5. Among several EU dates, prefers the one with a human label even if later.
check(
    "Label-aware picks announced date",
    select_release_date([mk(100, region=1, human=None), mk(400, region=1, human="20 Dec 2024")]),
    400,
)

# 6. Ignores cancelled (status 5) / postponed (6) EU entries.
check(
    "Cancelled/postponed EU entries excluded",
    select_release_date(
        [
            mk(100, region=1, human="old", status=5),
            mk(200, region=1, human="real", status=0),
        ]
    ),
    200,
)

# 7. Among all-labelled EU dates, picks earliest (tie-break).
check(
    "Earliest among labelled EU dates",
    select_release_date(
        [
            mk(500, region=1, human="later"),
            mk(300, region=1, human="earlier"),
        ]
    ),
    300,
)

# 8. Imprecise dates (year/quarter/month/TBD, stored as the period's last day)
#    are not calendar days: fall back to an exact Worldwide date.
check(
    "Year-only EU date skipped (category)",
    select_release_date([mk(900, region=1, human="2026", category=2), mk(400, region=8)]),
    400,
)
check(
    "Quarter EU date skipped (human label only)",
    select_release_date([mk(900, region=1, human="Q1 2027"), mk(400, region=8)]),
    400,
)
check(
    "Month-only date skipped",
    select_release_date([mk(900, region=1, human="Dec 2026")]),
    None,
)
check(
    "Exact day kept",
    select_release_date([mk(500, region=1, human="Nov 5, 2026", category=0)]),
    500,
)

print(f"\nAll {passed} checks passed.")
