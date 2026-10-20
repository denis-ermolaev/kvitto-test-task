"""Настройка окружения для тестов."""

import asyncio
from collections.abc import AsyncGenerator
from types import AsyncGeneratorType

import pytest
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app

load_dotenv()


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
async def apply_migrations() -> None:
    """Применяет миграции Alembic один раз за сессию, до всех тестов."""
    # Путь к alembic.ini
    alembic_cfg = Config("alembic.ini")
    # Применение миграций
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
async def app_lifespan(apply_migrations: None) -> AsyncGenerator[None]:
    """Запускает lifespan приложения для доступа к, например, сессии БД."""
    apply_migrations  # Зависимость от миграций, чтобы они проходили раньше # noqa: B018
    async with LifespanManager(app):
        yield


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Сессия от фабрики приложения (она уже использует тестовую БД, если запущена в отдельном докер контейнере)."""
    pg_async_session: async_sessionmaker[AsyncSession] = app.state.pg_async_session
    async with pg_async_session() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_database(db_session: AsyncSession) -> AsyncGenerator[None]:
    """Чистит БД после каждого теста."""
    yield
    # Не трогаем таблицу с тарифами, так как они заполняются только один раз в lifespan
    await db_session.execute(text("TRUNCATE payments RESTART IDENTITY CASCADE"))
    await db_session.commit()
