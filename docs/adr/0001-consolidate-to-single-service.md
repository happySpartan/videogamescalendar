# 1. Consolidate to a single service + package

**Status**: Accepted

**Context**: The repo originally split into three microservices (`game-api`, `admin-api`,
`data-sync`) sharing a `shared/` package that was never a real dependency (wired via
`sys.path.append` hacks, pyproject declared no runtime deps). For a read-mostly, solo-app
scale, that boundary buys little.

**Decision**: For now run ONE app process (public + admin routes) plus the Celery worker with
beat, all from a single Python root package `app` (`app/models`, `app/db`, `app/api`,
`app/admin`, `app/sync`), folding the old `shared/` modules into it. Keep Celery + Redis as the
scheduling engine and TanStack Query + the typed API client on the frontend.

**Why**: Consolidation removes packaging/deployment surface without losing any real
capability, and matches "product, cheap to start, split later". Reversible: modules have clean
boundaries (`api`/`admin`/`sync`) and can be split back into separate processes if scale demands.