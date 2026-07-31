FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by Docling (PDF processing + OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libxkbcommon0 \
    libxkbfile1 \
    poppler-utils \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
