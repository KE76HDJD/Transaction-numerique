"""
DAG Airflow — Transaction Pipeline (V3)

Ce DAG orchestre le pipeline complet :
1. Sensor : detecte les nouveaux fichiers CSV
2. Ingestion : decoupe le CSV source en lots quotidiens
3. Transformation : convertit step → timestamp, nettoie
4. Load PostgreSQL : charge les donnees en base
5. dbt Run : execute les modeles SQL (stg → int → mart)
6. dbt Test : verifie la qualite des donnees

Usage :
    airflow dags test transaction_pipeline
    airflow dags list
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.sensors.filesystem import FileSensor

# ============================================
# Configuration
# ============================================

PROJECT_ROOT = "/home/kevin/Transaction_numerique"
VENV_PYTHON = f"{PROJECT_ROOT}/venv/bin/python"
DBT_DIR = f"{PROJECT_ROOT}/V2-dbt"

default_args = {
    "owner": "kevin",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

# ============================================
# DAG Definition
# ============================================

with DAG(
    dag_id="transaction_pipeline",
    default_args=default_args,
    description="Pipeline complet: ingestion → transformation → load → dbt",
    schedule=None,  # Manuel ou cron: "@daily"
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transaction", "pipeline", "v3"],
) as dag:

    # ============================================
    # Task 1: Sensor — detecte le fichier source
    # ============================================
    wait_for_source = FileSensor(
        task_id="wait_for_source_file",
        filepath=f"{PROJECT_ROOT}/data/source/PS_20174392719_1491204439457_log.csv",
        poke_interval=30,
        timeout=300,
    )

    # ============================================
    # Task 2: Ingestion — split CSV → lots quotidiens
    # ============================================
    ingest = BashOperator(
        task_id="ingest_batch",
        bash_command=f"cd {PROJECT_ROOT} && {VENV_PYTHON} -m V1-batch.src.ingestion.ingest_batch",
    )

    # ============================================
    # Task 3: Transformation — step → timestamp
    # ============================================
    transform = BashOperator(
        task_id="transform_transactions",
        bash_command=f"cd {PROJECT_ROOT} && {VENV_PYTHON} -m V1-batch.src.transformation.transform_transactions",
    )

    # ============================================
    # Task 4: Load PostgreSQL — charge les 31 fichiers
    # ============================================
    load_pg = BashOperator(
        task_id="load_postgresql",
        bash_command=f"cd {PROJECT_ROOT} && {VENV_PYTHON} -m V1-batch.src.utils.database",
    )

    # ============================================
    # Task 5: dbt Run — execute les modeles SQL
    # ============================================
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && {VENV_PYTHON} -m dbt run --profiles-dir {DBT_DIR} --project-dir {DBT_DIR}",
    )

    # ============================================
    # Task 6: dbt Test — verifie la qualite
    # ============================================
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && {VENV_PYTHON} -m dbt test --profiles-dir {DBT_DIR} --project-dir {DBT_DIR}",
    )

    # ============================================
    # Dependances
    # ============================================
    wait_for_source >> ingest >> transform >> load_pg >> dbt_run >> dbt_test
