from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv
import logging
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from api_schemas import RegisterRequest, ShortenRequest, ShortenResponse
from security import hash_password, verify_password, create_token, get_current_user
from storage import get_store, get_user_store
from fastapi.concurrency import run_in_threadpool


load_dotenv()

BASE_URL = os.getenv("BASE_URL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/register")
async def register(request: RegisterRequest, store=Depends(get_user_store)):
    password_hash = await run_in_threadpool(hash_password, request.password)
    created = await store.add(request.username, password_hash)
    if not created:
        raise HTTPException(
            status_code=409,
            detail="Пользователь уже существует"
            )
    return {"username": request.username}


@app.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    store=Depends(get_user_store),
):
    user = await store.get(form.username)

    if user is None or not await run_in_threadpool(
        verify_password, form.password, user["password_hash"]
    ):
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
    code = await store.add(str(request.original_url), current_user)
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


@app.get("/my/links")
async def my_links(
    store=Depends(get_store),
    current_user: str = Depends(get_current_user),
):
    return await store.get_by_owner(current_user)


# Должен оставаться последним: ловит любой одиночный путь,
# и всё объявленное ниже до своего роута не дойдёт
@app.get("/{code}")
async def redirect(code, store=Depends(get_store)):
    link = await store.get(code)
    if link is None:
        logger.warning("Переход по несуществующему коду: %s", code)
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    await store.add_click(code)
    logger.info("Переход по коду: %s", code)
    return RedirectResponse(link["original_url"])
