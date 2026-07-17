from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class RecentlyPlayed(Base):
    __tablename__ = "recently_played"
    __table_args__ = (
        UniqueConstraint("track_id", "played_at", name="uq_recently_played"),
        {"schema": "spotify"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    track_id: Mapped[str | None] = mapped_column(String, nullable=True)
    track_uri: Mapped[str | None] = mapped_column(String, nullable=True)
