import pandas as pd
from pathlib import Path

class SQLLoader:
    """
    A class to load SQL queries from files.
    """

    def __init__(self, sql_path: Path):
        self.sql_path = sql_path

    def get_sql_query(self, file_dir: str | Path) -> list[Path]:
        """
        Reads a SQL file and returns the query as a string.
        """
        search_dir = Path(file_dir)
        if not search_dir.is_absolute():
            search_dir = self.sql_path / search_dir

        return sorted(search_dir.rglob("*.sql"))

    def read_sql_file(self, file_path: Path) -> str:
        """
        Reads a SQL file and returns the query as a string.
        """
        with open(file_path, "r") as f:
            query = f.read()

        return query


