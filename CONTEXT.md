# Context — Videogame Calendar

Project glossary (single context). Pure domain vocabulary, implementation-free.
This file is a glossary of what things ARE, not a spec. Updated the moment a term resolves.

- **Videogame Calendar** — what the product IS: a web app that shows a monthly calendar of
  video-game releases. The core value is "what comes out, and when", EU-centric.
  _Avoid_: "game calendar", "release tracker" as interchangeable synonyms — the calendar
  view is the product, the underlying data is a set of releases.

- **Game** — a title in the catalog (e.g. "Zelda: Tears of the Kingdom"). Has a name,
  is associated to genres, platforms, a studio/company and optionally a franchise.

- **Release** — a Game's dated calendar event. One Game has exactly ONE canonical Release
  shown on the calendar, on one day (see **EU release date**). Not to be confused with the
  many raw dates IGDB may hold for a game — the sync collapses those into one.

- **EU release date** — the single canonical date a Game appears on the calendar. Defined by
  the **release-date rule**: prefer an IGDB entry whose region is Europe (1); among several
  EU dates prefer the one whose human-readable label/note matches the announced date, else
  the earliest. Fall back to the Worldwide (8) region under the same rule. With no dated entry
  at all, the Game is **TBA**.
  _Avoid_: "release_date"/"first_release_date" as two different columns — there is ONE date.

- **Worldwide (IGDB region 8)** — the fallback region used when a Game has no Europe-dated
  IGDB entry, so well-known titles aren't marked TBA just for lacking an EU row. IGDB region
  codes: 1=Europe, 8=Worldwide, 2=NA, 3=AU, 5=JP.

- **TBA** — a Game with no usable date under the release-date rule. Shown as "TBA", kept in
  the catalog, but NOT placed on the calendar grid until it acquires a date.

- **Released / Upcoming** — derived status of a Game from its **EU release date**:
  released = date ≤ now, upcoming = date > now. Derived, never stored as separate columns.

- **Genre / Platform** — the two filter dimensions of the catalog. A Game has many-to-many
  relationships to both. Used by the calendar's filter bar.

- **Studio (Company)** — the maker of a Game. A Game belongs to a Company; optionally a
  Game belongs to one **Franchise** (a series identity spanning multiple Games).

- **Sync** — the recurring process that pulls data from **IGDB** into the catalog and computes
  each Game's **EU release date**. Runs on a schedule (the **sync cadence**), and can be
  triggered manually from **Admin**.

- **Sync cadence** — how often the **Sync** runs. Current choice: keep the existing cadence.

- **IGDB** — the external data source (release dates, genres, platforms, companies, franchises).
  The catalog is populated entirely from it; the app holds no hand-entered game data.

- **Admin** — the token-gated operations surface for things like triggering a manual **Sync**.
  v1 has no end-user accounts; only this admin ops surface exists, gated by a token.

- **Calendar** — the product's primary view: a month grid of **Releases** bucketed by day.
  Loading a month is one request for that month's window; days are grouped client-side.
  _Avoid_: using "calendar" to mean the underlying release data — the data is **Releases**.