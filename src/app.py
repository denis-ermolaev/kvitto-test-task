"""Точка входа в FastAPI приложение."""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Payment, Tariff, get_async_db
from src.lifespan import lifespan
from src.shemas import Health, PaymentRequest, PaymentResponse, TariffResponse
from src.utils import installment_schedule

app = FastAPI(lifespan=lifespan)


@app.get(
    "/health", status_code=status.HTTP_200_OK, response_model=Health, tags=["Other"]
)
async def health() -> Health:
    """Проверка работоспособности приложения."""
    return Health(message="ok")


@app.get(
    "/tariffs",
    status_code=status.HTTP_200_OK,
    response_model=list[TariffResponse],
    tags=["Main"],
)
async def get_tariffs(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> list[TariffResponse]:
    """Получить все возможные тарифы."""
    tariffs = await db.scalars(select(Tariff))
    tariffs = tariffs.all()
    return [TariffResponse.model_validate(tariff) for tariff in tariffs]


@app.post(
    "/payments",
    status_code=status.HTTP_201_CREATED,
    response_description="Успешное создание платежа.",
    responses={
        200: {
            "description": "Повторный запрос с тем же Idempotency-Key. Платёж не создаётся, возвращается существующий.",
            "model": PaymentResponse,
        }
    },
    response_model=PaymentResponse,
    tags=["Main"],
)
async def post_payments(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    payment_data: PaymentRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentResponse:
    """Создать платёж."""
    if idempotency_key:
        payment = await db.scalars(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        payment = payment.one_or_none()
        if payment:
            response.status_code = status.HTTP_200_OK
            return PaymentResponse.model_validate(payment)
    # Обработка ошибок ----
    tariff = await db.scalars(select(Tariff).where(Tariff.id == payment_data.tariff_id))
    tariff = tariff.one_or_none()
    if tariff is None:
        raise HTTPException(
            status_code=422, detail="tariff_id is incorrect! It's not found!"
        )
    if (
        payment_data.promo_code is not None
        and payment_data.promo_code.upper() != "KVITTO10"
    ):
        raise HTTPException(status_code=422, detail="Promo code is incorrect!!")
    # -----

    # Создание нового платежа ----
    discount = 0
    amount = tariff.price
    schedule = None
    if (
        payment_data.promo_code is not None
        and payment_data.promo_code.upper() == "KVITTO10"
    ):
        discount = amount * 10 // 100  # Округление вниз
        amount -= discount
    if (
        payment_data.method == "installment"
        and payment_data.installment_months is not None
    ):
        schedule = installment_schedule(amount, payment_data.installment_months)
    new_payment = Payment(
        idempotency_key=idempotency_key,
        amount=amount,
        discount=discount,
        schedule=schedule,
        **payment_data.model_dump(),
    )
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)
    response.status_code = status.HTTP_201_CREATED
    return PaymentResponse.model_validate(new_payment)


@app.get("/payments/{payment_id}", status_code=200, tags=["Main"])
async def get_payments(
    payment_id: int, db: Annotated[AsyncSession, Depends(get_async_db)]
) -> PaymentResponse:
    """Получить информацию о платежи, либо NotFound."""
    payment = await db.scalars(select(Payment).where(Payment.id == payment_id))
    payment = payment.one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return PaymentResponse.model_validate(payment)
