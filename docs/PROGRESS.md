# Progress & Outstanding Work

> Product goals and the phased plan live in [ROADMAP.md](ROADMAP.md).

Living status of the Video Game Calendar project: **open / in-flight work first**, then a
concise **archive** of what's done. Facts that are finished and stable belong in
[README](../README.md) / ADRs, not here.

> The one-shot architecture plan (`.hermes/plans/2026-08-11_…md`) is **complete and retired**;
> its leftover open items are folded into the Open Tasks below.

## Current status

Repo is on a **single consolidated backend** (ADR-0001), the **EU release-date rule**
(ADR-0002) is implemented and unit-verified, CI runs a real Postgres/Redis runtime pass, and
the **live IGDB sync is proven end-to-end**. The public site is now a **static build on
GitHub Pages** (ADR-0004, replacing the VPS plan of ADR-0003): a scheduled workflow exports
IGDB data to JSON and deploys the frontend in static mode. It has **not deployed yet** —
Pages must be enabled and the workflow merged to `main`.

```md
[x] CI green (ruff/mypy/tsc/build + Docker + runtime pass)
[x] ADR-0002 release-date rule implemented + tested
[x] IGDB live sync proven against real credentials
[x] Static export + static frontend mode + Pages workflow (ADR-0004)
[ ] First Pages deploy with real data + custom domain   ← main remaining work
```

## Open Tasks (todo)

### 1. First GitHub Pages deploy (ADR-0004) — main epic

Enable **Settings → Pages → Source: GitHub Actions**, merge to `main` (or run the
"Static site (GitHub Pages)" workflow), check the export log's per-month counts, then add
the custom domain. See README → Deployment (static site on GitHub Pages).

### 2. Browser-test the frontend against a running API

CI covers the offline runtime gap (`/releases`, `/genres`, `/platforms` smoke tests on real
Postgres/Redis), but no human/automated browser test of the calendar UI — rendering, filters,
deep-link `/game/:id` — has ever run. Run `npm run dev` against the backend and verify the
calendar month view, filtering, and navigation.

### 3. Security hardening (only if the VPS stack is ever deployed)

- Keep `/admin/*` off the public reverse proxy (or add auth in front of it).
- Rotate/use the `ADMIN_TOKEN` from `.env`; never bake it into the frontend build.
- Confirm `.env` files are gitignored (do not commit `IGDB_CLIENT_SECRET` / `ADMIN_TOKEN`).

---

## Archive — Done

### Completed features & integration

- **Single `app/` package** (ADR-0001): one FastAPI process serves public + admin routes;
  same package runs Celery worker/beat + Alembic migrations.
- **EU release-date rule** (ADR-0002) in `app/sync/igdb_client.py`: Europe → Worldwide → TBA,
  label-aware. Unit-verified by `python tests/test_release_date_rule.py` (all 7 checks pass).
- **Live IGDB sync proven end-to-end** against real Codespace-secret credentials — 92 upcoming
  games (Aug–Dec 2026) with canonical EU/WW dates; `GET /releases` serves them.
- **Frontend** wired to the typed API client via React Router + TanStack Query; `/releases`
  powers the calendar.
- **CI** (`.github/workflows/ci.yml`): offline gates (ruff/mypy/tsc/build) + Docker-build +
  runtime job (migrations → boot → smoke-test endpoints). Live IGDB sync runs only when real
  secrets are present.
- **Python 3.14** port (cp314-compatible pins; ruff + mypy clean; verified on CPython 3.14.7).

### Completed tasks & fixes

- **CORS** wired end-to-end (`CORS_ORIGINS` env, default `*`); documented in `.env.example` +
  runbook.
- **Frontend → API URL** actually reaches the Vite build: removed a stale `frontend/.env`
  (`:5050`), added `frontend/.dockerignore`, and made `VITE_GAME_API_URL` a build arg
  (runtime `environment:` had no effect). Verified baked URLs.
- **Dependabot config** committed, pinned to the three current manifests (was auto-running
  against deleted `services/*` dirs).
- **Dependabot advisories** resolved: bumped `fastapi`, `python-multipart`, `python-dotenv` to
  CVE-clean pins (vulns were not exploitable here — no multipart routes).
- **"Uncommitted" working-tree edits** reviewed + committed as two scoped commits (`d410e560`
  py3.14 bump; `2755f562` Dependabot fix), plus the related `.devcontainer/*` cleanups.

### Bug fixes: live IGDB integration (from the end-to-end proof)

- **`release_dates` field is `release_region`, not `region`** — old code read `region`, which
  is always `None`, so every game collapsed to TBA. Switched field + selector + unit test.
- **Dropped `game_localizations.language.name`** — IGDB rejects it as invalid.
- **`companies.start_date` INT4 → BIGINT** — pre-1970 studios (Nintendo 1889, negative epoch)
  overflowed INT4. Migration `2e9c41fbb2a7`.
- **`worker.py` session-scoped dedup cache** in `_lookup_or_create` — batched
  (insertmanyvalues) flush hid in-flight rows, so the same company/franchise could be inserted
  twice → unique `igdb_id` violation. Cache keyed by `(model, igdb_id)` reuses the in-flight
  object; added an `_add_unique` guard against duplicate many-to-many appends.
- **`app/api.py`**: `/games/search` declared before `/games/{game_id}` (route-order swallow),
  `regions` detail field is `identifier` not `code`, `/genres` + `/platforms` eager-load
  `games` to avoid N+1 on `game_count`.
- **`app/main.py`**: Redis client close uses `close()` (runtime-available) instead of
  `aclose()` — fixed lifespan teardown.