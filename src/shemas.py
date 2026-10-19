"""Схемы Pydantic."""

from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    """Ответ для эндроинта проверки состояния."""

    message: Literal["ok"]
