from sqlalchemy import Computed, Date, Float, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class TotalCalories(Base):
    # See health.steps for the civil_start_time -> date derivation pattern.
    #
    # totalCalories_kcalSum is a best-effort guess at the response's field
    # name (proto3 JSON camelCase of TotalCaloriesRollupValue.kcal_sum) —
    # unverified against a live payload since that needs real credentials.
    # If it comes back always-NULL once ingestion is running, check the raw
    # response shape and rename this column to match.
    __tablename__ = "total_calories"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_total_calories_date"),
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
    totalCalories_kcalSum: Mapped[float | None] = mapped_column(Float, nullable=True)
