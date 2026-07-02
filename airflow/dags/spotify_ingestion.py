  GNU nano 4.8                                 dags/spotify_ingestion.py
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("neondb")

with DAG(
    dag_id="api_ingestion_docker",
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(hours=1, minutes=30),
    catchup=False,
) as dag:

    run_ingestion = DockerOperator(
        task_id="run_ingestion_container",
        image="rikkijames/ingestion-app:latest",
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
        image="rikkijames/api_warehouse:latest",
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