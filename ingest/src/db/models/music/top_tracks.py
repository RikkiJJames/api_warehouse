from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class TopTracks(Base):
    __tablename__ = "top_tracks"
    __table_args__ = (
        UniqueConstraint("name", "artist_name", "date_added", name="uq_top_track_snapshot"),
        {"schema": "music"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    playcount: Mapped[str | None] = mapped_column(String, nullable=True)
    mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_name: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_url: Mapped[str | None] = mapped_column(String, nullable=True)
    date_added: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=True
    )
