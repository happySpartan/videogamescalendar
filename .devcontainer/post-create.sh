#!/bin/bash
set -e

echo ""
echo "🚀 Setting up Video Game Calendar development environment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Install Python dependencies for each service
print_step "Installing Python dependencies..."

cd /workspace/services/game-api
pip install -r requirements.txt
print_success "Game API dependencies installed"

cd /workspace/services/admin-api
pip install -r requirements.txt
print_success "Admin API dependencies installed"

cd /workspace/services/data-sync
pip install -r requirements.txt
print_success "Data Sync dependencies installed"

# Install frontend dependencies
print_step "Installing frontend dependencies..."
cd /workspace/frontend
npm install
print_success "Frontend dependencies installed"

# Wait for PostgreSQL to be ready
print_step "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
until pg_isready -h postgres -p 5432 -U gameuser > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_warning "PostgreSQL did not become ready in time. You may need to restart the database service."
else
    print_success "PostgreSQL is ready"
fi

# Wait for Redis to be ready
print_step "Waiting for Redis to be ready..."
max_attempts=30
attempt=0
until redis-cli -h localhost -p 6379 ping > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "Waiting for Redis... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_warning "Redis did not become ready in time. You may need to restart the Redis service."
else
    print_success "Redis is ready"
fi

# Copy environment file if it doesn't exist
if [ ! -f /workspace/.env ]; then
    print_step "Creating .env file..."
    cat > /workspace/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://gameuser:gamepass@postgres:5432/gamecalendar

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# IGDB API Configuration (⚠️ ADD YOUR CREDENTIALS)
IGDB_CLIENT_ID=your_client_id_here
IGDB_CLIENT_SECRET=your_client_secret_here

# Admin Configuration
ADMIN_TOKEN=your_secure_admin_token_here

# Development Settings
PYTHONPATH=/workspace
NODE_ENV=development
EOF
    print_warning ".env file created - REMEMBER TO ADD YOUR IGDB CREDENTIALS!"
else
    print_success ".env file already exists"
fi

# Return to workspace root
cd /workspace

echo ""
echo "================================================================"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "================================================================"
echo ""
echo -e "${BLUE}📋 Quick Start Commands:${NC}"
echo ""
echo "  1️⃣  Start infrastructure (already running in background):"
echo "     Already started: PostgreSQL on port 5432, Redis on port 6379"
echo ""
echo "  2️⃣  Start backend services (open 3 terminals):"
echo "     Terminal 1: cd services/game-api && uvicorn main:app --reload --port 8000"
echo "     Terminal 2: cd services/admin-api && uvicorn main:app --reload --port 8001"
echo "     Terminal 3: cd services/data-sync && celery -A worker worker --loglevel=info --pool=solo"
echo ""
echo "  3️⃣  Start frontend:"
echo "     Terminal 4: cd frontend && npm run dev"
echo ""
echo "  Or use VS Code tasks: Ctrl+Shift+P → 'Tasks: Run Task'"
echo ""
echo -e "${BLUE}🔗 Service URLs:${NC}"
echo "  Frontend:      http://localhost:3000"
echo "  Game API:      http://localhost:8000/docs"
echo "  Admin API:     http://localhost:8001/docs"
echo "  PostgreSQL:    localhost:5432"
echo "  Redis:         localhost:6379"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to:${NC}"
echo "  1. Add your IGDB credentials to .env"
echo "  2. Add your admin token to .env"
echo ""
echo "Happy coding! 🎮🚀"
echo ""
