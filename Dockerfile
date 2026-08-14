# Single-app image for the consolidated Video Game Calendar backend.
#
# One image serves all three roles (web API, Celery worker, Celery beat) via a
# CMD override in docker-compose.yml. The app package (app/) is installed from
# the root pyproject.toml, so there is no more shared/ sys.path hack.
#
#   web:    uvicorn app.main:app --host 0.0.0.0 --port 8000
#   worker: celery -A app.sync.celery_app worker --loglevel=info
#   beat:   celery -A app.sync.celery_app beat --loglevel=info
FROM python:3.14-slim

WORKDIR /app

# System deps: gcc for psycopg2/asyncpg builds, postgresql-client + curl for
# healthchecks.
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install the package first (caches deps independent of app source changes).
COPY pyproject.toml ./
COPY app/ ./app/
# Alembic config + migrations so the image can run `alembic upgrade head`
# (used by the compose `migrate` service and for deploy-time migrations).
COPY alembic.ini ./
COPY alembic/ ./alembic/
RUN pip install --no-cache-dir .

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command runs the web API; override per-service in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
