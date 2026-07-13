import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = create_engine(
    (
        f"postgresql://{os.getenv('DB_USER', '')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', '')}:{os.getenv('DB_PORT', '')}/{os.getenv('DB_NAME', '')}"
    ),
    # Connects to the cloudsql-proxy sidecar over loopback, which already
    # tunnels to Cloud SQL over TLS+IAM — requiring SSL again here breaks it.
    connect_args={"sslmode": "disable"},
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
