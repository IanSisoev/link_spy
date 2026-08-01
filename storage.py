import random
import string
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine
from models import Link


def generate_code():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(6))


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
        async with AsyncSession(engine) as session:
            link = await session.get(Link, code)
            if link is not None:
                link.clicks += 1
                await session.commit()


class MemoryStore:
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
        return self.links.get(code)

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

    async def add_click(self, code):
        self.links[code]["clicks"] += 1


real_store = None


def get_store():
    global real_store
    if real_store is None:
        real_store = LinkStore()
    return real_store
