"""Настройка окружения для тестов."""

from types import AsyncGeneratorType

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from src.app import app


@pytest.fixture(scope="session")
async def http_client() -> AsyncGeneratorType[AsyncClient]:
    """Предоставляет асинхронный http клиент c ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Применяет миграции Alembic один раз за сессию, до всех тестов."""
    # Путь к alembic.ini
    alembic_cfg = Config("alembic.ini")
    # Применение миграций
    command.upgrade(alembic_cfg, "head")
