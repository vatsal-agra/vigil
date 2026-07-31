# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1001 vigil && chown -R vigil:vigil /app
USER vigil

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=4s --start-period=25s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# --- development: hot reload on save -------------------------------------
FROM base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- production: multiple workers, no reloader ---------------------------
FROM base AS prod
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# --- worker: probe loop, no HTTP server ----------------------------------
FROM base AS worker
HEALTHCHECK NONE
CMD ["python", "worker.py"]
