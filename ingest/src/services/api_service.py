from contextlib import contextmanager
from src.db.core.db import Database
from src.db.repositories.api_repository import ApiRepository
import src.db.models  # noqa: F401 — registers all models with Base.metadata before create_all


class ApiService:
    def __init__(self, repository: ApiRepository):
        self.repository = repository


@contextmanager
def get_service():
    db = Database()
    db.connect()
    session = db.get_session()

    repo = ApiRepository(session)
    service = ApiService(repo)

    try:
        yield service
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        db.disconnect()
