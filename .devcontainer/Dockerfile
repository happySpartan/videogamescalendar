FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    build-essential \
    git \
    curl \
    wget \
    vim \
    nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python tools
RUN pip install --upgrade pip setuptools wheel

# Install development tools
RUN pip install \
    ruff \
    mypy \
    bandit \
    pre-commit \
    ipython \
    ipdb

# Set up environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create workspace directory
WORKDIR /workspace

# Switch to vscode user (created by base image)
USER vscode
