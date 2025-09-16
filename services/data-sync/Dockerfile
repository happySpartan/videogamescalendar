# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/data-sync/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared dependencies
COPY shared/ ./shared/

# Copy application code
COPY services/data-sync/ .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check for worker
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD celery -A worker inspect ping || exit 1

# Default command runs worker
CMD ["celery", "-A", "worker", "worker", "--loglevel=info"]