# 2. EU-centric release date with Worldwide fallback

**Status**: Accepted

**Context**: The whole calendar hangs on one date per Game, but IGDB returns multiple raw
release dates per game across regions (1=Europe, 8=Worldwide, 2=NA, 3=AU, 5=JP) and can carry
old/cancelled dates for the same region.

**Decision**: The Sync stores ONE canonical timezone-aware release date per Game, chosen by:
(1) prefer an IGDB entry with region Europe; among several EU dates, pick the one whose
human-readable label/note matches the announced date, else the earliest; (2) else use the
Worldwide region under the same rule; (3) else mark the Game TBA (kept in catalog, absent from
the grid). Status (released/upcoming/TBA) is derived from that single date.

**Why**: Deliberately avoids blind "earliest wins", which would surface stale pre-delay dates;
uses the note/label to pick the actually-announced date when present. The Worldwide fallback
keeps well-known titles on the calendar when no EU row exists, without making it a strict
EU-or-nothing product. TBA keeps undated games visible without polluting the grid.