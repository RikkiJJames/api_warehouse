from sqlalchemy import ForeignKey, Identity, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core.db import Base


class Categories(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("api_id", "category_name", name="uq_categories_api_category"),
        {"schema": "mma"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("config.api.id"), nullable=True
    )
    category_name: Mapped[str] = mapped_column()
