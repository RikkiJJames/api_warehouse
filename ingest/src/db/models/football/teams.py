from sqlalchemy import Boolean, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Teams(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season"),
        {"schema": "football"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    season: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_name: Mapped[str | None] = mapped_column(String, nullable=True)
    team_code: Mapped[str | None] = mapped_column(String, nullable=True)
    team_country: Mapped[str | None] = mapped_column(String, nullable=True)
    team_founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_national: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    team_logo: Mapped[str | None] = mapped_column(String, nullable=True)
    venue_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
