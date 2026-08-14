# LinkSpy
 
Сервис сокращения ссылок: принимает длинный URL, выдаёт короткий код, редиректит по нему на оригинал и считает переходы. Ссылки принадлежат создавшему их пользователю.
 
Живой сервис: https://link-spy-o2g7.onrender.com/docs
(бесплатный хостинг — первый запрос после паузы может занять до минуты, пока сервис просыпается)
 
## Стек
 
Python 3.13, FastAPI, PostgreSQL 16, SQLAlchemy (async, asyncpg), Alembic, JWT-авторизация с bcrypt, Docker Compose, pytest, GitHub Actions, деплой на Render.
 
## API
 
| Метод | Путь | Описание | Авторизация |
|---|---|---|---|
| `POST` | `/register` | создать аккаунт | — |
| `POST` | `/login` | получить JWT-токен | — |
| `POST` | `/shorten` | создать короткую ссылку | требуется |
| `GET` | `/my/links` | ссылки текущего пользователя | требуется |
| `GET` | `/stats/{code}` | статистика по коду | — |
| `GET` | `/{code}` | редирект на исходный URL, +1 к счётчику | — |
 
```http
POST /shorten
Authorization: Bearer <token>
{"original_url": "https://example.com/very/long/path"}
```
 
```json
{"code": "aB3kX9", "short_url": "https://link-spy-o2g7.onrender.com/aB3kX9"}
```
 
Невалидный URL отклоняется с кодом `422`, несуществующий код — `404`, отсутствующий или просроченный токен — `401`.
 
## Запуск локально
 
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
| `JWT_SECRET` | ключ для подписи токенов авторизации |
 
## Структура проекта
 
```
main.py           приложение и роуты
db_connecting.py  движок, декларативная база
db_models.py      таблицы: links, users
api_schemas.py    модели запросов и ответов
security.py       хеширование паролей, JWT
storage.py        работа с данными, хранилище в памяти для тестов
migrations/       ревизии Alembic
```
 
## Миграции
 
Изменения схемы оформлены ревизиями Alembic. При старте контейнер выполняет `alembic upgrade head`, поэтому деплой обновляет базу до того, как поднимется приложение.
 
## Тесты
 
```bash
pytest
```
 
База для тестов не нужна: хранилище подменяется на реализацию в памяти. Тесты гоняются при каждом push через GitHub Actions.
 
---
 
# LinkSpy
 
A URL shortener: takes a long URL, returns a short code, redirects to the original and counts clicks. Links belong to the user who created them.
 
Live: https://link-spy-o2g7.onrender.com/docs
(free hosting — the first request after a pause may take up to a minute while the service wakes up)
 
## Stack
 
Python 3.13, FastAPI, PostgreSQL 16, SQLAlchemy (async, asyncpg), Alembic, JWT auth with bcrypt, Docker Compose, pytest, GitHub Actions, deployed on Render.
 
## API
 
| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/register` | create an account | — |
| `POST` | `/login` | get a JWT token | — |
| `POST` | `/shorten` | create a short link | required |
| `GET` | `/my/links` | links created by the current user | required |
| `GET` | `/stats/{code}` | statistics for a code | — |
| `GET` | `/{code}` | redirect to the original URL, +1 click | — |
 
```http
POST /shorten
Authorization: Bearer <token>
{"original_url": "https://example.com/very/long/path"}
```
 
```json
{"code": "aB3kX9", "short_url": "https://link-spy-o2g7.onrender.com/aB3kX9"}
```
 
An invalid URL is rejected with `422`, an unknown code with `404`, a missing or expired token with `401`.
 
## Running locally
 
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
| `JWT_SECRET` | key used to sign auth tokens |
 
## Project layout
 
```
main.py           app and routes
db_connecting.py  engine, declarative base
db_models.py      tables: links, users
api_schemas.py    request and response models
security.py       password hashing, JWT
storage.py        data access, in-memory store for tests
migrations/       Alembic revisions
```
 
## Migrations
 
Schema changes are Alembic revisions. The container runs `alembic upgrade head` on startup, so a deploy migrates the database before the app comes up.
 
## Tests
 
```bash
pytest
```
 
No database required: the storage layer is swapped for an in-memory implementation. Tests run on every push via GitHub Actions.
