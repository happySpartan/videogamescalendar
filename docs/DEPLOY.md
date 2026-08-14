# Deploy Runbook — Single VPS with Docker Compose

> Deployment target per **ADR-0003**: one always-on small VPS (e.g. OVH) running the whole
> system as a Docker Compose stack. No managed autoscaling; the single box pays for idle,
> which is the right trade-off at this scale. There is **no Azure deployment** — the obsolete
> Azure workflow was removed.
>
> This runbook matches the current `docker-compose.yml` (one app image, five roles:
> `migrate`, `app`, `worker`, `beat` — plus `postgres`, `redis`, `frontend`).

## Architecture being deployed

| Compose service | Role | Talks on |
|-----------------|------|----------|
| `postgres`      | PostgreSQL 17 | 5432 (internal) |
| `redis`         | Redis 7 (cache + Celery broker/backend) | 6379 (internal) |
| `migrate`       | runs `alembic upgrade head`, exits 0 | – (one-shot) |
| `app`           | FastAPI — public + admin routes | **8000** |
| `worker`        | Celery worker — consumes IGDB sync tasks | – |
| `beat`          | Celery beat — hourly delta / daily 2am / weekly cleanup | – |
| `frontend`      | built React app served by nginx | **80 → 3000** (dev), port 80 in prod |

`app`/`worker`/`beat` start only **after** `migrate` completes successfully
(`service_completed_successfully`), so a fresh database is migrated automatically.

## 1. Prerequisites

- A VPS (1–2 vCPU, 2–4 GB RAM is plenty): any recent Ubuntu/Debian.
- SSH access (as root or a sudo user).
- Docker Engine **with the compose plugin** (`docker compose`, not the legacy `docker-compose`).
- A domain (recommended) and a way to issue TLS (Caddy makes this automatic).

## 2. Install Docker on the VPS

```bash
# Official convenience script (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# re-login, then confirm
docker --version && docker compose version
```

## 3. Clone the repo and configure environment

```bash
sudo mkdir -p /opt/videogamescalendar && sudo chown "$USER":"$USER" /opt/videogamescalendar
git clone https://github.com/happySpartan/videogamescalendar.git /opt/videogamescalendar/app
cd /opt/videogamescalendar/app

cp .env.example .env
# EDIT .env — must set:
#   IGDB_CLIENT_ID=...
#   IGDB_CLIENT_SECRET=...
#   ADMIN_TOKEN=<openssl rand -hex 32>
# DATABASE_URL/REDIS_URL in compose are overridden to point at the postgres/redis
# services, so you normally leave those as-is.
```

> See `.env.example` for the full list. The backend defaults are fine for a first boot; the
> three you must set for a running product are the IGDB credentials and the admin token.

## 4. Build and start the stack

```bash
docker compose up -d --build
```

This builds the single app image and the frontend image, applies migrations via `migrate`,
then starts `app`, `worker`, and `beat`.

## 5. Verify

```bash
docker compose ps                 # all services Up/healthy
curl -fsS http://localhost:8000/health   # {"status":"healthy", database:"connected", redis:"connected"...}
curl -fsS 'http://localhost:8000/releases?from=2030-01-01&to=2030-01-31&limit=10'
docker compose logs -f app worker beat   # watch sync + scheduler activity
```

Trigger a manual sync (the worker consumes it): the admin API is token-gated

```bash
curl -fsS -X POST http://localhost:8000/admin/sync/games \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"full_sync": true}'
# then confirm rows grow
docker compose exec postgres psql -U gameuser -d gamecalendar -c "select count(*) from games;"
```

## 6. Put it behind TLS with a reverse proxy (recommended)

The API listens on `:8000` and the frontend on `:80`. For a real deployment:

- **Option A — Caddy (easiest, automatic Let's Encrypt):**

  ```caddyfile
  # /etc/caddy/Caddyfile
  calendar.example.com {
      # frontend
      handle {
          reverse_proxy localhost:80
      }
  }
  api.calendar.example.com {
      # API (public + admin)
      reverse_proxy localhost:8000
  }
  ```

- **Option B — nginx:** proxy `api.<domain>` → `localhost:8000` and `<domain>` → `localhost:80`,
  with a certbot TLS block.

### Production-readiness gaps to close while you're here

1. **Frontend → API URL.** The frontend image bakes `VITE_GAME_API_URL` into the JS bundle at
   `npm run build` time. It is now a **build arg** (`frontend/Dockerfile`), wired through
   `docker-compose.yml` as `VITE_GAME_API_URL: ${VITE_GAME_API_URL:-http://localhost:8000}`.
   On the VPS the browser, not the server, calls the API — set `VITE_GAME_API_URL` in `.env` to
   the real public API URL (e.g. `https://api.calendar.example.com`) **before** `docker compose
   up -d --build`. Setting it at runtime (the old `environment:` block) had zero effect because
   Vite reads it during the build.
2. **CORS.** The API reads its allowed origins from the `CORS_ORIGINS` env var
   (`app/main.py` → `app/config.py`), defaulting to `*`. Before exposing the API publicly, set
   it in `.env` to your real frontend origin(s), e.g. `CORS_ORIGINS=https://calendar.example.com`
   (comma-separated for multiple). `docker-compose.yml` forwards `${CORS_ORIGINS:-*}` to the app
   service.
3. **Admin token.** The `/admin/*` routes are gated by `ADMIN_TOKEN` (env). Do **not** expose
   `/admin` through the proxy unless you add auth in front; keep it on the private interface if
   possible.
4. **Persistent data.** Both `postgres_data` and `redis_data` volumes persist via compose;
   don't `docker compose down -v` unless you intend to wipe them.

## 7. Backups

With the stack running (and preferably the app briefly stopped for a clean dump):

```bash
docker compose exec postgres pg_dump -U gameuser -d gamecalendar -Fc -f /tmp/app.dump
docker compose cp postgres:/tmp/app.dump ./backups/$(date +%F).dump
```

Store backups off-box (rsync to another host, or object storage). Redis is a cache/broker —
its data is re-derivable from IGDB, so a Redis backup is optional.

## 8. Updates (rolling deploy)

```bash
cd /opt/videogamescalendar/app
git pull
docker compose up -d --build
# migrations apply automatically via the migrate service before app/worker/beat restart
# verify:
curl -fsS http://localhost:8000/health
```

## 9. Troubleshooting

| Symptom | Likely cause / check |
|---------|----------------------|
| `/health` shows `database: disconnected` | Postgres not up/healty: `docker compose ps`, `docker compose logs postgres` |
| Empty tables | migration didn't run: `docker compose logs migrate`; run `docker compose run --rm migrate` |
| No news games after sync | IGDB creds missing or invalid; check `docker compose logs worker`; test the OAuth token manually |
| `migrate` never completes | `docker compose logs migrate` for the Alembic error (e.g. missing `pg_trgm` — the initial migration creates it) |
| Frontend calls `localhost` | `VITE_GAME_API_URL` baked at build time — rebuild after setting the public URL (see §6.1) |

## 10. Teardown (if ever needed)

```bash
docker compose down          # keep volumes
docker compose down -v       # WIPE postgres_data + redis_data
```
