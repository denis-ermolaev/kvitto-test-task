"""SQLAlhemy."""

import os
from datetime import UTC, datetime
from types import AsyncGeneratorType

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

load_dotenv()

DB_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"


async def get_async_db(request: Request) -> AsyncGeneratorType[AsyncSession]:
    """Depends от базы данных. Даёт асинхронную сессию."""
    pg_async_session = request.app.state.pg_async_session
    async with pg_async_session() as session:
        yield session


class Base(DeclarativeBase):
    """Родительская модель базы данных - все остальные наследуются от неё."""


class Tariff(Base):
    """Тариф."""

    __tablename__ = "tariffs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    payments = relationship(
        "Payment",
        back_populates="tariff",
        uselist=True,  # False - один к одному; True - один ко многим
        cascade="all, delete-orphan",
    )


class Payment(Base):
    """Платёж."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "succeeded", "failed", "refunded", name="status"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(
        Enum("card", "sbp", "installment", name="payment_method"),
        nullable=False,
    )

    installment_months: Mapped[str] = mapped_column(
        Enum("3", "6", "12", name="installment_months"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    schedule: Mapped[list] = mapped_column(JSON, nullable=True)

    email: Mapped[list] = mapped_column(String, nullable=False)

    tariff_id = mapped_column(ForeignKey("tariffs.id"), nullable=False)

    tariff = relationship(
        "Tariff",
        back_populates="payments",
    )
