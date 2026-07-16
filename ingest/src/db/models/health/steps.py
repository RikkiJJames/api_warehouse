from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Steps(Base):
    # One row per day — Google Health API's dailyRollUp response nests each
    # point under civilStartTime {year, month, day}; flatten_record explodes
    # that into civil_start_time_year/month/day, which `date` below derives
    # a queryable column from (same pattern as trakt.watched_movies.trakt_movie_id).
    __tablename__ = "steps"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_steps_date"),
        {"schema": "health"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    civilStartTime_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    civilStartTime_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    civilStartTime_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date: Mapped[object | None] = mapped_column(
        Date,
        Computed(
            '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
            persisted=True,
        ),
        nullable=True,
    )
    steps_countSum: Mapped[int | None] = mapped_column(Integer, nullable=True)
