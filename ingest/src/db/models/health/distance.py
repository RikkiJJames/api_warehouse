from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Distance(Base):
    # See health.steps for the civil_start_time -> date derivation pattern.
    __tablename__ = "distance"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_distance_date"),
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
    distance_metersSum: Mapped[int | None] = mapped_column(Integer, nullable=True)
