import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from ...config.logs.logging_config import *
import logging

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

Base = declarative_base()


class Database:
    def __init__(self, config=None):
        self.config = config
        self.engine = None

    def connect(self):
        try:
            config = {
                "host": os.getenv("DB_HOST", ""),
                "database": os.getenv("DB_NAME", ""),
                "user": os.getenv("DB_USER", ""),
                "password": os.getenv("DB_PASSWORD", ""),
                "port": os.getenv("DB_PORT", ""),
            }
            self.engine = create_engine(
                f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
            )
            logger.info("Database connection established.")

            with self.engine.begin() as conn:
                schemas = {t.schema for t in Base.metadata.tables.values() if t.schema}
                for schema in schemas:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            Base.metadata.create_all(self.engine)
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            raise

    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed.")

    def get_session(self) -> Session:
        if not self.engine:
            raise Exception("Database connection is not established.")
        Session = sessionmaker(bind=self.engine)
        return Session()

    def execute_query(self, query, params=None):
        if not self.engine:
            raise Exception("Database connection is not established.")

        with self.get_session() as session:
            if query.strip().upper().startswith("DROP") or query.strip().upper().startswith("TRUNCATE"):
                print("Cannot execute those queries")
                return
            result = session.execute(text(query), params)
            if query.strip().upper().startswith("SELECT"):
                return result.fetchall()
            else:
                session.commit()
                logger.info("Query executed and changes committed.")