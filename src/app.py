"""Точка входа в FastAPI приложение."""

from fastapi import FastAPI

from src.lifespan import lifespan
from src.shemas import Health

app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=200, response_model=Health, tags=["Other"])
async def health() -> Health:
    """Проверка работоспособности приложения."""
    return Health(message="ok")
