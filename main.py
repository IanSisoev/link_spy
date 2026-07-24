from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
import random
import string
import os
from dotenv import load_dotenv
import logging
from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
BASE_URL = os.getenv("BASE_URL")
engine = create_engine(DATABASE_URL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


class Base(DeclarativeBase):
    pass


class LinkStore:
    def __init__(self):
        Base.metadata.create_all(engine)

    def add(self, original_url):
        for attempt in range(5):
            code = generate_code()
            try:
                with Session(engine) as session:
                    session.add(Link(code=code, original_url=original_url))
                    session.commit()
                return code
            except IntegrityError:
                pass
        raise RuntimeError("Не удалось подобрать свободный код")

    def get(self, code):
        with Session(engine) as session:
            link = session.get(Link, code)
            if link is None:
                return None
            return {"code": link.code, "original_url": link.original_url, "clicks": link.clicks}

    def add_click(self, code):
        with Session(engine) as session:
            link = session.get(Link, code)
            if link is not None:
                link.clicks += 1
                session.commit()

class Link(Base):
    __tablename__ = "links"

    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    clicks: Mapped[int] = mapped_column(default=0)


class ShortenRequest(BaseModel):
    original_url: HttpUrl


class ShortenResponse(BaseModel):
    code: str
    short_url: str


def generate_code():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(6))


class MemoryStore:
    def __init__(self):
        self.links = {}

    def add(self, original_url):
        code = generate_code()
        self.links[code] = {"code": code, "original_url": original_url, "clicks": 0}
        return code

    def get(self, code):
        return self.links.get(code)

    def add_click(self, code):
        self.links[code]["clicks"] += 1


real_store = None


def get_store():
    global real_store
    if real_store is None:
        real_store = LinkStore()
    return real_store


@app.post("/shorten", response_model=ShortenResponse)
def shorten(request: ShortenRequest, store=Depends(get_store)):
    code = store.add(str(request.original_url))
    logger.info("Создана ссылка: %s -> %s", code, request.original_url)
    return ShortenResponse(
        code=code,
        short_url=BASE_URL + "/" + code,
    )


@app.get("/stats/{code}")
def stats(code, store=Depends(get_store)):
    link = store.get(code)
    if link is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return link


@app.get("/{code}")
def redirect(code, store=Depends(get_store)):
    link = store.get(code)
    if link is None:
        logger.warning("Переход по несуществующему коду: %s", code)
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    store.add_click(code)
    logger.info("Переход по коду: %s", code)
    return RedirectResponse(link["original_url"])
