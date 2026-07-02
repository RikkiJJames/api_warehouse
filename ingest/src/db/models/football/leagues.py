from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Leagues(Base):
    __tablename__ = "leagues"
    __table_args__ = (
        UniqueConstraint("league_id", name="uq_league_id"),
        {"schema": "football"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    league_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    league_name: Mapped[str | None] = mapped_column(String, nullable=True)
    league_type: Mapped[str | None] = mapped_column(String, nullable=True)
    league_logo: Mapped[str | None] = mapped_column(String, nullable=True)
    country_name: Mapped[str | None] = mapped_column(String, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String, nullable=True)
    country_flag: Mapped[str | None] = mapped_column(String, nullable=True)
