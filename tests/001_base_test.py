"""Базовые тесты."""

import hashlib
import hmac
import json
import os
import uuid

from httpx import AsyncClient

from src.schemas import PaymentResponse
from src.utils import installment_schedule


async def test_health(http_client: AsyncClient):
    """Проверка работы приложения(health)."""
    result = await http_client.get("/health")
    assert result.is_success
    assert result.json() == {"message": "ok"}


async def test_get_tariffs(http_client: AsyncClient):
    """Проверка получения тарифов."""
    result = await http_client.get("/tariffs")
    assert result.is_success
    assert result.json() == [
        {"id": 1, "title": "basic", "price": 990000},
        {"id": 2, "title": "standard", "price": 1990000},
        {"id": 3, "title": "premium", "price": 2990000},
    ]


async def test_post_payments_promo_code(http_client: AsyncClient):
    """Проверка получения тарифов с промокодом и без."""
    # С промокодом ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
            "promo_code": "KVITTO10",
        },
    )
    assert result.is_success
    assert result.json()["amount"] == 891000

    # Промокод в нижнем регистре ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
            "promo_code": "kvitto10",
        },
    )
    assert result.is_success
    assert result.json()["amount"] == 891000

    # Без промокода ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "user@example.com",
            "method": "card",
        },
    )
    assert result.is_success
    assert result.json()["amount"] == 1990000

    # Не существующий промокод ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
            "promo_code": "kvitto20",
        },
    )
    assert result.status_code == 422

    # Не существующий tariff_id ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 15,
            "email": "user@example.com",
            "method": "card",
            "promo_code": "kvitto10",
        },
    )
    assert result.status_code == 422


async def test_installment_schedule():
    """Проверка функции для рассчёта графика платежей для рассрочки."""
    result = installment_schedule(1990000, 3)
    assert result == [663334, 663333, 663333]

    result = installment_schedule(1990095, 3)
    assert result == [663365, 663365, 663365]


async def test_post_payments_installment(http_client: AsyncClient):
    """Проверка получения тарифов с рассрочкой."""
    # На 3 месяца ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 3,
            "promo_code": "KVITTO10",
        },
    )
    assert result.is_success
    json_result = result.json()
    assert sum(json_result["schedule"]) == json_result["amount"]

    # На 6 ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 6,
            "promo_code": "KVITTO10",
        },
    )
    assert result.is_success
    json_result = result.json()
    assert sum(json_result["schedule"]) == json_result["amount"]

    # На 12 ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 12,
            "promo_code": "KVITTO10",
        },
    )
    assert result.is_success
    json_result = result.json()
    assert sum(json_result["schedule"]) == json_result["amount"]

    # На 24 - не разрешённое кол-во месяцев ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 24,
            "promo_code": "KVITTO10",
        },
    )
    assert result.status_code == 422

    # Не хватает installment_months ----
    result = await http_client.post(
        "/payments",
        json={"tariff_id": 1, "email": "user@example.com", "method": "installment"},
    )
    assert result.status_code == 422

    # installment_months можно указывать только с "method": "installment" ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
            "installment_months": 12,
        },
    )
    assert result.status_code == 422


async def test_post_payments_idempotency_key(http_client: AsyncClient):
    """Проверка получения тарифов с idempotency_key."""
    # Первое создание ----
    idempotency_key = str(uuid.uuid4())
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 3,
            "promo_code": "KVITTO10",
        },
        headers={"Idempotency-Key": idempotency_key},
    )
    assert result.status_code == 201
    payment_id = result.json()["id"]

    # Вторая попытка создания, платёж уже создан, возвращается просто текущий ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 3,
            "promo_code": "KVITTO10",
        },
        headers={"Idempotency-Key": idempotency_key},
    )
    assert result.status_code == 200
    assert payment_id == result.json()["id"]


async def test_get_payments(http_client: AsyncClient):
    """Получить payment по id."""
    # Создание трёх платежей ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 12,
            "promo_code": "KVITTO10",
        },
    )
    assert result.is_success
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "user@example.com",
            "method": "card",
        },
    )
    assert result.is_success
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "installment",
            "installment_months": 6,
        },
    )
    assert result.is_success

    # Успешное получение ----
    result = await http_client.get(
        f"/payments/{1}",
    )
    assert result.is_success
    assert PaymentResponse(**result.json())

    # Платежа с id 15 не существует ----
    result = await http_client.get(
        f"/payments/{15}",
    )
    assert result.status_code == 404


async def test_change_payment_status(http_client: AsyncClient):
    """Проверка смены статуса платежа банком. С учётом заголовка X-Signature для аутентификации."""
    # Принимает подпись, но так как такого платёжа нету - 404 ----
    payload = {"payment_id": 1, "status": "succeeded"}
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    signature = hmac.new(
        key=os.environ["WEBHOOK_SECRET"].encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    result = await http_client.post(
        "/webhooks/bank",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert result.status_code == 404

    # Создание платежа ----
    result = await http_client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
        },
    )
    assert result.is_success

    # Банк делает корректный переход с корректной подписью ----
    result = await http_client.post(
        "/webhooks/bank",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert result.is_success
    assert result.json() == {"result": "ok"}

    # Неправильный переход с succeeded к failed ----
    result = await http_client.get(
        f"/payments/{1}",
    )
    assert result.is_success
    assert result.json()["status"] == "succeeded"

    payload = {"payment_id": 1, "status": "failed"}
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(
        key=os.environ["WEBHOOK_SECRET"].encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    result = await http_client.post(
        "/webhooks/bank",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert result.status_code == 409
    assert result.json() == {"error": "invalid_transition"}

    result = await http_client.get(
        f"/payments/{1}",
    )
    assert result.is_success
    assert result.json()["status"] == "succeeded"

    # Неправильная подпись ----
    result = await http_client.post(
        "/webhooks/bank",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "random",
        },
    )
    assert result.status_code == 401
