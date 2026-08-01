# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

WORKDIR /app

# Cache bust — change this value to force a clean rebuild
ENV DOCKER_BUILD_CACHEBUST=2026-08-01-v1

# Install system libraries Docling + PyTorch + OpenCV require
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libxcb-shm0 \
    libxcb-xfixes0 \
    libxcb-render0 \
    libxcb-shape0 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libgomp1 \
    libfontconfig1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create logs directory for Loguru
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Railway injects PORT at runtime; default to 8080
ENV PORT=8080
EXPOSE 8080

# Shell form so $PORT is expanded at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}