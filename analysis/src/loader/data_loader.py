from ingest.src.db.core.db import Database
import pandas as pd
import threading
import time
from pathlib import Path
from .sql_loader import SQLLoader
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

SRC_PATH = Path(__file__).parents[1]
SQL_PATH = SRC_PATH / "sql"

# `marimo run` gives every browser session its own kernel, so without this
# each visitor (and every page refresh) re-ran every query even though the
# warehouse only refreshes every couple of hours. Module-level, so it's
# shared by every session in the server process; results expire after the
# TTL so a fresh dbt run shows up without a redeploy.
CACHE_TTL_SECONDS = 15 * 60
_cache: dict[Path, tuple[float, pd.DataFrame]] = {}
_cache_locks: dict[Path, threading.Lock] = {}
_cache_locks_guard = threading.Lock()

class DataLoader:
    """
    A class to load data from SQL queries.
    """

    def __init__(self):
        self.sql_loader: SQLLoader = SQLLoader(sql_path=SQL_PATH)
        self.db: Database = Database()

    def load_data(self, file_dir: str) -> dict[str, pd.DataFrame]:
        """
        Loads data from a SQL query and returns it as a pandas DataFrame.
        """
        self.db.connect()
        data: dict[str, pd.DataFrame] = {}

        sql_file_paths = self.sql_loader.get_sql_query(file_dir)
        if not sql_file_paths:
            raise FileNotFoundError(f"No SQL files found in directory: {file_dir}")
        
        for sql_file_path in sql_file_paths:
            query = self.sql_loader.read_sql_file(sql_file_path)
            result = self.db.execute_query(query)
            data[sql_file_path.stem] = pd.DataFrame(result)

        return data

    def load_file(self, sql_file_path: Path) -> pd.DataFrame:
        """
        Runs a single SQL file and returns the result as a pandas DataFrame,
        served from the shared cache while it's younger than CACHE_TTL_SECONDS.
        """
        with _cache_locks_guard:
            lock = _cache_locks.setdefault(sql_file_path, threading.Lock())

        # Per-file lock: sessions that miss at the same time wait for one
        # query instead of each running their own.
        with lock:
            cached = _cache.get(sql_file_path)
            if cached is None or time.monotonic() - cached[0] > CACHE_TTL_SECONDS:
                if self.db.engine is None:
                    self.db.connect()
                query = self.sql_loader.read_sql_file(sql_file_path)
                cached = (time.monotonic(), pd.DataFrame(self.db.execute_query(query)))
                _cache[sql_file_path] = cached

        # A copy per caller — notebook cells modify their frames in place
        # (e.g. converting date columns), which mustn't leak across sessions.
        return cached[1].copy()
