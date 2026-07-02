from sqlalchemy import ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Seasons(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("year", name="uq_season_year"),
        {"schema": "football"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

