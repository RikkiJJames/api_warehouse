from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Countries(Base):
    __tablename__ = "countries"
    __table_args__ = (
        UniqueConstraint("code", name="uq_country_code"),
        {"schema": "football"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str | None] = mapped_column(String, nullable=True)
    flag: Mapped[str | None] = mapped_column(String, nullable=True)
