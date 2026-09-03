# Plan Directeur — 5 Versions du Projet

## Transaction Data Platform

---

## 1. Vision globale

Ce projet construit un pipeline de données à travers **5 architectures successives**, pour comprendre **pourquoi** chaque brique du data engineering existe.

```
V1 (Batch)          ──►  V2 (dbt)           ──►  V3 (Airflow)
Python + PostgreSQL       SQL models + tests       Orchestration DAG
         │                        │                        │
         └────────────────────────┴────────────────────────┘
                                        │
                         V4 (Kafka)     ──►  V5 (Quality)
                         Streaming temps reel  Monitoring + alertes
```

---

## 2. Arborescence du projet

```
Transaction_numerique/
│
├── V1-batch/                            # V1 : Pipeline batch
│   ├── src/
│   │   ├── ingestion/
│   │   │   └── ingest_batch.py         # Split CSV → lots quotidiens
│   │   ├── transformation/
│   │   │   └── transform_transactions.py  # step → timestamp (Python)
│   │   └── utils/
│   │       └── database.py             # Load PostgreSQL
│   ├── sql/
│   │   └── create_tables.sql           # Schema staging
│   ├── tests/
│   │   ├── test_ingest_batch.py
│   │   ├── test_transform_transactions.py
│   │   └── test_database.py
│   └── README.md
│
├── V2-dbt/                              # V2 : Transformation dbt
│   ├── models/
│   │   ├── staging/
│   │   │   ├── _sources.yml            # Definition des sources
│   │   │   └── stg_transactions.sql    # Nettoyage
│   │   ├── intermediate/
│   │   │   └── int_daily_agg.sql       # Agregation quotidienne
│   │   └── marts/
│   │       └── mart_transactions.sql   # Business-ready
│   ├── tests/
│   │   └── schema.yml                  # Tests (not_null, unique, etc.)
│   ├── dbt_project.yml                 # Config dbt
│   ├── profiles.yml                    # Connexion PostgreSQL
│   └── README.md
│
├── V3-airflow/                          # V3 : Orchestration
│   ├── dags/
│   │   └── transaction_pipeline.py     # DAG Airflow
│   ├── plugins/                         # Plugins custom
│   └── README.md
│
├── V4-kafka/                            # V4 : Streaming
│   ├── producer/
│   │   └── kafka_producer.py           # Envoie transactions
│   ├── consumer/
│   │   └── kafka_consumer.py           # Recoit → PostgreSQL
│   ├── docker-compose.kafka.yml        # Services Kafka
│   └── README.md
│
├── V5-quality/                          # V5 : Qualite & Monitoring
│   ├── great_expectations/
│   │   ├── expectations/
│   │   └── great_expectations.yml
│   ├── monitoring/
│   │   ├── prometheus/
│   │   └── grafana/
│   └── README.md
│
├── data/
│   ├── source/       <- Dataset original
│   ├── raw/          <- Donnees brutes (lots)
│   ├── processed/    <- Donnees transformees
│   └── sample/       <- Echantillon pour tests
│
├── docs/             <- Documentation
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## 3. Flux entre les versions

```
V1 (Batch)
│  CSV → Python → PostgreSQL
│
├──► V2 (dbt)
│    │  Meme ingestion, mais la transformation = SQL models dbt
│    │  Python transform → remplace par stg → int → mart
│    │
│    ├──► V3 (Airflow)
│    │    │  Meme chose, mais orchestre par un DAG
│    │    │  dbt run + dbt test = taches Airflow
│    │    │
│    │    ├──► V4 (Kafka)
│    │    │    │  Ingestion = Kafka au lieu de CSV
│    │    │    │  Producer → topic → Consumer → PostgreSQL
│    │    │    │  Meme dbt pour la transformation
│    │    │    │
│    │    │    └──► V5 (Quality)
│    │    │         │  Meme pipeline, mais + qualite
│    │    │         │  Great Expectations + Prometheus
```

---

## 4. Detail de chaque version

### V1 — Batch (FAIT)

| Composant | Fichier | Role |
|-----------|---------|------|
| Ingestion | `src/ingestion/ingest_batch.py` | Split CSV source en 31 fichiers quotidiens |
| Transformation | `src/transformation/transform_transactions.py` | step → timestamp, nettoyage, validation |
| Chargement | `src/utils/database.py` | Load PostgreSQL avec retry, pool |
| Schema | `sql/create_tables.sql` | Table transactions + indexes |
| Tests | `tests/test_*.py` | Tests unitaires (16 tests) |
| Docker | `docker-compose.yml` | PostgreSQL 16 avec healthcheck |

**Ce que V1 resout :**
- Ingestion de donnees massives (6.36M lignes) par lots
- Separation staging (donnees brutes) vs transformees
- Chargement robuste avec retry et pool de connexions

**Ce que V1 ne resout PAS :**
- Transformation SQL versionnee et testee → V2
- Orchestration automatique → V3
- Traitement temps reel → V4
- Monitoring et qualite → V5

---

### V2 — dbt (A IMPLANTER)

| Composant | Fichier | Role |
|-----------|---------|------|
| Staging | `models/staging/stg_transactions.sql` | Nettoyage des donnees |
| Intermediate | `models/intermediate/int_daily_agg.sql` | Agregation quotidienne |
| Marts | `models/marts/mart_transactions.sql` | Donnees business-ready |
| Sources | `models/staging/_sources.yml` | Definition des sources |
| Tests | `tests/schema.yml` | not_null, unique, accepted_values |
| Config | `dbt_project.yml` | Configuration dbt |
| Profiles | `profiles.yml` | Connexion PostgreSQL |

**Ce que V2 ajoute :**
- Transformation en SQL pur (plus de Python pour la transfo)
- Tests integres (not_null, unique, accepted_values)
- Documentation automatique (lineage, colonnes)
- Pattern staging → intermediate → marts

**Ce que V2 ne resout PAS :**
- Orchestration automatique → V3
- Traitement temps reel → V4
- Monitoring et qualite → V5

**Commandes :**
```bash
dbt run                    # Execute tous les modeles
dbt test                   # Execute tous les tests
dbt docs generate          # Genere la documentation
dbt docs serve             # Ouvre la doc dans le navigateur
```

---

### V3 — Airflow (A IMPLANTER)

| Composant | Fichier | Role |
|-----------|---------|------|
| DAG | `dags/transaction_pipeline.py` | Orchestration du pipeline |
| Capteur | Sensor pour detecter nouveaux fichiers |
| Taches | BashOperator / PythonOperator |

**Ce que V3 ajoute :**
- Orchestration automatique (pas besoin de lancer manuellement)
- Gestion des dependances entre taches
- Retries automatiques en cas d'echec
- Idempotence (rejouer ne duplique pas)
- Planning (cron)
- Monitoring des taches (UI Airflow)

**Ce que V3 ne resout PAS :**
- Traitement temps reel → V4
- Monitoring avance → V5

**Structure du DAG :**
```python
# transaction_pipeline.py
start → load_staging → dbt_run → dbt_test → end
```

---

### V4 — Kafka (A IMPLANTER)

| Composant | Fichier | Role |
|-----------|---------|------|
| Producer | `producer/kafka_producer.py` | Envoie transactions sur un topic |
| Consumer | `consumer/kafka_consumer.py` | Recoit et ecrit en PostgreSQL |
| Config | `docker-compose.kafka.yml` | Services Kafka + Zookeeper |

**Ce que V4 ajoute :**
- Streaming temps reel (pas de fichiers CSV)
- Decouplage producteur/consommateur
- Scalabilite (plusieurs consumers)
- Tolérance aux pannes

**Concepts cles :**
- **Topic :** File de messages (comme une table)
- **Partition :** Parallelisation d'un topic
- **Consumer Group :** Plusieurs consumers qui partagent la charge
- **Exactly-once :** Chaque message est traite une seule fois

---

### V5 — Quality & Monitoring (A IMPLANTER)

| Composant | Fichier | Role |
|-----------|---------|------|
| Expectations | `great_expectations/expectations/` | Regles de qualite |
| Prometheus | `monitoring/prometheus/` | Metriques du pipeline |
| Grafana | `monitoring/grafana/` | Dashboards visuels |

**Ce que V5 ajoute :**
- Tests de qualite des donnees (montants negatifs, doublons, etc.)
- Monitoring du pipeline (latence, volume, taux d'echec)
- Alertes automatiques
- Separation qualite des donnees vs qualite du pipeline

---

## 5. Schema de donnees (commun aux 5 versions)

```sql
CREATE TABLE transactions (
    id                SERIAL PRIMARY KEY,
    transaction_date  TIMESTAMP NOT NULL,
    transaction_date_only DATE NOT NULL,
    transaction_hour  INTEGER NOT NULL,
    step              INTEGER NOT NULL,
    type              VARCHAR(20) NOT NULL,
    amount            NUMERIC(15, 2) NOT NULL,
    name_orig         VARCHAR(20) NOT NULL,
    old_balance_org   NUMERIC(15, 2),
    new_balance_orig  NUMERIC(15, 2),
    name_dest         VARCHAR(20) NOT NULL,
    old_balance_dest  NUMERIC(15, 2),
    new_balance_dest  NUMERIC(15, 2),
    is_fraud          INTEGER NOT NULL DEFAULT 0,
    is_flagged_fraud  INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Ce schema ne change PAS entre les 5 versions — seuls les **moyens d'y arriver** changent.

---

## 6. Commandes essentielles

### Toutes les versions

```bash
# Demarrer PostgreSQL
docker-compose up -d

# Activer le venv
source venv/bin/activate

# Tests
pytest tests/ -v
```

### V1 — Batch

```bash
python -m src.ingestion.ingest_batch
python -m src.transformation.transform_transactions
python -m src.utils.database
```

### V2 — dbt

```bash
dbt run
dbt test
dbt docs generate
```

### V3 — Airflow

```bash
airflow scheduler
airflow webserver
```

### V4 — Kafka

```bash
# Producer
python kafka_producer.py

# Consumer
python kafka_consumer.py
```

### V5 — Quality

```bash
great_expectations checkpoint run
```

---

## 7. Ordre d'implementation

| Priorite | Version | Contenu | Estimation |
|----------|---------|---------|------------|
| 1 | V1 | Batch pipeline | FAIT |
| 2 | V2 | dbt models + tests | ~2h |
| 3 | V3 | Airflow DAG | ~2h |
| 4 | V4 | Kafka producer/consumer | ~3h |
| 5 | V5 | Quality + monitoring | ~2h |

---

*Document genere pour le projet Transaction Data Platform*
*V1 Batch — Consolidation terminee*
