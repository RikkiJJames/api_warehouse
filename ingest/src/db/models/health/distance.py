from sqlalchemy import Computed, Date, ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
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
    distance_metersSum: Mapped[int | None] = mapped_column(Integer, nullable=True)
