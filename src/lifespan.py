"""Определение lifespan для FastAPI приложения."""

from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import DB_URL, fill_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Асинхронный контекстный менеджер для открытия и закрытия базы данных для FastAPI приложения."""
    # __enter___
    # Подключение к PostgreSQL ----
    pg_engine = create_async_engine(DB_URL)
    pg_async_session = async_sessionmaker(pg_engine, expire_on_commit=False)
    app.state.pg_engine = pg_engine
    app.state.pg_async_session = pg_async_session
    # Заполнение БД ----
    await fill_db(pg_async_session)
    try:
        yield
    finally:
        # __exit__
        await pg_engine.dispose()
