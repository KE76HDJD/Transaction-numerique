# V3 — Airflow (Orchestration)

## Qu'est-ce que cette version resout ?

V3 ajoute l'**orchestration automatique** du pipeline. Au lieu de lancer les commandes manuellement, un DAG Airflow enchaîne les tâches automatiquement.

### Ce que V3 ajoute par rapport a V2

| Avant (V2) | Apres (V3) |
|------------|------------|
| Lancement manuel des commandes | DAG automatique |
| Pas de retries | 2 retries automatiques |
| Pas de planning | Cron schedule possible |
| Pas de monitoring | UI Airflow pour suivre |

### Ce que V3 ne resout PAS

- Traitement temps reel → V4 (Kafka)
- Monitoring avance → V5

## Architecture du DAG

```
wait_for_source
      │
      ▼
  ingest_batch        ← Split CSV en 31 fichiers
      │
      ▼
transform_transactions ← step → timestamp
      │
      ▼
  load_postgresql      ← Charge en base
      │
      ▼
    dbt_run            ← stg → int → mart
      │
      ▼
   dbt_test            ← 23 tests
```

## Utilisation

### 1. Initialiser Airflow

```bash
# Activer le venv
source venv/bin/activate

# Initialiser la base de données Airflow
airflow db migrate

# Créer un utilisateur admin
airflow users create \
    --username admin \
    --firstname Kevin \
    --lastname Admin \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### 2. Lancer Airflow

```bash
# Terminal 1 : Scheduler
airflow scheduler

# Terminal 2 : Webserver (UI)
airflow webserver --port 8080
```

### 3. Accéder à l'UI

```
http://localhost:8080
Login: admin / admin
```

### 4. Tester le DAG

```bash
# Tester sans Airflow
airflow dags test transaction_pipeline

# Vérifier le DAG
airflow dags list
airflow dags show transaction_pipeline
```

### 5. Activer le DAG

Dans l'UI Airflow :
1. Trouver `transaction_pipeline`
2. Activer le toggle "Active"
3. Le DAG s'exécutera selon le schedule (ou manuellement)

## Fichiers

```
V3-airflow/
├── dags/
│   └── transaction_pipeline.py   # Le DAG
├── logs/                         # Logs Airflow
├── plugins/                      # Plugins custom
└── README.md
```

## Commandes utiles

```bash
# Voir les DAGs
airflow dags list

# Voir un DAG
airflow dags show transaction_pipeline

# Tester un DAG
airflow dags test transaction_pipeline

# Voir les tasks
airflow tasks list transaction_pipeline

# Exécuter une task
airflow tasks test transaction_pipeline ingest_batch
```
