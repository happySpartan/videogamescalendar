# 3. Production deploy on a single small VPS with Docker Compose

**Status**: Accepted

**Context**: Earlier framing assumed Azure Container Apps (API scale-to-zero, always-on worker &
beat, managed autoscaling). The chosen environment is a small VPS (e.g. OVH) with Docker
installed and containers running on it.

**Decision**: Run the whole system as Docker Compose services on one always-on VPS — web app
(public + admin routes), Celery worker, Celery beat, Postgres, Redis. No managed autoscaling;
the API pays for idle alongside the always-on worker/beat. Mirror in the existing
`docker-compose.yml` shape (single host, one compose unit), consolidating the app services.

**Why**: Simplest possible ops and cheap, matching a solo product and the existing compose file.
Trade-off accepted: no horizontal scaling and paying for an idle box; that's the right bet at
this scale and split later (separate DB / managed containers) stays open.