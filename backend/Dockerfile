# ==========================================
# STAGE 1: Base (Dependencias del sistema y uv)
# ==========================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app/

# Dependencias necesarias para OpenCV y Ultralytics (YOLO)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# ==========================================
# STAGE 2: Builder (Construye el entorno virtual)
# ==========================================
FROM base AS builder

ARG DEVICE_TYPE=cpu

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_COMPILE_BYTECODE=1 \
    uv sync --frozen --no-dev --no-install-project --extra ${DEVICE_TYPE}

# ==========================================
# STAGE 3: Local environment
# ==========================================
FROM builder AS local

ARG DEVICE_TYPE=cpu

ENV ENV=local

# En local sí instalamos el grupo [dev] (pytest, httpx, etc.)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --extra ${DEVICE_TYPE}

COPY . .

CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000", "src/server/main.py"]

# ==========================================
# STAGE 4: Production environment
# ==========================================
FROM base AS production

ENV ENV=production

RUN groupadd -g 10001 appuser && \
    useradd -u 10000 -g appuser -m -s /sbin/nologin appuser


COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

USER appuser

CMD ["fastapi", "run", "--workers", "4", "--host", "0.0.0.0", "--port", "8000", "src/server/main.py"]