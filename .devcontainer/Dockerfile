# Development container for Video Games Calendar
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install PostgreSQL client tools
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y postgresql-client redis-tools \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip \
    && pip install black flake8 pytest pytest-cov mypy isort ipython

# Set working directory
WORKDIR /workspaces/videogamescalendar

# Keep container running
CMD ["sleep", "infinity"]
