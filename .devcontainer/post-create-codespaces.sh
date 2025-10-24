#!/bin/bash

# Post-create script for GitHub Codespaces
# Note: Temporarily disable exit-on-error for Docker checks
set +e

echo "🚀 Setting up Video Games Calendar development environment in Codespaces..."

# Re-enable exit on error for dependency installation
set -e

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip --quiet

# Install all service requirements
if [ -f "services/game-api/requirements.txt" ]; then
    echo "  - Installing game-api dependencies..."
    pip install -r services/game-api/requirements.txt --quiet
fi

if [ -f "services/admin-api/requirements.txt" ]; then
    echo "  - Installing admin-api dependencies..."
    pip install -r services/admin-api/requirements.txt --quiet
fi

if [ -f "services/data-sync/requirements.txt" ]; then
    echo "  - Installing data-sync dependencies..."
    pip install -r services/data-sync/requirements.txt --quiet
fi

if [ -f "scripts/requirements.txt" ]; then
    echo "  - Installing script dependencies..."
    pip install -r scripts/requirements.txt --quiet
fi

# Install Python dev tools
echo "🔧 Installing Python development tools..."
pip install black flake8 pytest pytest-cov mypy isort --quiet

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
fi

# Allow Docker operations to fail gracefully
set +e

# Start docker compose services in the background
echo "🐳 Starting backend services (PostgreSQL, Redis)..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker command not found. Services will need to be started manually."
    echo "   Run: docker compose up -d postgres redis"
else
    # Check if docker compose works
    if docker compose version &> /dev/null; then
        docker compose up -d postgres redis 2>&1 || {
            echo "⚠️  Failed to start services. You may need to start them manually with:"
            echo "   docker compose up -d postgres redis"
        }
        
        # Wait for PostgreSQL to be ready
        echo "⏳ Waiting for PostgreSQL to be ready..."
        timeout=60
        elapsed=0
        until docker compose exec -T postgres pg_isready -U gameuser -d gamecalendar > /dev/null 2>&1; do
          if [ $elapsed -ge $timeout ]; then
            echo "⚠️  PostgreSQL startup timeout. You may need to start it manually with: docker compose up postgres"
            break
          fi
          echo "  Waiting for PostgreSQL... (${elapsed}s)"
          sleep 3
          elapsed=$((elapsed + 3))
        done

        if docker compose exec -T postgres pg_isready -U gameuser -d gamecalendar > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
        fi

        # Wait for Redis to be ready
        echo "⏳ Waiting for Redis to be ready..."
        elapsed=0
        until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
          if [ $elapsed -ge $timeout ]; then
            echo "⚠️  Redis startup timeout. You may need to start it manually with: docker compose up redis"
            break
          fi
          echo "  Waiting for Redis... (${elapsed}s)"
          sleep 2
          elapsed=$((elapsed + 2))
        done

        if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis is ready!"
        fi
    else
        echo "⚠️  Docker Compose not available yet. Services will need to be started manually."
        echo "   Run: docker compose up -d postgres redis"
    fi
fi

# Re-enable exit on error
set -e

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
  echo "📝 Creating .env file from template..."
  if [ -f ".env.example" ]; then
    cp .env.example .env
  else
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://gameuser:gamepass@localhost:5432/gamecalendar

# Redis
REDIS_URL=redis://localhost:6379/0

# IGDB API Credentials (Add your own)
IGDB_CLIENT_ID=your_client_id_here
IGDB_CLIENT_SECRET=your_client_secret_here

# Admin Token (Change this!)
ADMIN_TOKEN=change_me_in_production

# Environment
NODE_ENV=development
PYTHON_ENV=development
EOF
  fi
  echo "⚠️  Please update .env file with your IGDB API credentials"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Quick Start Commands:"
echo "  - Start frontend dev server:  cd frontend && npm run dev"
echo "  - Start Game API:             cd services/game-api && uvicorn main:app --reload --host 0.0.0.0"
echo "  - Start Admin API:            cd services/admin-api && uvicorn main:app --reload --host 0.0.0.0 --port 8001"
echo "  - View running services:      docker compose ps"
echo "  - View service logs:          docker compose logs -f"
echo ""
echo "🎉 Happy coding!"
