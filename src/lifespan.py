"""Определение lifespan для FastAPI приложения."""

import os
from types import AsyncGeneratorType

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGeneratorType[None]:
    """Асинхронный контекстный менеджер для открытия и закрытия базы данных для FastAPI приложения."""
    # __enter___
    pg_engine = create_async_engine(
        f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
    )
    pg_async_session = async_sessionmaker(pg_engine, expire_on_commit=False)
    app.state.pg_engine = pg_engine
    app.state.pg_async_session = pg_async_session
    try:
        yield
    finally:
        # __exit__
        await pg_engine.dispose()
