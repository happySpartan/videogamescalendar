# 4. Public site as a static build on GitHub Pages

**Status**: Accepted (supersedes ADR-0003 for the public site; the VPS stays an option)

**Context**: ADR-0003 chose a single always-on VPS for the full stack (FastAPI, Postgres, Redis,
Celery). The product goal is a personal/portfolio calendar at near-zero cost and ops. The
calendar data is read-only and only changes when the Sync runs, so a live API and database
are not needed to serve it.

**Decision**: A scheduled GitHub Actions workflow (`.github/workflows/pages.yml`) runs
`python -m app.static_export`, which pulls a window of games from IGDB (2 months back, 12
months ahead), applies the same normalization and EU release-date rule (ADR-0002) as the
sync worker, and writes JSON files: one per month of releases, one per game, plus genres,
platforms and metadata. The frontend is built with `VITE_DATA_MODE=static`, reading those
files instead of the API, and the result is deployed to GitHub Pages. The workflow schedule
is the sync cadence (every 6 hours); "Run workflow" is the manual sync.

**Why**: $0 hosting, no servers, database or secrets to operate, HTTPS and custom domains
included, and the agent can ship it end to end from the repo. Trade-offs accepted: data is
up to 6 hours stale; filtering and search run in the browser over a month's releases; game
ids in static mode are IGDB ids; no admin surface. The FastAPI/Celery stack stays in the repo
for local development and remains deployable per ADR-0003 if a live API is ever needed.
