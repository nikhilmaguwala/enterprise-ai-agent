# FastAPI modular monolith
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/apps/api:/app/packages/agent/src:/app/packages/domain/src:/app/packages/integrations/src:/app/packages/knowledge/src:/app/packages/observability/src

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Workspace packages (editable layout)
COPY packages/ /app/packages/
COPY apps/api/pyproject.toml apps/api/README.md* /app/apps/api/
COPY apps/api/app /app/apps/api/app
COPY apps/api/alembic /app/apps/api/alembic
COPY apps/api/alembic.ini* /app/apps/api/

WORKDIR /app/apps/api
RUN pip install --upgrade pip \
    && if [ -f pyproject.toml ]; then pip install -e ".[dev]" || pip install -e .; fi \
    && pip install "fastapi[standard]" uvicorn alembic

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
