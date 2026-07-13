from sqlalchemy import ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class MovieDetails(Base):
    # One row per unique movie (not per watch event) — Trakt's watch-history
    # endpoints no longer include image data, so posters have to come from a
    # dedicated per-movie detail lookup (GET /movies/{id}) instead.
    __tablename__ = "movie_details"
    __table_args__ = (
        UniqueConstraint("ids_trakt", name="uq_trakt_movie_details_ids_trakt"),
        {"schema": "trakt"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    # Named ids_trakt (not trakt_movie_id) to match flatten_record's natural
    # output: the bare "ids": {"trakt": ...} object at the response root
    # flattens to "ids_trakt", since there's no wrapping "movie" key here
    # unlike the history endpoints.
    ids_trakt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    images: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
