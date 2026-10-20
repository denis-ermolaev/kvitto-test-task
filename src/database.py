"""SQLAlhemy."""

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

load_dotenv()

DB_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"


async def get_async_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """Depends от базы данных. Даёт асинхронную сессию."""
    pg_async_session: async_sessionmaker[AsyncSession] = (
        request.app.state.pg_async_session
    )
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
        default="pending",
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, nullable=False)
    promo_code: Mapped[str] = mapped_column(String, nullable=True)
    method: Mapped[str] = mapped_column(
        Enum("card", "sbp", "installment", name="payment_method"),
        nullable=False,
    )

    installment_months: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    schedule: Mapped[list] = mapped_column(JSON, nullable=True)

    email: Mapped[str] = mapped_column(String, nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String, nullable=True)

    tariff_id = mapped_column(ForeignKey("tariffs.id"), nullable=False)

    tariff = relationship(
        "Tariff",
        back_populates="payments",
    )


async def fill_db(pg_async_session: async_sessionmaker[AsyncSession]) -> None:
    """Заполняет базу данных начальными значениями."""
    async with pg_async_session() as db:
        tarriffs = [
            ("basic", 9900_00),
            ("standard", 19900_00),
            ("premium", 29900_00),
        ]
        title, price = 0, 1

        for tarriff in tarriffs:
            current_tariff = await db.scalars(
                select(Tariff).where(Tariff.title == tarriff[title])
            )
            current_tariff = current_tariff.one_or_none()
            if current_tariff is None:
                db.add(Tariff(title=tarriff[title], price=tarriff[price]))
                await db.commit()
