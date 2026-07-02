from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
from airflow.hooks.base import BaseHook
from airflow.models import Variable

conn = BaseHook.get_connection("neondb")

with DAG(
    dag_id="api_ingestion_docker",
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(hours=1, minutes=30),
    catchup=False,
) as dag:

    run_ingestion = DockerOperator(
        task_id="run_ingestion_container",
        image="rikkijames/api-warehouse-ingest:latest",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove="success",
        environment={
            "DB_HOST": conn.host,
            "DB_PORT": str(conn.port),
            "DB_USER": conn.login,
            "DB_PASSWORD": conn.password,
            "DB_NAME": conn.schema,
            "TRAKT_CLIENT_ID": Variable.get("TRAKT_CLIENT_ID"),
            "TRAKT_CLIENT_SECRET": Variable.get("TRAKT_CLIENT_SECRET"),
            "TRAKT_REFRESH_TOKEN": Variable.get("TRAKT_REFRESH_TOKEN"),
            "TRAKT_REDIRECT_URL": Variable.get("TRAKT_REDIRECT_URL"),
        },
        command="uv run python main.py",
    )

    run_dbt = DockerOperator(
        task_id="run_dbt",
        image="rikkijames/api-warehouse-dbt:latest",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove="success",
        environment={
            "DB_HOST": conn.host,
            "DB_PORT": str(conn.port),
            "DB_USER": conn.login,
            "DB_PASSWORD": conn.password,
            "DB_NAME": conn.schema,
        },
        command="dbt build --profiles-dir .",
    )

    run_ingestion >> run_dbt