"""iCalendar (RFC 5545) feeds of releases, for calendar-app subscriptions.

Each release is an all-day event on its EU release date (ADR-0002). The event
UID is derived from the IGDB id only, so when a game's date moves the calendar
app updates the existing event instead of adding a second one.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

PRODID = "-//Videogame Calendar//EN"
# Matches the export cadence (.github/workflows/pages.yml): ask apps to re-fetch
# every 6 hours (most apps poll less often regardless).
REFRESH_INTERVAL = "PT6H"


def _escape(text: str) -> str:
    """Escape a TEXT value (RFC 5545 §3.3.11)."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold a content line at 75 octets without splitting a UTF-8 character."""
    out: list[str] = []
    current = ""
    size = 0
    limit = 75
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > limit:
            out.append(current)
            current, size, limit = " ", 1, 75
        current += char
        size += width
    out.append(current)
    return "\r\n".join(out)


def _day(value: date) -> str:
    return value.strftime("%Y%m%d")


def build_calendar(
    releases: list[dict],
    name: str,
    generated_at: datetime,
    site_url: str | None = None,
) -> str:
    """Render ``releases`` (``GET /releases`` items) as one VCALENDAR document.

    Releases without a ``release_date`` (TBA) are skipped. ``site_url`` (the
    deployed site root) adds a link to each game's page when given.
    """
    stamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
        "X-WR-CALDESC:Video game release dates (EU)",
        f"REFRESH-INTERVAL;VALUE=DURATION:{REFRESH_INTERVAL}",
        f"X-PUBLISHED-TTL:{REFRESH_INTERVAL}",
    ]
    for release in releases:
        if not release.get("release_date"):
            continue
        day = date.fromisoformat(release["release_date"][:10])
        platforms = ", ".join(p.get("name") or "" for p in release.get("platforms") or [])
        url = f"{site_url.rstrip('/')}/game/{release['id']}" if site_url else None
        description = "\n".join(filter(None, [platforms, url]))
        lines += [
            "BEGIN:VEVENT",
            f"UID:igdb-{release['id']}@videogamescalendar",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{_day(day)}",
            # DTEND is exclusive: an all-day event ends the next day.
            f"DTEND;VALUE=DATE:{_day(day + timedelta(days=1))}",
            f"SUMMARY:{_escape(release.get('name') or '')}",
            *([f"DESCRIPTION:{_escape(description)}"] if description else []),
            *([f"URL:{url}"] if url else []),
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "".join(_fold(line) + "\r\n" for line in lines)
