"""Схемы Pydantic."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Health(BaseModel):
    """Ответ для эндроинта проверки состояния."""

    message: Literal["ok"]


class TariffResponse(BaseModel):
    """Валидация ответа для получения информации о тарифе."""

    id: int
    title: Literal["basic", "standard", "premium"]
    price: int

    model_config = ConfigDict(from_attributes=True)
