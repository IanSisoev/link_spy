import random
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine
from models import Link


def generate_code():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(6))


class LinkStore:
    async def add(self, original_url):
        for _ in range(5):
            code = generate_code()
            try:
                async with AsyncSession(engine) as session:
                    session.add(Link(code=code, original_url=original_url))
                    await session.commit()
                return code
            except IntegrityError:
                pass
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

    async def add_click(self, code):
        async with AsyncSession(engine) as session:
            link = await session.get(Link, code)
            if link is not None:
                link.clicks += 1
                await session.commit()


class MemoryStore:
    def __init__(self):
        self.links = {}

    async def add(self, original_url):
        code = generate_code()
        self.links[code] = {
            "code": code,
            "original_url": original_url,
            "clicks": 0
            }
        return code

    async def get(self, code):
        return self.links.get(code)

    async def add_click(self, code):
        self.links[code]["clicks"] += 1


real_store = None


def get_store():
    global real_store
    if real_store is None:
        real_store = LinkStore()
    return real_store
