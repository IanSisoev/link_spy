from fastapi.testclient import TestClient
from main import app, get_store, MemoryStore, generate_code


memory = MemoryStore()
app.dependency_overrides[get_store] = lambda: memory

client = TestClient(app)


def test_create_and_redirect():
    response = client.post("/shorten", json={"original_url": "https://google.com"})
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
