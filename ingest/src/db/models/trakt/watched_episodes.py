from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class WatchedEpisodes(Base):
    __tablename__ = "watched_episodes"
    __table_args__ = (
        UniqueConstraint("history_id", name="uq_trakt_watched_episodes_history_id"),
        {"schema": "trakt"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    history_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    watched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action: Mapped[str | None] = mapped_column(String, nullable=True)

    episode_season: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_number_abs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_title: Mapped[str | None] = mapped_column(String, nullable=True)
    episode_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    episode_overview: Mapped[str | None] = mapped_column(String, nullable=True)
    episode_runtime: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    episode_first_aired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    show_title: Mapped[str | None] = mapped_column(String, nullable=True)
    show_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    show_overview: Mapped[str | None] = mapped_column(String, nullable=True)
    show_network: Mapped[str | None] = mapped_column(String, nullable=True)
    show_status: Mapped[str | None] = mapped_column(String, nullable=True)
    show_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    show_homepage: Mapped[str | None] = mapped_column(String, nullable=True)
    show_runtime: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_genres: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    show_country: Mapped[str | None] = mapped_column(String, nullable=True)
    show_certification: Mapped[str | None] = mapped_column(String, nullable=True)
    show_first_aired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    show_aired_episodes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_airs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    show_images: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    show_my_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    show_my_rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
