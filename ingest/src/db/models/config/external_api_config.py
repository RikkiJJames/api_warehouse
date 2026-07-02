from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from src.db.core.db import Base
from datetime import datetime, timezone


class ApiConfig(Base):
    __tablename__ = "api_config"
    __table_args__ = ({"schema": "config"},)

    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, ForeignKey("config.apis.id"), nullable=False)
    parameter_name = Column(String, nullable=False)
    parameter_value = Column(String, nullable=False)
    valid_from = Column(DateTime, default=datetime.now(timezone.utc))
    valid_to = Column(DateTime, default=datetime.max.replace(tzinfo=timezone.utc))
    is_current = Column(Boolean, default=True)
