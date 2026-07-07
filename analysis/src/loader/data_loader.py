from ingest.src.db.core.db import Database
import pandas as pd
from pathlib import Path
from .sql_loader import SQLLoader
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

SRC_PATH = Path(__file__).parents[1]
SQL_PATH = SRC_PATH / "sql"

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
