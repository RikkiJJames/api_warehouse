from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class ReadBooks(Base):
    __tablename__ = "read_books"
    __table_args__ = (
        UniqueConstraint("user_book_id", name="uq_hardcover_read_books_user_book_id"),
        {"schema": "hardcover"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    user_book_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    my_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    book_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    book_title: Mapped[str | None] = mapped_column(String, nullable=True)
    book_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    book_release_date: Mapped[str | None] = mapped_column(String, nullable=True)
    book_image: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    read_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
