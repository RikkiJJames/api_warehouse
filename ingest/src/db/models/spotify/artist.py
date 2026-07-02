from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class SpotifyArtist(Base):
    __tablename__ = "artist"
    __table_args__ = (
        UniqueConstraint("artist_id", name="uq_spotify_artist"),
        {"schema": "spotify"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    artist_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    uri: Mapped[str | None] = mapped_column(String, nullable=True)
