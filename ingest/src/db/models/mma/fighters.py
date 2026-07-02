from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Fighters(Base):
    __tablename__ = "fighters"
    __table_args__ = (
        UniqueConstraint("fighter_id", "category", name="uq_fighter_id_category"),
        {"schema": "mma"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    fighter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String, nullable=True)
    photo: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    birth_date: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[str | None] = mapped_column(String, nullable=True)
    weight: Mapped[str | None] = mapped_column(String, nullable=True)
    reach: Mapped[str | None] = mapped_column(String, nullable=True)
    stance: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_update: Mapped[str | None] = mapped_column(String, nullable=True)
