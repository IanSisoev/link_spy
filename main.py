from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv
import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from schemas import RegisterRequest, ShortenRequest, ShortenResponse
from database import engine
from models import User
from security import hash_password, verify_password, create_token, get_current_user
from storage import get_store


load_dotenv()

BASE_URL = os.getenv("BASE_URL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


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
