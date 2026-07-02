from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class WatchlistShows(Base):
    __tablename__ = "watchlist_shows"
    __table_args__ = (
        UniqueConstraint("watchlist_id", name="uq_trakt_watchlist_shows_watchlist_id"),
        {"schema": "trakt"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    watchlist_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    show_title: Mapped[str | None] = mapped_column(String, nullable=True)
    show_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
