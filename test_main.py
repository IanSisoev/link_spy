from fastapi.testclient import TestClient
from main import app
from security import get_current_user
from storage import (
    get_store,
    get_user_store,
    MemoryStore,
    MemoryUserStore,
    generate_code,
)

memory_users = MemoryUserStore()
app.dependency_overrides[get_user_store] = lambda: memory_users


memory = MemoryStore()
app.dependency_overrides[get_store] = lambda: memory
app.dependency_overrides[get_current_user] = lambda: "testuser"

client = TestClient(app)


def test_create_and_redirect():
    response = client.post(
        "/shorten",
        json={"original_url": "https://google.com"}
        )
    assert response.status_code == 200
    code = response.json()["code"]
    response = client.get("/" + code, follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://google.com/"


def test_shorten_rejects_invalid_url():
    response = client.post("/shorten", json={"original_url": "not a url"})
    assert response.status_code == 422


def test_redirect_not_found():
    response = client.get("/несуществующий", follow_redirects=False)
    assert response.status_code == 404


def test_generate_code_length():
    code = generate_code()
    assert len(code) == 6


def test_generate_code_unique():
    code1 = generate_code()
    code2 = generate_code()
    assert code1 != code2


def test_my_links_shows_only_own_links():
    response = client.post(
        "/shorten",
        json={"original_url": "https://example.com"}
        )
    my_code = response.json()["code"]

    memory.links["stranger"] = {
        "code": "stranger",
        "original_url": "https://other.com",
        "clicks": 0,
        "owner": "someone_else",
        }

    response = client.get("/my/links")
    assert response.status_code == 200

    codes = [link["code"] for link in response.json()]
    assert my_code in codes
    assert "stranger" not in codes


def test_shorten_requires_token():
    # Снимаем подмену, чтобы отработала настоящая проверка токена
    app.dependency_overrides.pop(get_current_user)
    try:
        response = client.post(
            "/shorten",
            json={"original_url": "https://google.com"}
            )
        assert response.status_code == 401
    finally:
        # finally обязателен: упавший assert иначе оставит подмену снятой,
        # и посыплются следующие тесты
        app.dependency_overrides[get_current_user] = lambda: "testuser"


def test_register_and_login():
    response = client.post(
        "/register",
        json={"username": "alice", "password": "secret123"}
        )
    assert response.status_code == 200

    response = client.post(
        # /login принимает форму, а не JSON — так требует OAuth2
        "/login",
        data={"username": "alice", "password": "secret123"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_rejects_duplicate():
    client.post(
        "/register",
        json={"username": "bob", "password": "secret123"}
        )
    response = client.post(
        "/register",
        json={"username": "bob", "password": "other-password"}
        )
    assert response.status_code == 409


def test_login_rejects_wrong_password():
    client.post(
        "/register",
        json={"username": "carol", "password": "secret123"}
        )
    response = client.post(
        "/login",
        data={"username": "carol", "password": "wrong-password"}
        )
    assert response.status_code == 401
