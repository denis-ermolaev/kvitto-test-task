# Квитто — сервис приёма оплаты курса

Тестовое задание: небольшой сервис, через который онлайн-школа принимает оплату курса через Квитто. Реализованы тарифы, создание платежа, получение платежа и уведомление от банка.

## Стек

- Python 3.14
- FastAPI, Pydantic v2
- PostgreSQL 16, SQLAlchemy 2 (async), Alembic
- pytest, httpx
- Docker Compose, uv, Makefile
- ruff, ty, pre-commit, GitHub Actions

## Быстрый старт

### Требования

- Docker и Docker Compose
- `make`
- Свободные порты `8000` и `5432`

`uv` на хосте не обязателен: приложение, миграции и тесты запускаются внутри контейнеров.

### Запуск

```bash
git clone https://github.com/denis-ermolaev/kvitto-test-task.git
cd kvitto-test-task

make run_project
```

Команда `make run_project`:

1. собирает образ приложения;
2. создаёт `.env` из `.env.example`, если файла ещё нет;
3. поднимает PostgreSQL и приложение;
4. применяет миграции Alembic.

После запуска доступны:

- Swagger UI — http://127.0.0.1:8000/docs
- OpenAPI — http://127.0.0.1:8000/openapi.json
- Проверка состояния — http://127.0.0.1:8000/health

Остановить приложение:

```bash
make dev_down
```

## Переменные окружения

Файл `.env` создаётся автоматически при `make run_project`. Перед использованием рекомендуется изменить пароль БД и секрет вебхука.

| Переменная | Назначение | Значение по умолчанию |
| --- | --- | --- |
| `DB_NAME` | Имя базы данных | `api` |
| `DB_USER` | Пользователь БД | `api` |
| `DB_PASSWORD` | Пароль БД | `your_secure_password_here` |
| `DB_HOST` | Хост БД (внутри Docker) | `db` |
| `DB_PORT` | Порт БД | `5432` |
| `WEBHOOK_SECRET` | Секрет для подписи вебхука | `secret` |

`DB_HOST=db` рассчитан на запуск внутри Docker Compose. Для локального запуска без Docker потребуется изменить хост на `localhost`.

## API

| Метод | Путь | Назначение | Ответы |
| --- | --- | --- | --- |
| `GET` | `/health` | Проверка работоспособности | `200` |
| `GET` | `/tariffs` | Список тарифов | `200` |
| `POST` | `/payments` | Создание платежа | `201`, `200` при повторе с `Idempotency-Key`, `422` |
| `GET` | `/payments/{id}` | Получение платежа | `200`, `404` |
| `POST` | `/webhooks/bank` | Смена статуса платежа банком | `200`, `401`, `404`, `409` |

### Коротко о правилах

- Все суммы — в копейках, целыми числами.
- Промокод `KVITTO10` даёт скидку 10%, регистр не важен.
- Для `method=installment` обязателен `installment_months`: `3`, `6` или `12`.
- Новый платёж получает статус `pending`. Разрешены переходы `pending → succeeded`, `pending → failed`, `succeeded → refunded`.
- Вебхук требует заголовок `X-Signature` — HMAC-SHA256 от сырого тела запроса с секретом `WEBHOOK_SECRET`.

## Примеры запросов

### Получить тарифы

```bash
curl http://127.0.0.1:8000/tariffs
```

### Создать платёж картой

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": 2,
    "email": "student@example.com",
    "method": "card"
  }'
```

### Создать рассрочку с промокодом

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": 2,
    "email": "student@example.com",
    "method": "installment",
    "installment_months": 3,
    "promo_code": "kvitto10"
  }'
```

Ответ будет содержать `amount` со скидкой и `schedule` — график платежей. Сумма `schedule` всегда равна `amount`.

### Повторный запрос с Idempotency-Key

Первый запрос создаёт платёж и возвращает `201`. Повторный запрос с тем же ключом вернёт существующий платёж с кодом `200` и не создаст дубль.

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-key-123" \
  -d '{
    "tariff_id": 1,
    "email": "student@example.com",
    "method": "card"
  }'
```

### Получить платёж

Замените `1` на `id` из ответа на создание платежа.

```bash
curl http://127.0.0.1:8000/payments/1
```

### Уведомление от банка

Подпись считается от точного тела запроса. Замените `payment_id` на id существующего платежа в статусе `pending`.

```bash
source .env

BODY='{"payment_id":1,"status":"succeeded"}'
SIGNATURE=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

curl -X POST http://127.0.0.1:8000/webhooks/bank \
  -H "Content-Type: application/json" \
  -H "X-Signature: $SIGNATURE" \
  -d "$BODY"
```

При успешной смене статуса вернётся `200 {"result":"ok"}`. Неверная подпись — `401`, запрещённый переход — `409 {"error":"invalid_transition"}`.

## Тесты

Перед запуском тестов должен существовать `.env` (если его ещё нет):

```bash
test -f .env || cp .env.example .env
make test_all
```

`make test_all` запускает отдельный compose-проект `kvitto_test` с тестовой БД на tmpfs. После прогона контейнеры удаляются, данные тестовой БД не сохраняются. Тесты не используют dev-базу и не конфликтуют с запущенным приложением.

Сейчас в проекте 8 тестов, покрытие `src` — 98%.

Покрыты:

- получение тарифов;
- промокод в верхнем и нижнем регистре, а также неизвестный промокод;
- график рассрочки для 3, 6 и 12 месяцев;
- идемпотентность при повторном запросе;
- получение платежа и `404` для несуществующего;
- смена статуса банком, запрещённый переход и неверная подпись.

## Миграции

Применить миграции:

```bash
make migrations
```

Создать новую миграцию:

```bash
make make_migrations MESSAGE="add payment index"
```

## Полезные команды

| Команда | Действие |
| --- | --- |
| `make help` | Список доступных команд |
| `make run_project` | Сборка и запуск проекта |
| `make test_all` | Запуск тестов в отдельном окружении |
| `make logs_web` | Логи приложения |
| `make shell` | Shell внутри контейнера приложения |
| `make compose_ps` | Состояние контейнеров |
| `make dev_down` | Остановить контейнеры разработки |
| `make down_test` | Удалить тестовые контейнеры и volume |
| `make pre-commit-all` | Запустить pre-commit хуки на всех файлах |
| `make run_actions` | Локальный запуск GitHub Actions через `act` |

## Структура проекта

```text
src/
  app.py          # FastAPI-приложение и эндпоинты
  schemas.py      # Pydantic-схемы запросов и ответов
  database.py     # SQLAlchemy-модели и зависимость сессии
  lifespan.py     # Создание engine/session и заполнение тарифов
  utils.py        # Расчёт графика рассрочки
tests/
  conftest.py     # Фикстуры, миграции и очистка БД
  001_base_test.py
migrations/       # Alembic
docker-compose.dev.yml
docker-compose.test.yml
Makefile
```

## Проблемы с прокси

Если `curl` к `127.0.0.1` уходит через прокси, добавьте локальные адреса в `NO_PROXY`. Например, в `~/.bashrc`:
Если есть проблемы со сборкой docker контейнера, можно установить прокси `HTTPS_PROXY` и `HTTP_PROXY`

```bash
# ~/.bashrc
HTTP_PROXY=http://user:password@ip:port
HTTPS_PROXY=http://user:password@ip:port
NO_PROXY=localhost,127.0.0.1
```

Затем выполните `source ~/.bashrc`. Для разового запроса можно использовать `curl --noproxy '*'`.
