# config/local/Dockerfile
# Multi-stage build (LOCAL) con toolchain para deps que compilan (ej: scikit-surprise)

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Toolchain + headers (necesario para paquetes con C/C++ extensions)
# scikit-surprise en particular necesita gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copiamos lo mínimo para aprovechar cache
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Instala deps del proyecto en /app/dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --target /app/dependencies .

# Copiamos el resto (alembic.ini, config/, etc)
COPY . ./

# ------------------------------------------------------------

FROM python:3.12-slim-bookworm AS final

ARG APP_UID=10001
ARG APP_GID=10001

# Runtime libs (postgres) + (opcional) CA certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g ${APP_GID} appgroup && \
    useradd -u ${APP_UID} -g ${APP_GID} -s /usr/sbin/nologin -M appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/dependencies:/app/src" \
    PATH="/app/dependencies/bin:$PATH"

COPY --from=builder --chown=${APP_UID}:${APP_GID} /app/ ./

USER appuser

EXPOSE 8888

# Si tu compose pasa UVICORN_PORT, este CMD fijo en 8888 igual funciona
# pero mejor es que tu compose overridee el command (como ya lo tenés).
CMD ["uvicorn", "app.run:make_app", "--host", "0.0.0.0", "--port", "8888", "--loop", "uvloop"]
