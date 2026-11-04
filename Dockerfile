# =============================================================================
# AQUILA - Academic Demonstration Dockerfile (Optional Container Deployment)
# Multi-stage lightweight Python 3.13 image
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Set non-interactive debian frontend and python environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AQUILA_ENV=production \
    AQUILA_HOST=0.0.0.0 \
    AQUILA_PORT=8000

# Install system dependencies for geospatial libraries (GDAL, GEOS, PROJ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements-lock.txt .

# Install pinned Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-lock.txt

# Copy application code, datasets, and scripts
COPY app/ app/
COPY config/ config/
COPY data/ data/
COPY scripts/ scripts/
COPY .env.example .env

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000 8501

# Default command: launch FastAPI server
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

