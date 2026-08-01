from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from sqlalchemy import ForeignKey


class Link(Base):
    __tablename__ = "links"
    owner: Mapped[str | None] = mapped_column(ForeignKey("users.username"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    clicks: Mapped[int] = mapped_column(default=0)


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(primary_key=True)
    password_hash: Mapped[str]
