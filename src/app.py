"""Точка входа в FastAPI приложение."""

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Tariff, get_async_db
from src.lifespan import lifespan
from src.shemas import Health, TariffResponse

app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=200, response_model=Health, tags=["Other"])
async def health() -> Health:
    """Проверка работоспособности приложения."""
    return Health(message="ok")


@app.get(
    "/tariffs", status_code=200, response_model=list[TariffResponse], tags=["Main"]
)
async def get_tariffs(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> list[TariffResponse]:
    """Получить все возможные тарифы."""
    tariffs = await db.scalars(select(Tariff))
    tariffs = tariffs.all()
    return [TariffResponse.model_validate(tariff) for tariff in tariffs]
