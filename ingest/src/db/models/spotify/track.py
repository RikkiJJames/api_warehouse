from sqlalchemy import Boolean, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class SpotifyTrack(Base):
    __tablename__ = "track"
    __table_args__ = (
        UniqueConstraint("track_id", name="uq_spotify_track"),
        {"schema": "spotify"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    track_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explicit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    uri: Mapped[str | None] = mapped_column(String, nullable=True)
    popularity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    album_id: Mapped[str | None] = mapped_column(String, nullable=True)
    artist_id: Mapped[str | None] = mapped_column(String, nullable=True)
