from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class FighterRecords(Base):
    __tablename__ = "fighter_records"
    __table_args__ = (
        UniqueConstraint("fighter_id", name="uq_fighter_records_fighter_id"),
        {"schema": "mma"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    fighter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fighter_name: Mapped[str | None] = mapped_column(String, nullable=True)
    fighter_photo: Mapped[str | None] = mapped_column(String, nullable=True)
    total_win: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_loss: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_draw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ko_win: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ko_loss: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_win: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_loss: Mapped[int | None] = mapped_column(Integer, nullable=True)
