# Use Python 3.13 as base image to match local development environment
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SSL_CERT_DIR=/app/ssl \
    SSL_CERT_FILE=/app/ssl/Root.pem \
    REQUESTS_CA_BUNDLE=/app/ssl/Root.pem

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev python3-dev openssl curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/ssl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directory for SQLite database and logs (if they don't exist)
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f https://localhost:5050/ --insecure || exit 1

# Make scripts executable
RUN chmod +x run.py run_with_ssl.py

# Create startup script for Docker
RUN echo '#!/bin/bash\n\
if [ -f "/app/ssl/Root.pem" ]; then\n\
  echo "Using provided ZScaler certificate"\n\
else\n\
  echo "ZScaler certificate not provided, using default certificates"\n\
  cp $(python -c "import certifi; print(certifi.where())") /app/ssl/Root.pem\n\
fi\n\
echo "Starting with SSL support..."\n\
python run_with_ssl.py' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Entry point - use the SSL-enabled script via entrypoint script
CMD ["/app/docker-entrypoint.sh"]
