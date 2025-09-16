# Migration Scripts

This directory contains scripts for database migration and schema management.

## Scripts

### `migrate_sqlite_to_postgresql.py`
Migrates existing SQLite data to the new PostgreSQL microservices architecture.

**Features:**
- Migrates all reference data (genres, platforms, companies)
- Migrates games with relationships
- Preserves original SQLite IDs in metadata
- Comprehensive error handling and logging
- Migration statistics and reporting

**Usage:**
```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Run migration
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db

# Dry run (show what would be migrated)
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db --dry-run
```

### `setup_migrations.py`
Sets up and manages Alembic database migrations for PostgreSQL schema management.

**Features:**
- Initializes Alembic configuration
- Creates initial migration from models
- Manages schema migrations
- Migration history tracking

**Usage:**
```bash
# Initialize Alembic (one-time setup)
python scripts/setup_migrations.py init

# Create initial migration
python scripts/setup_migrations.py create-initial

# Run all pending migrations
python scripts/setup_migrations.py migrate

# Create new migration
python scripts/setup_migrations.py create --message "Add user ratings table"

# Show migration history
python scripts/setup_migrations.py history
```

## Migration Process

The recommended migration process from the existing SQLite system to the new PostgreSQL microservices architecture:

### 1. Environment Setup
```bash
# Set environment variables
export DATABASE_URL="postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar"
export REDIS_URL="redis://localhost:6379"

# Install dependencies
pip install -r scripts/requirements.txt
```

### 2. Database Schema Setup
```bash
# Initialize Alembic
python scripts/setup_migrations.py init

# Create initial migration
python scripts/setup_migrations.py create-initial

# Apply migrations to create schema
python scripts/setup_migrations.py migrate
```

### 3. Data Migration
```bash
# Migrate data from SQLite
python scripts/migrate_sqlite_to_postgresql.py backend/gamecalendar.db
```

### 4. Verification
After migration, verify the data:
- Check game counts: `SELECT COUNT(*) FROM games;`
- Check relationships: `SELECT COUNT(*) FROM game_genres;`
- Verify data integrity: Run sample queries

## Error Handling

Both scripts include comprehensive error handling:
- **Database connection errors**: Clear error messages for connection issues
- **Data integrity errors**: Rollback on constraint violations
- **Migration conflicts**: Duplicate detection and resolution
- **Logging**: Detailed logs for debugging and monitoring

## Data Mapping

### SQLite → PostgreSQL Field Mapping

**Games Table:**
- `id` → `id` (new auto-increment)
- `igdb_id` → `igdb_id` (preserved)
- `name` → `name`
- `summary` → `summary`
- `first_release_date` → `first_release_date` (converted to timestamp)
- `rating` → `rating`
- JSON fields → `metadata` (JSONB)
- Original SQLite ID stored in `metadata.sqlite_id`

**Reference Tables (Genres, Platforms, Companies):**
- Similar mapping with preserved IGDB IDs
- Enhanced with new PostgreSQL-optimized fields
- Original relationships reconstructed

### Relationship Mapping
- `game_genres` → Many-to-many through SQLAlchemy
- `game_platforms` → Many-to-many through SQLAlchemy  
- `game_companies` → Many-to-many through SQLAlchemy

## Performance Considerations

- **Batch Processing**: Games are processed in batches for memory efficiency
- **Transaction Management**: Proper rollback on errors
- **Index Creation**: PostgreSQL indexes created during schema migration
- **Connection Pooling**: Efficient database connection usage

## Rollback Strategy

If migration issues occur:

1. **Database Rollback**: Drop and recreate the PostgreSQL database
2. **Schema Rollback**: Use Alembic to downgrade migrations
3. **Data Recovery**: Re-run migration scripts with fixes

## Monitoring

Both scripts provide detailed logging:
- **INFO**: Progress updates and successful operations
- **WARNING**: Non-critical issues (e.g., missing optional data)
- **ERROR**: Critical failures requiring attention

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify DATABASE_URL and PostgreSQL service
2. **Permission Errors**: Ensure PostgreSQL user has necessary privileges
3. **Data Conflicts**: Check for duplicate IGDB IDs or names
4. **Memory Issues**: Reduce batch sizes for large datasets

### Debug Mode
Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```