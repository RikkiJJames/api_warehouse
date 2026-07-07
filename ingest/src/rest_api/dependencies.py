import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = create_engine(
    (
        f"postgresql://{os.getenv('DB_USER', '')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', '')}:{os.getenv('DB_PORT', '')}/{os.getenv('DB_NAME', '')}"
    ),
    connect_args={"sslmode": "require"},
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
