# Video Game Calendar

A modern web application for browsing upcoming video game releases with a scalable microservices architecture.

## Features

- **Upcoming Game Releases**: Browse games by time periods (current month, year, etc.)
- **Advanced Search & Filtering**: Search by name, filter by platforms, genres, and languages
- **Calendar View**: Visualize releases by date
- **Admin Dashboard**: System monitoring and data management
- **IGDB Integration**: Automatic synchronization with IGDB API
- **Modern Architecture**: Microservices with FastAPI, PostgreSQL, and Redis

## Quick Start

### Docker (Recommended)
```bash
# Clone and setup
git clone <repository-url>
cd videogamecalendar
cp .env.example .env
# Edit .env with your IGDB API credentials

# Start all services
docker-compose up --build -d

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Manual Setup
```bash
# Infrastructure
docker-compose up postgres redis -d

# Database setup
pip install -r scripts/requirements.txt
python scripts/setup_migrations.py init
python scripts/setup_migrations.py migrate

# Services (in separate terminals)
cd services/game-api && uvicorn main:app --reload --port 8000
cd services/admin-api && uvicorn main:app --reload --port 8001
cd services/data-sync && celery -A worker worker --loglevel=info

# Frontend
cd frontend && npm install && npm run dev
```

## Documentation

📖 **[Complete Documentation](./DOCUMENTATION.md)** - Comprehensive setup, architecture, and deployment guide

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Mantine UI
- **Backend**: FastAPI, Celery, SQLAlchemy
- **Database**: PostgreSQL with JSONB optimization
- **Cache**: Redis
- **Infrastructure**: Docker Compose

## Project Structure

```
videogamecalendar/
├── services/          # Microservices (Game API, Admin API, Data Sync)
├── frontend/          # React application
├── shared/           # Common models and utilities
├── infrastructure/   # Docker configurations
└── DOCUMENTATION.md  # Complete documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For detailed contribution guidelines, see [DOCUMENTATION.md](./DOCUMENTATION.md).

## License

This project is open source. Feel free to submit issues or pull requests!
