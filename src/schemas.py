"""Схемы Pydantic."""

import datetime as dt
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


class Health(BaseModel):
    """Ответ для эндроинта проверки состояния."""

    message: Literal["ok"]


class TariffResponse(BaseModel):
    """Валидация ответа для получения информации о тарифе."""

    id: int
    title: Literal["basic", "standard", "premium"]
    price: int

    model_config = ConfigDict(from_attributes=True)


class PaymentRequest(BaseModel):
    """Валидация тела запроса на создание платежа."""

    tariff_id: int
    email: EmailStr
    method: Literal["card", "sbp", "installment"]
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @model_validator(mode="after")
    def check_installment(self) -> Self:
        """Проверка, если рассрочка, то должно быть указано сколько месяцев для неё. Иначе месяцев быть не должно."""
        if self.method == "installment" and self.installment_months is None:
            msg = "installment_months обязателен для installment"
            raise ValueError(msg)
        if self.method != "installment" and self.installment_months is not None:
            msg_0 = "installment_months допустим только для installment"
            raise ValueError(msg_0)
        return self


class PaymentResponse(BaseModel):
    """Валидация для выдачи платежа без закрытых данных, по типу idempotency_key."""

    id: int
    status: Literal["pending", "succeeded", "failed", "refunded"]
    tariff_id: int
    amount: int
    discount: int
    method: Literal["card", "sbp", "installment"]
    installment_months: Literal[3, 6, 12] | None = None
    schedule: list[int] | None = None
    email: EmailStr
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class ChangePaymentStatusRequest(BaseModel):
    """Тело запроса на смену статуса платежа."""

    payment_id: int
    status: Literal["pending", "succeeded", "failed", "refunded"]
