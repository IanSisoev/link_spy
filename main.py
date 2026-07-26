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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import bcrypt
import jwt
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
BASE_URL = os.getenv("BASE_URL")
engine = create_async_engine(DATABASE_URL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now() + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Неверный или просроченный токен"
            )
    return payload["sub"]


class Base(DeclarativeBase):
    pass


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LinkStore:
    async def add(self, original_url):
        for attempt in range(5):
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


class Link(Base):
    __tablename__ = "links"
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    clicks: Mapped[int] = mapped_column(default=0)


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(primary_key=True)
    password_hash: Mapped[str]


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


@app.post("/register")
async def register(request: RegisterRequest):
    async with AsyncSession(engine) as session:
        existing = await session.get(User, request.username)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="Пользователь уже существует"
                )

        user = User(
            username=request.username,
            password_hash=hash_password(request.password),
        )
        session.add(user)
        await session.commit()

    return {"username": request.username}


@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    async with AsyncSession(engine) as session:
        user = await session.get(User, form.username)

    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль"
            )

    token = create_token(form.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/shorten", response_model=ShortenResponse)
async def shorten(
    request: ShortenRequest,
    store=Depends(get_store),
    current_user: str = Depends(get_current_user),
):
    code = await store.add(str(request.original_url))
    logger.info(
        "Создана ссылка пользователем %s: %s -> %s",
        current_user,
        code,
        request.original_url
        )
    return ShortenResponse(code=code, short_url=BASE_URL + "/" + code)


@app.get("/stats/{code}")
async def stats(code, store=Depends(get_store)):
    link = await store.get(code)
    if link is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return link


@app.get("/{code}")
async def redirect(code, store=Depends(get_store)):
    link = await store.get(code)
    if link is None:
        logger.warning("Переход по несуществующему коду: %s", code)
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    await store.add_click(code)
    logger.info("Переход по коду: %s", code)
    return RedirectResponse(link["original_url"])
