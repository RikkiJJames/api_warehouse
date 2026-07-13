from sqlalchemy import ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class ShowDetails(Base):
    # One row per unique show (not per watched episode) — see movie_details.py
    # for why this needs its own per-show detail lookup (GET /shows/{id}).
    __tablename__ = "show_details"
    __table_args__ = (
        UniqueConstraint("ids_trakt", name="uq_trakt_show_details_ids_trakt"),
        {"schema": "trakt"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    ids_trakt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    images: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
