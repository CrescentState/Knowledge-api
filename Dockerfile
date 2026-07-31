FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 libxcb-shm0 libxcb-xfixes0 libgl1 libglib2.0-0 \
    libsm6 libxext6 libgomp1 tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy app code
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
