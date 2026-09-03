# Transaction Data Platform

Plateforme de suivi et de traitement de transactions numeriques.

## Roadmap : 5 versions architecturales

| Version | Architecture | Ce qu'elle resout | Status |
|---------|-------------|-------------------|--------|
| **V1 — Batch** | Python + PostgreSQL | Extraction, chargement staging, transformation | OK |
| **V2 — dbt** | dbt + PostgreSQL | Transformation as code, tests, ligneеe | A venir |
| **V3 — Airflow** | Airflow + dbt + PostgreSQL | Orchestration, retries, idempotence | A venir |
| **V4 — Kafka** | Kafka + PostgreSQL | Streaming temps reel, flux continu | A venir |
| **V5 — Qualite** | Great Expectations + Prometheus | Monitoring, alertes, qualite des donnees | A venir |

## Version 1 — Batch

### Qu'est-ce que cette version resout ?

V1 construit le pipeline batch de base : lire des fichiers CSV, les charger dans PostgreSQL (staging), puis les transformer en donnees business-ready.

**Ce que V1 resout :**
- Ingestion de donnees massives (6.36M lignes) par lots journaliers
- Separation staging (donnees brutes) vs transformees (pretes a l'analyse)
- Chargement robuste avec retry, pool de connexions, healthcheck

**Ce que V1 ne resout PAS (c'est le role des versions suivantes) :**
- Transformation SQL versionnee et testee (→ V2 dbt)
- Orchestration automatique des dependances (→ V3 Airflow)
- Traitement en temps reel (→ V4 Kafka)
- Monitoring et qualite des donnees (→ V5 Qualite)

### Architecture

```
Dataset Original (6.36M lignes, 471 Mo)
       |
       v
  BATCH INGESTION (ingest_batch.py)
       |  Split par fenetre de 24h
       v
  DATA RAW (day_01.csv ... day_31.csv)
       |
       v
  TRANSFORMATION (transform_transactions.py)
       |  step → timestamp, nettoyage, validation
       v
  DATA PROCESSED (transactions_day_01.csv ... transactions_day_31.csv)
       |
       v
  POSTGRESQL (database.py → docker PostgreSQL 16)
       |
       v
  DONNEES EXPLOITABLES (table transactions, 6.36M lignes)
```

## Installation

```bash
# Cloner le depot
git clone <url-du-depot>
cd Transaction_numerique

# Creer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt
```

## Demarrage

### 1. PostgreSQL (Docker)

```bash
# Demarrer PostgreSQL
docker-compose up -d

# Verifier que le container tourne
docker ps

# Verifier la connexion
psql -h localhost -p 5434 -U kevin -d transaction_db
# Mot de passe : kevin123
```

### 2. Pipeline batch

```bash
# Activer le venv (OBLIGATOIRE)
source venv/bin/activate

# 1. Ingestion (decoupe le CSV source en 31 fichiers)
python -m src.ingestion.ingest_batch

# 2. Transformation (ajoute timestamps, nettoie)
python -m src.transformation.transform_transactions

# 3. Chargement PostgreSQL (charge les 31 fichiers)
python -m src.utils.database
```

### 3. Tests V1

```bash
# Lancer les tests Python
pytest tests/ -v
```

## V2 — Transformation dbt

### 1. Installer dbt

```bash
source venv/bin/activate
pip install dbt-postgres
```

### 2. Tester la connexion

```bash
cd v2-dbt
dbt debug
```

### 3. Executer les modeles

```bash
# Lancer tous les modeles SQL (stg → int → mart)
dbt run
```

### 4. Lancer les tests

```bash
# Lancer les 23 tests (not_null, unique, accepted_values, etc.)
dbt test
```

### 5. Documentation

```bash
# Generer la documentation HTML
dbt docs generate

# Ouvrir dans le navigateur
dbt docs serve
```

### Commandes utiles

```bash
# Executer un seul modele
dbt run --select stg_transactions

# Executer les tests d'un seul modele
dbt test --select mart_transactions

# Nettoyer et tout relancer
dbt clean
dbt run
dbt test
```

## Structure du projet

```
Transaction_numerique/
|
+-- data/
|   +-- source/       <- Dataset original (471 Mo)
|   +-- raw/          <- Donnees brutes (31 fichiers)
|   +-- processed/    <- Donnees transformees (31 fichiers)
|   +-- sample/       <- Echantillon pour tests (100 lignes)
|
+-- src/
|   +-- ingestion/    <- Ingestion batch (V1)
|   +-- transformation/ <- Transformation Python (V1)
|   +-- utils/        <- Utilitaires (connexion PostgreSQL)
|
+-- v2-dbt/           <- Transformation dbt (V2)
|   +-- models/
|   |   +-- staging/
|   |   +-- intermediate/
|   |   +-- marts/
|   +-- tests/
|
+-- sql/              <- Scripts SQL (creation tables)
+-- tests/            <- Tests unitaires Python
+-- docs/             <- Documentation
+-- docker-compose.yml <- PostgreSQL Docker
+-- requirements.txt  <- Dependances Python
+-- .env              <- Configuration DB (non versionne)
```

## Dependances

- Python 3.8+
- pandas (manipulation de donnees)
- sqlalchemy (connexion PostgreSQL)
- psycopg2-binary (driver PostgreSQL)
- python-dotenv (variables d'environnement)
- pytest (tests)

## Schema de donnees

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    transaction_date_only DATE NOT NULL,
    transaction_hour INTEGER NOT NULL,
    step INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    name_orig VARCHAR(20) NOT NULL,
    old_balance_org NUMERIC(15, 2),
    new_balance_orig NUMERIC(15, 2),
    name_dest VARCHAR(20) NOT NULL,
    old_balance_dest NUMERIC(15, 2),
    new_balance_dest NUMERIC(15, 2),
    is_fraud INTEGER NOT NULL DEFAULT 0,
    is_flagged_fraud INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Statistiques finales

- **Total** : 6,362,620 transactions
- **Types** : CASH_OUT (35.2%), PAYMENT (33.8%), CASH_IN (22.0%), TRANSFER (8.4%), DEBIT (0.7%)
- **Fraudes** : 8,213 (0.13%)
