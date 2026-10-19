"""SQLAlhemy."""

from types import AsyncGeneratorType

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


async def get_async_db(request: Request) -> AsyncGeneratorType[AsyncSession]:
    """Depends от базы данных. Даёт асинхронную сессию."""
    pg_async_session = request.app.state.pg_async_session
    async with pg_async_session() as session:
        yield session


class Base(DeclarativeBase):
    """Родительская модель базы данных - все остальные наследуются от неё."""
