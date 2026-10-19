# Roadmap

Product spec + phased plan for Videogame Calendar. Task-level status lives in
[PROGRESS.md](PROGRESS.md); domain vocabulary in the [README](../README.md#domain-glossary).

## Product spec (PRD-lite)

**Goal** — a personal tool and portfolio piece: a polished, live, EU-centric monthly
calendar of video-game releases. Success = it is publicly reachable on its own domain,
works reliably without babysitting, and is pleasant to show.

**Target user** — casual EU gamers who want to know "what comes out this month, and when".

**In scope (v1)** — what exists today: month calendar, list/grid views, search, genre and
platform filters, game detail page, IGDB sync on a schedule, token-gated admin.

**Out of scope (for now)** — user accounts, wishlists, notifications/newsletter, prices,
monetization, horizontal scaling. Revisit only if the goal changes.

**Quality bar** — minimal: keep the existing CI gates (ruff/mypy/tsc/build, Docker build,
runtime smoke test) green; add tests only where a feature needs them.

**Decisions so far**

- Single consolidated backend — [ADR-0001](adr/0001-consolidate-to-single-service.md)
- One canonical EU release date per game — [ADR-0002](adr/0002-eu-release-date-rule.md)
- Single VPS with Docker Compose — [ADR-0003](adr/0003-vps-docker-compose-deploy.md)
- Domain: already owned. VPS: not yet chosen.

## Phase 1 — Ship v1 (live on VPS with domain + TLS) (#1)

Definition of done: `https://<domain>` serves the calendar with real IGDB data, the sync
runs on schedule, `/admin/*` is not publicly reachable.

1. **Pick and provision the VPS** (#4) — choose a provider (e.g. Hetzner/OVH, 2 vCPU / 4 GB),
   create the box, SSH hardening (key-only, firewall allowing 22/80/443).
2. **Deploy the stack** (#5) — follow the README runbook: install Docker, clone, set `.env`,
   `docker compose up -d --build`, verify `/health` and `/releases`.
3. **Domain + TLS** (#6) — point DNS at the VPS, put Caddy in front (automatic HTTPS), serve
   frontend and API under the domain, set `CORS_ORIGINS` and `VITE_GAME_API_URL` to it.
4. **Admin hardening** (#7) — keep `/admin/*` off the public proxy (or behind extra auth),
   generate a fresh `ADMIN_TOKEN`, confirm no secrets in the repo or frontend bundle.
5. **Manual browser pass** (#8) — verify month view, navigation, filters, search and
   `/game/:id` deep links against the live API; fix whatever breaks.
6. **Backups** (#9) — nightly `pg_dump` to off-box storage (data is re-syncable from IGDB, so
   this is cheap insurance, not critical).

## Phase 2 — Calendar export (iCal) (#2)

Let people subscribe to releases from Google/Apple/Outlook Calendar.

1. **`GET /calendar.ics`** (#10) — iCalendar feed of upcoming releases (all-day events on the
   EU release date; TBA games excluded), cached in Redis like `/releases`.
2. **Filtered feeds** (#11) — same endpoint accepts `platform` / `genre` query params so a
   user can subscribe to e.g. "Switch releases only".
3. **Subscribe button in the UI** (#12) — copies the feed URL (with the active filters) and
   offers a `webcal://` link.

## Phase 3 — Richer game pages (#3)

IGDB already has the data; most of the work is fetching and rendering it.

1. **Sync videos + websites** (#13) — add `videos.video_id,videos.name` and
   `websites.url,websites.category` to `GAME_FIELDS` and map them in the worker
   (the `videos` / `websites` columns already exist but are never populated).
2. **Trailers + screenshot gallery** (#14) — embed YouTube trailers and show the
   already-synced screenshots on the detail page.
3. **Store links** (#15) — show Steam / PlayStation / Xbox / Nintendo eShop / Epic / GOG links
   from IGDB websites, with platform icons.

## Later / ideas (not committed)

- Uptime monitoring + error alerts for the sync (e.g. a healthcheck ping).
- Open Graph tags per game page for nicer sharing.
- "This week" view as a landing page.
