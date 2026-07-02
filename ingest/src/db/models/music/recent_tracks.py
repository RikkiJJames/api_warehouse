from datetime import datetime

from sqlalchemy import Computed, DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class RecentTracks(Base):
    __tablename__ = "recent_tracks"
    __table_args__ = (
        UniqueConstraint("artist_name", "name", "date_uts", name="uq_recent_track"),
        {"schema": "music"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_name: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    album_name: Mapped[str | None] = mapped_column(String, nullable=True)
    album_mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    date_uts: Mapped[str | None] = mapped_column(String, nullable=True)
    date_name: Mapped[str | None] = mapped_column(String, nullable=True)
    listened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        Computed("to_timestamp(date_uts::integer)", persisted=True),
        nullable=True,
    )
