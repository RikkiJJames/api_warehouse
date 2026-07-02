from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class TopArtists(Base):
    __tablename__ = "top_artists"
    __table_args__ = (
        UniqueConstraint("name", "date_added", name="uq_top_artist_snapshot"),
        {"schema": "music"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    playcount: Mapped[str | None] = mapped_column(String, nullable=True)
    listeners: Mapped[str | None] = mapped_column(String, nullable=True)
    mbid: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    date_added: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=True
    )
