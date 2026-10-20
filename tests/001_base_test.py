"""Базовые тесты."""

import hashlib
import hmac
import json
import os

from httpx import AsyncClient


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
    # ---------------------------------------------------------------------------- #

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
    # ---------------------------------------------------------------------------- #

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
    # ---------------------------------------------------------------------------- #

    # Неправильный переход с succeeded к failed ----
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
    # ---------------------------------------------------------------------------- #

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
    # ---------------------------------------------------------------------------- #
