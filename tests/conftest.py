"""Настройка окружения для тестов."""

from types import AsyncGeneratorType

import pytest
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
