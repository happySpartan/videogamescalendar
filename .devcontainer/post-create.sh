#!/bin/bash

# Post-create script for setting up the development environment
set -e

echo "🚀 Setting up Video Games Calendar development environment..."

# Additional stack tooling (Postgres/Redis clients, jq) + uv package manager
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends postgresql-client redis-tools jq > /dev/null
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python dependencies (single consolidated app package)
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

# Install Python dev tools
echo "🔧 Installing Python development tools..."
pip install ruff mypy bandit

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
cd /workspaces/videogamescalendar/frontend
npm install
cd /workspaces/videogamescalendar

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -U gameuser -d gamecalendar > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
until redis-cli -h redis ping > /dev/null 2>&1; do
  echo "Waiting for Redis..."
  sleep 2
done

echo "✅ Redis is ready!"

# Create .env file if it doesn't exist
if [ ! -f /workspaces/videogamescalendar/.env ]; then
  echo "📝 Creating .env file..."
  cat > /workspaces/videogamescalendar/.env << EOF
# Database
DATABASE_URL=postgresql://gameuser:gamepass@postgres:5432/gamecalendar

# Redis
REDIS_URL=redis://redis:6379/0

# IGDB API Credentials (Add your own)
IGDB_CLIENT_ID=your_client_id_here
IGDB_CLIENT_SECRET=your_client_secret_here

# Admin Token (Change this!)
ADMIN_TOKEN=change_me_in_production

# Environment
NODE_ENV=development
PYTHON_ENV=development
EOF
  echo "⚠️  Please update .env file with your IGDB API credentials"
fi

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Quick Start Commands:"
echo "  - Start frontend dev server:  cd frontend && npm run dev"
echo "  - Start backend API:          uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Start Celery worker:        celery -A app.sync.celery_app worker --loglevel=info"
echo "  - Start Celery beat:          celery -A app.sync.celery_app beat --loglevel=info"
echo "  - Run all services:           docker-compose up"
echo ""
echo "🎉 Happy coding!"
