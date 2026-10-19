"""Базовые тесты."""

from httpx import AsyncClient


async def test_health(http_client: AsyncClient):
    """Проверка работы приложения(health)."""
    result = await http_client.get("health")
    assert result.is_success
    assert result.json() == {"message": "ok"}
