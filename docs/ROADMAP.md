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
- Single VPS with Docker Compose — [ADR-0003](adr/0003-vps-docker-compose-deploy.md),
  superseded for the public site by a static GitHub Pages build —
  [ADR-0004](adr/0004-static-site-on-github-pages.md)
- Domain: already owned.

## Phase 1 — Ship v1 (live on GitHub Pages with domain + HTTPS) (#1)

Switched from a VPS to a static site on GitHub Pages ([ADR-0004](adr/0004-static-site-on-github-pages.md)):
$0, nothing to operate. Definition of done: `https://<domain>` serves the calendar with real
IGDB data, refreshed every 6 hours by `.github/workflows/pages.yml`.

1. **Static export + static frontend mode + Pages workflow** — done in the repo.
2. **Enable Pages** — Settings → Pages → Source: GitHub Actions; merge to `main` to deploy.
3. **Custom domain** (#6) — Settings → Pages → Custom domain + DNS record, enforce HTTPS.
4. **Browser pass on the live site** (#8) — month view, navigation, filters, search and
   `/game/:id` deep links with real data; fix whatever breaks.

Dropped with the VPS: provisioning (#4), compose deploy (#5), admin hardening (#7) and
database backups (#9) — the static site has no server, admin surface or database.

## Phase 2 — Calendar export (iCal) (#2)

Let people subscribe to releases from Google/Apple/Outlook Calendar.

1. **`calendar.ics` feed** (#10) — iCalendar feed of upcoming releases (all-day events on
   the EU release date; TBA games excluded). With the static site this is a file written by
   the export, not an API route. (The UI already has a one-off "Export ICS" download.)
2. **Filtered feeds** (#11) — per-platform feed files (e.g. `calendar-switch.ics`) so a
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
