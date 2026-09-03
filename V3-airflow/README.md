# V3 — Airflow (Orchestration Docker)

## Qu'est-ce que cette version resout ?

V3 ajoute l'**orchestration automatique** du pipeline avec Docker. Le DAG Airflow enchaîne les tâches : ingestion → transformation → load → dbt run → dbt test.

### Services Docker

| Service | Port | Rôle |
|---------|------|------|
| airflow-webserver | 8080 | UI Airflow |
| airflow-scheduler | - | Execute les DAGs |
| airflow-worker | - | Execute les tâches |
| airflow-triggerer | - | Gère les triggers |
| airflow-flower | 5555 | Monitoring Celery |
| postgres-airflow | 5433 | Metadata Airflow |
| redis | 6379 | Broker Celery |

## Démarrage

### 1. Build et démarrage

```bash
# Depuis la racine du projet
docker compose -f docker-compose.airflow.yml up -d --build

# Vérifier que tous les services tournent
docker compose -f docker-compose.airflow.yml ps
```

### 2. Accéder à l'UI

```
http://localhost:8080
Login: admin / admin
```

### 3. Trouver le DAG

Dans l'UI Airflow :
1. Chercher `transaction_pipeline`
2. Activer le toggle "Active"
3. Le DAG est prêt à être lancé

### 4. Lancer le pipeline

Dans l'UI :
- Cliquer sur `transaction_pipeline`
- Cliquer sur "▶ Trigger DAG"
- Suivre l'exécution en temps réel

Ou en ligne de commande :

```bash
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
    airflow dags trigger transaction_pipeline
```

## Commandes utiles

```bash
# Voir les logs
docker compose -f docker-compose.airflow.yml logs -f

# Voir les logs d'un service
docker compose -f docker-compose.airflow.yml logs -f airflow-scheduler

# Lister les DAGs
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
    airflow dags list

# Tester un DAG
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
    airflow dags test transaction_pipeline

# Arrêter
docker compose -f docker-compose.airflow.yml down

# Tout supprimer (y compris les données)
docker compose -f docker-compose.airflow.yml down -v
```

## Le DAG — 5 tâches

```
ingest_batch
      │  Split CSV → 31 fichiers
      ▼
transform_transactions
      │  step → timestamp, nettoyage
      ▼
  load_postgresql
      │  Charge 6.36M lignes
      ▼
    dbt_run
      │  stg → int → mart (SQL)
      ▼
   dbt_test
      │  23 tests qualite
      ▼
   ✓ TERMINE
```

## Fichiers

```
V3-airflow/
├── dags/
│   └── transaction_pipeline.py   # Le DAG
├── logs/                         # Logs Airflow
├── plugins/                      # Plugins
├── Dockerfile                    # Image custom
├── requirements.txt              # Deps Python
└── README.md

docker-compose.airflow.yml        # Config Docker
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  webserver   │  │  scheduler   │  │   worker     │  │
│  │  (UI :8080)  │  │              │  │  (Celery)    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  postgres    │  │    redis     │  │   flower     │  │
│  │  (metadata)  │  │  (broker)    │  │  (monitor)   │  │
│  │  :5433       │  │  :6379       │  │  :5555       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        │
                        │ host.docker.internal
                        ▼
              ┌──────────────────┐
              │   PostgreSQL     │
              │   (transaction)  │
              │   :5434          │
              └──────────────────┘
```
