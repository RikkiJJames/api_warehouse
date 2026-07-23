from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Distance(Base):
    # See health.steps for the civil_start_time -> date derivation pattern.
    #
    # DistanceRollupValue's only field is millimetersSum (confirmed against
    # https://developers.google.com/health/reference/rest/v4/DistanceRollupValue),
    # not metersSum — flatten_record produces "distance_millimetersSum", so a
    # metersSum-named column here would silently stay NULL forever (no error,
    # since _build_row just drops any flattened key it doesn't recognize).
    # stg_distance.sql converts to meters for the mart layer.
    __tablename__ = "distance"
    __table_args__ = (
        UniqueConstraint("date", name="uq_health_distance_date"),
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
    distance_millimetersSum: Mapped[int | None] = mapped_column(Integer, nullable=True)
