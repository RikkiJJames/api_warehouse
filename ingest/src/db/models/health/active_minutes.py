from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class ActiveMinutes(Base):
    # See health.steps for the civil_start_time -> date derivation pattern.
    #
    # activeMinutesRollupByActivityLevel is a list of per-activity-level
    # entries (e.g. LIGHT/MODERATE/VIGOROUS), not a single scalar, so it's
    # stored whole as JSONB rather than split into its own column — a dbt
    # staging model can sum activeMinutesSum across entries once the exact
    # field name is confirmed against a live payload (best-effort guess,
    # unverified — see total_calories.py for why).
    __tablename__ = "active_minutes"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_active_minutes_date"),
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
    activeMinutes_activeMinutesRollupByActivityLevel: Mapped[list | None] = mapped_column(
        JSONB, nullable=True
    )
