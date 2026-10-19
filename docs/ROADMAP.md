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
4. **Browser pass on the live site** (#8) — done against the deployed Pages build (real
   IGDB data): month/week views, >500-release months, search, filters, game pages, feeds.
   It found the dead "+N more" badge and big releases buried behind indie titles; both
   fixed (day list dialog, days ordered by IGDB hypes + follows).

Dropped with the VPS: provisioning (#4), compose deploy (#5), admin hardening (#7) and
database backups (#9) — the static site has no server, admin surface or database.

## Phase 2 — Calendar export (iCal) (#2) — done

Let people subscribe to releases from Google/Apple/Outlook Calendar.

1. **`calendar.ics` feed** (#10) — written by the static export: all-day events on the EU
   release date for upcoming releases plus the last 30 days, a stable per-game UID so moved
   dates update in place, `REFRESH-INTERVAL` of 6 hours to match the export cadence.
2. **Per-platform feeds** (#11) — `calendars/platform-<id>.ics` for every IGDB platform
   (empty when it has no releases, so a subscribed URL never turns into a 404).
3. **Subscribe button** (#12) — header dialog (static build only): pick a platform, then
   open the `webcal://` link, add to Google Calendar, or copy the feed URL.

## Phase 3 — Richer game pages (#3) — done

1. **Sync videos + websites** (#13) — `videos.video_id,videos.name` and `websites.url` are
   fetched by both the sync worker and the static export. Store links are recognised by
   host (Steam, PlayStation Store, Xbox, Nintendo eShop, Epic, GOG, itch.io, app stores)
   rather than IGDB's website type enum. Screenshots now use the 16:9 `t_screenshot_big`
   size (they were cropped to the cover size).
2. **Trailers + screenshot gallery** (#14) — click-to-load YouTube player
   (`youtube-nocookie.com`, nothing loads until played), video switcher, screenshot grid
   with a full-size viewer.
3. **Store links** (#15) — store buttons plus up to three other sites (official site etc.).

## Later / ideas (not committed)

- Uptime monitoring + error alerts for the sync (e.g. a healthcheck ping).
- Open Graph tags per game page for nicer sharing.
- "This week" view as a landing page.
