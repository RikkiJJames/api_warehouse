from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Steps(Base):
    # One row per day — Google Health API's dailyRollUp response nests each
    # point under civilStartTime, a CivilDateTime ({date: {year,month,day},
    # time: <optional>}), not a bare {year,month,day}; flatten_record's one
    # level of flattening turns that into civilStartTime_date (a nested
    # {year,month,day} dict), which `date` below derives a queryable column
    # from (same pattern as trakt.watched_movies.trakt_movie_id).
    __tablename__ = "steps"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_steps_date"),
        {"schema": "health"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("config.api.id"), nullable=True)
    civilStartTime_date: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    date: Mapped[object | None] = mapped_column(
        Date,
        Computed(
            "(make_date("
            "(\"civilStartTime_date\"->>'year')::int, "
            "(\"civilStartTime_date\"->>'month')::int, "
            "(\"civilStartTime_date\"->>'day')::int"
            "))",
            persisted=True,
        ),
        nullable=True,
    )
    steps_countSum: Mapped[int | None] = mapped_column(Integer, nullable=True)
