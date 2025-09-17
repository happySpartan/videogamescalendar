# Video Game Calendar Backend (Legacy)

> **Note**: This is the legacy Flask backend. The new microservices architecture is recommended for new deployments. See [DOCUMENTATION.md](../DOCUMENTATION.md) for the modern setup.

Flask-based backend that provides RESTful API endpoints for game data.

## Features

- RESTful API endpoints
- IGDB API integration
- SQLite database
- SSL support for corporate environments

## Quick Setup

```bash
cd backend
pip install -r requirements.txt

# Configure .env file
cp .env.example .env
# Add your IGDB API credentials

python run.py
```

## SSL Support

For corporate environments requiring SSL:

```bash
# Windows
.\run_backend.ps1

# Linux/Mac
./run_backend_ssl.sh
```

## Project Structure

### Root Files:

- `app.py`: Flask application entry point that defines all API endpoints.
- `database.py`: Re-exports database models and utilities for backward compatibility.
- `config.py`: Manages configuration settings and environment variables.
- `debug.py`: Special script for running the app in debug mode.
- `run.py`: Main script to initialize backend and start Flask server.
- `requirements.txt`: Lists all Python dependencies.
- `gamecalendar.db`: SQLite database file (generated at runtime).

### Directories and Their Purpose:

#### `/models/`

Contains SQLAlchemy ORM model definitions that represent database tables:

- `__init__.py`: Imports and re-exports all models for easy access.
- `base.py`: Base classes for models, including timestamp functionality.
- `game.py`: Game model with relationships to other entities.
- `genre.py`: Game genre model.
- `platform.py`: Gaming platform model (PC, consoles, etc.).
- `language.py`: Supported language model.
- `region.py`: Geographic region model.
- `company.py`: Game developer/publisher company model.
- `franchise.py`: Game franchise/series model.

#### `/services/`

Contains service classes that handle business logic:

- `igdb_service.py`: Core service for interacting with IGDB API, fetches game data.
- `cache_service.py`: Handles data caching to reduce API calls.
- `db_manager.py`: Manages database connections and sessions.
- `startup_loader.py`: Handles initial data loading when the app starts.

#### `/utils/`

Contains utility functions and helpers:

- `db_utils.py`: Database setup utilities (engine, session factory, etc.).
- `route_helpers.py`: Flask route decorators and API helpers.
- `__init__.py`: Package initialization.

#### `/scripts/`

Contains maintenance and utility scripts:

- `initialize_schema.py`: Creates or recreates the database schema.
- `fix_database.py`: Script for database maintenance and repairs.
- `drop_association_tables.py`: Helper script for schema management.

#### `/logs/`

Contains application logs (generated at runtime).

## Configuration

The application uses environment variables for configuration (via `.env` file):

- `TWITCH_CLIENT_ID`: Your IGDB/Twitch API client ID
- `TWITCH_CLIENT_SECRET`: Your IGDB/Twitch API client secret
- `CACHE_REFRESH_HOURS`: How often to refresh data (default: 168 hours/1 week)
- `GAMES_REFRESH_HOURS`: How often to refresh game data (default: 168 hours/1 week)

## Data Flow

1. User requests data via API endpoint in `app.py`
2. App checks for cached data in database
3. If data is stale or missing:
   a. `igdb_service.py` fetches fresh data from IGDB API in batches of 300
   b. Data is processed and stored in database models
4. Response is formatted and returned to client

## API Endpoints

The application exposes various endpoints for game data:

- `/api/games`: Main endpoint with filtering options
- `/api/genres`, `/api/platforms`, etc.: Reference data endpoints
- `/api/refresh-data`: Admin endpoint to force data refresh

For complete API documentation, see the [API Endpoints](#api-endpoints) section below.

## Getting Started

### Prerequisites

- Python 3.10+
- Dependencies listed in `requirements.txt`
- IGDB API credentials (Client ID and Secret)

### Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory with your IGDB credentials:

```env
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
```

### Running the Backend

To start the backend, simply run:

```bash
python run.py
```

This will:

- Initialize the database schema (`gamecalendar.db` SQLite file).
- Fetch and cache essential data (platforms, genres, languages, regions, and games).

For development/debugging, use:

```bash
python debug.py
```

### Database Schema

The database schema includes the following main tables:

- `games`: Stores game details (name, release date, genre, language, etc.).
- `genres`: Game genres from IGDB.
- `platforms`: Gaming platforms from IGDB.
- `languages`: Supported languages from IGDB.
- `regions`: Game regions from IGDB.
- `companies`: Game developers/publishers from IGDB.
- `franchises`: Game franchises from IGDB.

## API Endpoints

### Game Endpoints

| Endpoint                     | Method | Description                                       | Parameters                                          |
| ---------------------------- | ------ | ------------------------------------------------- | --------------------------------------------------- |
| `/api/games/current-month` | GET    | Returns games being released in the current month | None                                                |
| `/api/games/2025`          | GET    | Returns games expected to be released in 2025     | None                                                |
| `/api/cached-games`        | GET    | Returns games that have been cached               | `year` (optional): Filter by year (default: 2025) |
| `/api/game/<game_id>`      | GET    | Returns detailed information for a specific game  | `game_id`: ID of the game to fetch                |
| `/api/games/search`        | GET    | Search for games by name                          | `q`: Search query (min 2 chars)                   |

### Reference Data Endpoints

| Endpoint            | Method | Description                            | Parameters |
| ------------------- | ------ | -------------------------------------- | ---------- |
| `/api/genres`     | GET    | Returns all game genres                | None       |
| `/api/platforms`  | GET    | Returns all gaming platforms           | None       |
| `/api/languages`  | GET    | Returns all supported languages        | None       |
| `/api/regions`    | GET    | Returns all game regions               | None       |
| `/api/companies`  | GET    | Returns all game developers/publishers | None       |
| `/api/franchises` | GET    | Returns all game franchises            | None       |

### Admin Endpoints

| Endpoint                  | Method | Description                             | Parameters                                                                                                                             |
| ------------------------- | ------ | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `/api/refresh-data`     | POST   | Refresh data from IGDB API              | `all`: Refresh all data including games `<br>games`: Refresh only games `<br>`Requires `X-Admin-Key` header for admin features |
| `/api/system/db-status` | GET    | Returns database connection pool status | Requires `X-Admin-Key` header                                                                                                        |

### System Endpoints

| Endpoint | Method | Description           | Parameters |
| -------- | ------ | --------------------- | ---------- |
| `/`    | GET    | Health check endpoint | None       |

## Response Examples

### Genre Response

```json
[
  {
    "id": 1,
    "name": "Point-and-click",
    "slug": "point-and-click",
    "url": "https://www.igdb.com/genres/point-and-click",
    "created_at": 1297555200,
    "updated_at": 1323216000
  }
]
```

### Platform Response

```json
[
  {
    "id": 6,
    "name": "PC (Microsoft Windows)",
    "abbreviation": "PC",
    "alternative_name": "Personal Computer",
    "category": 4,
    "generation": null,
    "slug": "win",
    "summary": "Microsoft Windows is a series of graphical interface operating systems developed, marketed, and sold by Microsoft.",
    "url": "https://www.igdb.com/platforms/win"
  }
]
```

### Game Response

```json
{
  "id": 119133,
  "name": "Elden Ring",
  "slug": "elden-ring",
  "summary": "Elden Ring is an action-RPG open world game with RPG elements such as stats, weapons and spells.",
  "storyline": "In the Lands Between ruled by Queen Marika the Eternal, the Elden Ring, the source of the Erdtree, has been shattered...",
  "release_date": "2022-02-25T00:00:00.000Z",
  "rating": 94.3,
  "rating_count": 1234,
  "cover_url": "//images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg",
  "developer": {
    "id": 962,
    "name": "FromSoftware"
  },
  "franchise": {
    "id": 119,
    "name": "Souls"
  },
  "genre": {
    "id": 12,
    "name": "Role-playing (RPG)"
  },
  "video_id": "E3Huy2cdih0"
}
```

## Error Handling

All API endpoints will return an error response in the following format when an error occurs:

```json
{
  "error": "Error message details"
}
```

Error responses will have appropriate HTTP status codes:

- 400: Bad request (e.g., missing or invalid parameters)
- 404: Resource not found
- 500: Server error

## Logging

Logging is configured in `log_config.py`. To enable debug logging, set the environment variable:

```env
DEBUG=true
```

## Database Maintenance

Several scripts are available in the `scripts` directory for database maintenance:

- `initialize_schema.py`: Completely reinitialize the database schema
- `fix_database.py`: Check and fix database schema issues
- `drop_association_tables.py`: Remove association tables if needed

## Contributing

- Keep code concise and well-documented.
- Use the modular structure with models in the `models` directory.
- Avoid redundant logging, especially in loops.
- Clearly document new features and endpoints.

Happy coding!
