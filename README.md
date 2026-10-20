# Тестовое задание на junior python backend (fastapi) разработчика от компании Квитто

Небольшой сервис, через который онлайн-школа принимает оплату курса через Квитто: три эндпоинта и уведомление от банка.

## Запуск

Тестовый запуск:
```bash
mkdir kvitto-test-task
cd kvitto-test-task
git clone https://github.com/denis-ermolaev/kvitto-test-task.git
# или, если настроен доступ по ssh
git clone git@github.com:denis-ermolaev/kvitto-test-task.git

make run_project
# -> http://127.0.0.1:8000/docs
```

Запуск тестов:
```bash
make test_all
```

Тестовые curl:

## Проблемы запуска

Если проблема с доступом, можно использовать прокси, добавить переменные окружения в `~/.bashrc`, предварительно их заполнив
```
# HTTP_PROXY=http://user:password@ip:port
# HTTPS_PROXY=http://user:password@ip:port
# NO_PROXY=localhost,127.0.0.1
```
Далее `source ~/.bashrc`
