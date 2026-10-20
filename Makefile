.DEFAULT_GOAL := help

COMPOSE := docker compose
WEB := $(COMPOSE) -f docker-compose.dev.yml exec web

# Самые важные команды (+ чтобы make не считал команды - файлами или директориями)
.PHONY: run_project pre-commit_all make_migrations migrations

## Справка
help:
	@echo "Available commands:"
	@awk 'prev ~ /^## / && $$0 ~ /^[a-zA-Z_-]+:/ {printf "  \033[36m%-25s\033[0m %s\n", substr($$0, 1, index($$0, ":")-1), substr(prev, 4)}; {prev=$$0}' Makefile


run_project:
	dev_compose_build
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env создан"; \
	else \
		echo ".env уже есть"; \
	fi
	dev_compose_without_build

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                 Качество кода                                #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Качество кода
## Установить pre-commit хуки
pre-commit-install-host:
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# Запускает и pre-push и pre-commit хуки!
## Запустить pre-commit хуки на хосте (на всех файлах — полная проверка)
pre-commit-all:
	uv run pre-commit run --all-files --hook-stage pre-push

## Запустить тесты в тестовом окружении
test:
	$(COMPOSE) -f docker-compose.test.yml run --rm web

## Удалить тестовые контейнеры
down_test:
	$(COMPOSE) -f docker-compose.test.yml down -v

## Единная команда для запуска тестов
test_all:
	@set -e; \
	trap '$(MAKE) -s down_test' EXIT; \
	$(MAKE) test

## Запустить GitHub Actions локально, требуется установленный act (https://github.com/nektos/act)
run_actions:
	act

## Ревью кода от ИИ-агента
review_project:
	opencode run --agent plan "Проведи финальный чек лист всего проекта, как написанно в файле AGENT.md" > tmp/review-project.md

# ---------------------------------------------------------------------------- #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                  Контейнеры                                  #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Команды внутри контейнера ----
### Контейнеры
## Показать состояние контейнеров
compose_ps:
	$(COMPOSE) -f docker-compose.dev.yml ps

## Смотреть логи web-контейнера
logs_web:
	$(COMPOSE) -f docker-compose.dev.yml logs -f web

## Открыть shell в web-контейнере
shell:
	$(WEB) bash


## Запустить контейнер разработки без пересборки
dev_compose_without_build:
	$(COMPOSE) -f docker-compose.dev.yml up -d --no-build
	$(MAKE) migrations

## Остановить контейнер разработки
dev_down:
	$(COMPOSE) -f docker-compose.dev.yml down

## Собрать образ контейнера для разработки
dev_compose_build:
	$(COMPOSE) -f docker-compose.dev.yml build

## Собрать образ тестового окружения
test_compose_build:
	$(COMPOSE) -f docker-compose.test.yml build

## Остановить контейнер разработки и удалить volume
remove_volume:
	$(COMPOSE) -f docker-compose.dev.yml down -v

# ---------------------------------------------------------------------------- #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                  Миграции БД                                 #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

### Миграции
## Инициализировать настройки alembic (alembic.ini и env.py)
init_migrations:
	uv run alembic init -t async migrations/

MESSAGE ?= Auto-generated migration
## Создать миграцию
make_migrations:
	$(WEB) uv run alembic revision --autogenerate -m "$(MESSAGE)"

## Приминить миграцию
migrations:
	$(WEB) uv run alembic upgrade head


# ---------------------------------------------------------------------------- #
