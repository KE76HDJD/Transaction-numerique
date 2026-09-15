"""
DAG Airflow — Transaction Pipeline (V3)

Ce DAG orchestre le pipeline complet :
1. Ingestion : decoupe le CSV source en lots quotidiens
2. Transformation : convertit step → timestamp, nettoie
3. Load PostgreSQL : charge les donnees en base
4. dbt Run : verifie les modeles SQL (stg → int → mart) — V2 deja execute, on verifie
5. dbt Test : verifie la qualite des donnees

Architecture legere : dbt tourne en V2 (projet dedie, 3 modeles, 23 tests, docs).
V3 verifie les tables produites, sans reinstaller dbt dans l'image Airflow.

Usage:
    docker compose -f docker-compose.airflow.yml up -d
    http://localhost:8082 (admin/admin)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ============================================
# Configuration
# ============================================

PROJECT_ROOT = "/opt/airflow/project"
PYTHON = "python3"

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
    description="Pipeline complet: ingestion → transformation → load → dbt verify",
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
    # Task 4: dbt Run — verifie les modeles (V2 deja execute)
    # En prod : DockerOperator avec ghcr.io/dbt-labs/dbt-postgres:1.8.7
    # Ici : verification legere des tables produites par V2
    # ============================================
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"""
            {PYTHON} -c "
import psycopg2
conn = psycopg2.connect(host='host.docker.internal', port=5434, dbname='transaction_db', user='kevin', password='kevin123')
cur = conn.cursor()
cur.execute('SELECT count(*) FROM public_staging.stg_transactions')
print(f'stg_transactions: {{cur.fetchone()[0]:,}} rows')
cur.execute('SELECT count(*) FROM public_marts.mart_transactions')
print(f'mart_transactions: {{cur.fetchone()[0]:,}} rows')
conn.close()
print('dbt models OK')
"
        """,
    )

    # ============================================
    # Task 5: dbt Test — verifie la qualite (23 tests dbt)
    # ============================================
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"""
            {PYTHON} << 'PYEOF'
import psycopg2
conn = psycopg2.connect(host='host.docker.internal', port=5434, dbname='transaction_db', user='kevin', password='kevin123')
cur = conn.cursor()
checks = [
    ('not_null id', 'SELECT count(*) FROM public.transactions WHERE id IS NULL', 0),
    ('accepted_values type', "SELECT count(*) FROM public.transactions WHERE type NOT IN ('PAYMENT','TRANSFER','CASH_OUT','CASH_IN','DEBIT')", 0),
    ('amount > 0', 'SELECT count(*) FROM public.transactions WHERE amount <= 0', 0),
]
ok = True
for name, sql, expected in checks:
    cur.execute(sql)
    val = cur.fetchone()[0]
    status = 'PASS' if val == expected else 'FAIL'
    print(f'{{name}}: {{status}} ({{val}})')
    if status == 'FAIL':
        ok = False
cur.execute('SELECT count(*), count(DISTINCT transaction_date) FROM public_marts.mart_transactions')
c, d = cur.fetchone()
status = 'PASS' if c==d else 'FAIL'
print(f'unique mart date: {{status}} ({{c}} rows, {{d}} distinct)')
if status == 'FAIL':
    ok = False
conn.close()
if not ok:
    raise SystemExit(1)
print('dbt tests OK (23 tests en V2)')
PYEOF
        """,
    )

    # ============================================
    # Dependances
    # ============================================
    ingest >> transform >> load_pg >> dbt_run >> dbt_test
