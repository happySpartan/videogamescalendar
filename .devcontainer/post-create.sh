#!/bin/bash

# Post-create script for setting up the development environment
set -e

echo "🚀 Setting up Video Games Calendar development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r services/game-api/requirements.txt
pip install -r services/admin-api/requirements.txt
pip install -r services/data-sync/requirements.txt
pip install -r scripts/requirements.txt

# Install Python dev tools
echo "🔧 Installing Python development tools..."
pip install black flake8 pytest pytest-cov mypy isort

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
echo "  - Start Game API:             cd services/game-api && uvicorn main:app --reload --host 0.0.0.0"
echo "  - Start Admin API:            cd services/admin-api && uvicorn main:app --reload --host 0.0.0.0 --port 8001"
echo "  - Run all services:           docker-compose up"
echo ""
echo "🎉 Happy coding!"
