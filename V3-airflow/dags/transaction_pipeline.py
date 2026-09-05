"""
DAG Airflow — Transaction Pipeline (V3)

Ce DAG orchestre le pipeline complet :
1. Ingestion : decoupe le CSV source en lots quotidiens
2. Transformation : convertit step → timestamp, nettoie
3. Load PostgreSQL : charge les donnees en base
4. dbt Run : execute les modeles SQL (stg → int → mart)
5. dbt Test : verifie la qualite des donnees

Usage:
    docker compose -f docker-compose.airflow.yml up -d
    http://localhost:8080 (admin/admin)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ============================================
# Configuration
# ============================================

PROJECT_ROOT = "/opt/airflow/project"
PYTHON = "/opt/airflow/project/venv/bin/python"

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
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transaction", "pipeline", "v3"],
) as dag:

    # ============================================
    # Task 1: Ingestion — split CSV → lots quotidiens
    # ============================================
    ingest = BashOperator(
        task_id="ingest_batch",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m V1-batch.src.ingestion.ingest_batch",
    )

    # ============================================
    # Task 2: Transformation — step → timestamp
    # ============================================
    transform = BashOperator(
        task_id="transform_transactions",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m V1-batch.src.transformation.transform_transactions",
    )

    # ============================================
    # Task 3: Load PostgreSQL — charge les 31 fichiers
    # ============================================
    load_pg = BashOperator(
        task_id="load_postgresql",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m V1-batch.src.utils.database",
    )

    # ============================================
    # Task 4: dbt Run — execute les modeles SQL
    # ============================================
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_ROOT}/V2-dbt && {PYTHON} -m dbt run --profiles-dir . --project-dir .",
    )

    # ============================================
    # Task 5: dbt Test — verifie la qualite
    # ============================================
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_ROOT}/V2-dbt && {PYTHON} -m dbt test --profiles-dir . --project-dir .",
    )

    # ============================================
    # Dependances
    # ============================================
    ingest >> transform >> load_pg >> dbt_run >> dbt_test
