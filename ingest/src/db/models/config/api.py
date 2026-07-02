from sqlalchemy import Identity, ForeignKey, UniqueConstraint
from src.db.core.db import Base
from sqlalchemy.orm import Mapped, mapped_column


class Api(Base):
    __tablename__ = "api"
    __table_args__ = {"schema": "config"}
    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    base_url: Mapped[str] = mapped_column(unique=True, nullable=False)


class ApiConfig(Base):
    __tablename__ = "api_config"
    __table_args__ = (
        UniqueConstraint("api_id", "parameter_name", name="uq_api_config_api_param"),
        {"schema": "config"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("config.api.id"))
    parameter_name: Mapped[str] = mapped_column(nullable=False)
    parameter_value: Mapped[str] = mapped_column(nullable=False)
