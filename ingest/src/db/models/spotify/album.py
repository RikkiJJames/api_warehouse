from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class SpotifyAlbum(Base):
    __tablename__ = "album"
    __table_args__ = (
        UniqueConstraint("album_id", name="uq_spotify_album"),
        {"schema": "spotify"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    album_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    uri: Mapped[str | None] = mapped_column(String, nullable=True)
    release_date: Mapped[str | None] = mapped_column(String, nullable=True)
    total_tracks: Mapped[int | None] = mapped_column(Integer, nullable=True)
