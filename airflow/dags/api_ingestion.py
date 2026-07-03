from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("neon_db")

with DAG(
    dag_id="api_ingestion_docker",
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(hours=1),
    catchup=False,
) as dag:

    # All api credentials (client_id/secret/redirect_url/refresh_token/api_key)
    # are !env_optional in the pipeline config and already seeded in
    # config.api_config from an earlier local run — the container reads them
    # from the DB, so only the DB connection itself needs to be supplied here.
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