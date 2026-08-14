import secrets
import string
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from db_connecting import engine
from db_models import Link, User
# Код ошибки PostgreSQL: нарушение уникальности
UNIQUE_VIOLATION = "23505"


def generate_code():
    letters = string.ascii_letters + string.digits
    return "".join(secrets.choice(letters) for _ in range(6))


class LinkStore:
    async def add(self, original_url, owner):
        for _ in range(5):
            code = generate_code()
            try:
                async with AsyncSession(engine) as session:
                    session.add(
                        Link(code=code, original_url=original_url, owner=owner)
                    )
                    await session.commit()
                return code
            except IntegrityError as error:
                # Повтором лечится только занятый код; остальное —
                # например, несуществующий owner — пробрасываем как есть
                if getattr(error.orig, "sqlstate", None) != UNIQUE_VIOLATION:
                    raise
        raise RuntimeError("Не удалось подобрать свободный код")

    async def get(self, code):
        async with AsyncSession(engine) as session:
            link = await session.get(Link, code)
            if link is None:
                return None
            return {
                "code": link.code,
                "original_url": link.original_url,
                "clicks": link.clicks
                }

    async def get_by_owner(self, owner):
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Link).where(Link.owner == owner)
            )
            return [
                {
                    "code": link.code,
                    "original_url": link.original_url,
                    "clicks": link.clicks,
                }
                for link in result.scalars()
            ]

    async def add_click(self, code):
        # Прибавляет база, а не Python: при двух одновременных переходах
        # чтение-и-запись на нашей стороне потеряли бы один клик
        async with AsyncSession(engine) as session:
            await session.execute(
                update(Link)
                .where(Link.code == code)
                .values(clicks=Link.clicks + 1)
            )
            await session.commit()


class MemoryStore:
    """Хранилище в памяти для тестов.

    Обязано повторять интерфейс и форму ответов LinkStore: разойдутся —
    и тесты начнут проверять поведение, которого нет в проде.
    """
    def __init__(self):
        self.links = {}

    async def add(self, original_url, owner):
        code = generate_code()
        self.links[code] = {
            "code": code,
            "original_url": original_url,
            "clicks": 0,
            "owner": owner,
            }
        return code

    async def get(self, code):
        link = self.links.get(code)
        if link is None:
            return None
        return {
            "code": link["code"],
            "original_url": link["original_url"],
            "clicks": link["clicks"],
        }

    async def add_click(self, code):
        if code in self.links:
            self.links[code]["clicks"] += 1

    async def get_by_owner(self, owner):
        return [
            {
                "code": link["code"],
                "original_url": link["original_url"],
                "clicks": link["clicks"],
            }
            for link in self.links.values()
            if link["owner"] == owner
        ]


real_store = None


def get_store():
    global real_store
    if real_store is None:
        real_store = LinkStore()
    return real_store


class UserStore:
    async def get(self, username):
        async with AsyncSession(engine) as session:
            user = await session.get(User, username)
            if user is None:
                return None
            return {
                "username": user.username,
                "password_hash": user.password_hash,
            }

    async def add(self, username, password_hash):
        # Не проверяем занятость логина заранее: между проверкой и вставкой
        # успел бы влезть второй такой же запрос. Уникальность стережёт база
        async with AsyncSession(engine) as session:
            session.add(User(username=username, password_hash=password_hash))
            try:
                await session.commit()
            except IntegrityError:
                return False
        return True


class MemoryUserStore:
    def __init__(self):
        self.users = {}

    async def get(self, username):
        user = self.users.get(username)
        if user is None:
            return None
        return {
            "username": user["username"],
            "password_hash": user["password_hash"],
        }

    async def add(self, username, password_hash):
        if username in self.users:
            return False
        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
        }
        return True


real_user_store = None


def get_user_store():
    global real_user_store
    if real_user_store is None:
        real_user_store = UserStore()
    return real_user_store
