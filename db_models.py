from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db_connecting import Base
from sqlalchemy import ForeignKey


class Link(Base):
    __tablename__ = "links"
    # Пустой owner — у ссылок, созданных до появления авторизации.
    # Индекс — под фильтр по владельцу в /my/links
    owner: Mapped[str | None] = mapped_column(
        ForeignKey("users.username"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    clicks: Mapped[int] = mapped_column(default=0)


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(primary_key=True)
    password_hash: Mapped[str]
