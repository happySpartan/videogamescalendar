#!/bin/bash
# ---------------------------------------------------------------------------
# Post-create script for GitHub Codespaces (devcontainer.json -> postCreateCommand)
#
# Single setup entrypoint for this repo. Installs every tool the stack needs,
# brings up Postgres + Redis via docker-compose, and writes a local .env for
# the backend.
#
# IGDB credentials are supplied via GitHub *Codespace secrets*
# (IGDB_CLIENT_ID, IGDB_CLIENT_SECRET). Secrets are injected as environment
# variables at container start, so this script picks them up automatically if
# set and writes them into .env — no manual editing needed.
# ---------------------------------------------------------------------------
set +e   # Docker may not be ready immediately; handle gracefully
echo "🚀 Setting up Video Games Calendar development environment in Codespaces..."

# --- Base tooling that the devcontainer features + apt give us ------------
# The python:3.14-bookworm base image already ships: git, curl, ca-certificates,
# build-essential. Devcontainer features add: Node 20, GitHub CLI (gh),
# Docker-in-Docker. We add the rest of the stack toolchain below.

set -e

echo "🔧 Installing additional stack tooling (uv, jq, Postgres/Redis clients)..."
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  postgresql-client \
  redis-tools \
  jq \
  > /dev/null

# uv — fast Python package/venv manager (preferred over raw pip for this repo).
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Put uv on PATH for this shell; a fresh shell picks it up from ~/.local/bin.
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "  uv: $(uv --version 2>/dev/null || echo 'not found')"

# --- Python dependencies (single consolidated app package) ----------------
echo "📦 Installing Python dependencies (editable + dev extras)..."
pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet
echo "  app + dev extras installed"

# --- Frontend dependencies ------------------------------------------------
echo "📦 Installing frontend dependencies..."
if [ -d "frontend" ]; then
  (cd frontend && npm install)
fi

# --- Bring up Postgres + Redis via docker-compose --------------------------
set +e
echo "🐳 Starting backend services (PostgreSQL, Redis)..."
docker_declined=0
if ! command -v docker &> /dev/null; then
  echo "⚠️  docker not found. Start services manually: docker compose up -d postgres redis"
  docker_declined=1
elif ! docker compose version &> /dev/null; then
  echo "⚠️  docker compose unavailable. Start services manually: docker compose up -d postgres redis"
  docker_declined=1
fi

if [ $docker_declined -eq 0 ]; then
  docker compose up -d postgres redis

  echo "⏳ Waiting for PostgreSQL..."
  for i in $(seq 1 20); do
    docker compose exec -T postgres pg_isready -U gameuser -d gamecalendar > /dev/null 2>&1 && break
    sleep 3
  done
  docker compose exec -T postgres pg_isready -U gameuser -d gamecalendar > /dev/null 2>&1 \
    && echo "✅ PostgreSQL is ready!" || echo "⚠️  PostgreSQL not ready yet."

  echo "⏳ Waiting for Redis..."
  for i in $(seq 1 20); do
    docker compose exec -T redis redis-cli ping > /dev/null 2>&1 && break
    sleep 2
  done
  docker compose exec -T redis redis-cli ping > /dev/null 2>&1 \
    && echo "✅ Redis is ready!" || echo "⚠️  Redis not ready yet."
fi
set -e

# --- Write .env (never overwrite an existing, hand-edited one) -------------
if [ ! -f ".env" ]; then
  echo "📝 Creating .env from template..."
  template=".env.example"
  if [ ! -f "$template" ]; then
    # Minimal inline fallback if .env.example is ever missing.
    cat > .env <<'EOF'
DATABASE_URL=postgresql://gameuser:***@localhost:5432/gamecalendar
REDIS_URL=redis://localhost:6379/0
IGDB_CLIENT_ID=your_client_id_here
IGDB_CLIENT_SECRET=your_client_secret_here
ADMIN_TOKEN=change_me_in_production
CORS_ORIGINS=*
EOF
  else
    cp "$template" .env
  fi

  # Pull secrets from Codespace secret env vars if present, else keep placeholders.
  # NOTE: values containing ':' or '&' could break naive sed; credentials are
  # base64/url-safe so this is acceptable. Use "|" as sed delimiter.
  if [ -n "${IGDB_CLIENT_ID:-}" ]; then
    sed -i "s|^IGDB_CLIENT_ID=.*|IGDB_CLIENT_ID=${IGDB_CLIENT_ID}|" .env
  fi
  if [ -n "${IGDB_CLIENT_SECRET:-}" ]; then
    sed -i "s|^IGDB_CLIENT_SECRET=.*|IGDB_CLIENT_SECRET=${IGDB_CLIENT_SECRET}|" .env
  fi
  if [ -n "${ADMIN_TOKEN:-}" ]; then
    sed -i "s|^ADMIN_TOKEN=.*|ADMIN_TOKEN=${ADMIN_TOKEN}|" .env
  fi

  if [ -n "${IGDB_CLIENT_ID:-}" ] && [ -n "${IGDB_CLIENT_SECRET:-}" ]; then
    echo "✅ IGDB credentials populated from Codespace secrets."
  else
    echo "⚠️  IGDB credentials not set as Codespace secrets. Set IGDB_CLIENT_ID /"
    echo "   IGDB_CLIENT_SECRET as repo/user Codespace secrets, then rebuild,"
    echo "   or edit .env manually."
  fi
else
  echo "ℹ️  .env already exists — leaving it untouched."
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Quick Start Commands:"
echo "  - Start frontend dev server: cd frontend && npm run dev"
echo "  - Start backend API:         uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Start Celery worker:       celery -A app.sync.celery_app worker --loglevel=info"
echo "  - Start Celery beat:         celery -A app.sync.celery_app beat --loglevel=info"
echo "  - All services:              docker compose up -d --build"
echo "  - View services:             docker compose ps / docker compose logs -f"
echo "  - GitHub CLI:                gh (auth: gh auth login)"
echo "  - Run quality gates:         ruff check app tests && mypy app && (cd frontend && tsc --noEmit)"
echo ""
echo "🎉 Happy coding!"