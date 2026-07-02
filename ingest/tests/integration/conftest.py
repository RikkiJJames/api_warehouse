import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.db.core.db import Base, DATABASE_CONFIG

import src.db.models  # noqa: F401 — registers all models with Base.metadata


def _build_url(cfg: dict) -> str | None:
    if not all(cfg.get(k) for k in ("host", "database", "user", "password", "port")):
        return None
    return (
        f"postgresql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )


@pytest.fixture(scope="session")
def db_engine():
    url = _build_url(DATABASE_CONFIG)
    if not url:
        pytest.skip("DB connection params not set — skipping integration tests")

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS config"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS mma"))
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS config CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS mma CASCADE"))
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    with db_engine.begin() as conn:
        conn.execute(text("TRUNCATE config.endpoint_params CASCADE"))
        conn.execute(text("TRUNCATE config.endpoints CASCADE"))
        conn.execute(text("TRUNCATE config.api_config CASCADE"))
        conn.execute(text("TRUNCATE config.api CASCADE"))
        conn.execute(text("TRUNCATE mma.categories CASCADE"))
        conn.execute(text("TRUNCATE mma.fighters CASCADE"))
        conn.execute(text("TRUNCATE mma.fighter_records CASCADE"))
    session.close()
