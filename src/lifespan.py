"""Определение lifespan для FastAPI приложения."""

from types import AsyncGeneratorType

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import DB_URL


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGeneratorType[None]:
    """Асинхронный контекстный менеджер для открытия и закрытия базы данных для FastAPI приложения."""
    # __enter___
    pg_engine = create_async_engine(DB_URL)
    pg_async_session = async_sessionmaker(pg_engine, expire_on_commit=False)
    app.state.pg_engine = pg_engine
    app.state.pg_async_session = pg_async_session
    try:
        yield
    finally:
        # __exit__
        await pg_engine.dispose()
