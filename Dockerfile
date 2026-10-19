# base ----
FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Установка uv
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/
# Файлы с зависимостями
COPY pyproject.toml uv.lock ./
# Переменные окружения исключительно для сборки контейнера
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY


# 1. deps-dev ----
FROM base AS deps-dev

# Настройки для uv
ENV UV_PYTHON=3.14 UV_LINK_MODE=symlink UV_PROJECT_ENVIRONMENT=/opt/venv PYTHONPATH=/app
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV PATH="/opt/venv/bin:$PATH"
# Установка зависимостей и dev-зависимостей
RUN uv sync --no-install-project
ENV UV_COMPILE_BYTECODE=0
EXPOSE 8000

# 1.1. dev ----
FROM deps-dev AS dev
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 1.2. test ----
FROM deps-dev AS test
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
