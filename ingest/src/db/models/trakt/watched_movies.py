from datetime import datetime

from sqlalchemy import BigInteger, Computed, DateTime, Float, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class WatchedMovies(Base):
    __tablename__ = "watched_movies"
    __table_args__ = (
        UniqueConstraint("history_id", name="uq_trakt_watched_movies_history_id"),
        {"schema": "trakt"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    history_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    watched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action: Mapped[str | None] = mapped_column(String, nullable=True)

    movie_title: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movie_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # movie_details's path_id param queries this directly against the raw
    # table (dbt's staging layer already extracts the same value, but that
    # alias doesn't exist here) — same pattern as recent_tracks.listened_at.
    trakt_movie_id: Mapped[int | None] = mapped_column(
        Integer, Computed("(movie_ids->>'trakt')::integer", persisted=True), nullable=True
    )
    movie_tagline: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_overview: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_released: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_runtime: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movie_country: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_trailer: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_homepage: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_status: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    movie_votes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movie_language: Mapped[str | None] = mapped_column(String, nullable=True)
    movie_genres: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    movie_certification: Mapped[str | None] = mapped_column(String, nullable=True)

    my_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    my_rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
