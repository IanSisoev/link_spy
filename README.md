# LinkSpy

Сервис сокращения ссылок: принимает длинный URL, выдаёт короткий код, редиректит по нему на оригинал и считает переходы.

## Стек

Python 3.13, FastAPI, PostgreSQL 16, psycopg 3 с пулом соединений, Docker Compose, pytest.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

Документация API: http://127.0.0.1:8000/docs

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | строка подключения к PostgreSQL |
| `BASE_URL` | базовый адрес для сборки короткой ссылки |

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/shorten` | создать короткую ссылку |
| `GET` | `/{code}` | редирект на исходный URL, +1 к счётчику |
| `GET` | `/stats/{code}` | статистика по коду |

```http
POST /shorten
{"original_url": "https://example.com/very/long/path"}
```

```json
{"code": "aB3kX9", "short_url": "http://127.0.0.1:8000/aB3kX9"}
```

Невалидный URL отклоняется с кодом `422`, несуществующий код — `404`.

## Тесты

```bash
pytest
```

База для тестов не нужна: хранилище подменяется на реализацию в памяти.


# LinkSpy

A URL shortener: takes a long URL, returns a short code, redirects to the original and counts clicks.

## Stack

Python 3.13, FastAPI, PostgreSQL 16, psycopg 3 with a connection pool, Docker Compose, pytest.

## Running

```bash
cp .env.example .env
docker compose up --build
```

API docs: http://127.0.0.1:8000/docs

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `BASE_URL` | base address used to build the short link |

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/shorten` | create a short link |
| `GET` | `/{code}` | redirect to the original URL, +1 click |
| `GET` | `/stats/{code}` | statistics for a code |

```http
POST /shorten
{"original_url": "https://example.com/very/long/path"}
```

```json
{"code": "aB3kX9", "short_url": "http://127.0.0.1:8000/aB3kX9"}
```

An invalid URL is rejected with `422`, an unknown code with `404`.

## Tests

```bash
pytest
```

No database required: the storage layer is swapped for an in-memory implementation.