from pydantic import BaseModel, HttpUrl


class RegisterRequest(BaseModel):
    username: str
    password: str


class ShortenRequest(BaseModel):
    original_url: HttpUrl


class ShortenResponse(BaseModel):
    code: str
    short_url: str
