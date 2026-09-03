# Transaction Data Platform

Plateforme de suivi et de traitement de transactions numeriques.

## Objectif

Construire un pipeline de donnees professionnel permettant de :
1. Recevoir des donnees de transactions
2. Stocker les donnees brutes
3. Transformer et nettoyer les donnees
4. Charger les donnees dans PostgreSQL
5. Permettre l'analyse et la prise de decision

## Architecture (Version 1 - Pipeline Batch)

```
Dataset Original
       |
       v
transactions_original.csv
       |
       v
  BATCH INGESTION
       |
       v
Decoupage en lots
       |
       v
   DATA RAW
       |
       v
TRANSFORMATION
       |
       v
DATA PROCESSED
       |
       v
 POSTGRESQL
       |
       v
DONNEES EXPLOITABLES
```

## Structure du projet

```
transaction-data-platform/
|
+-- data/
|   +-- source/       <- Dataset original
|   +-- raw/          <- Donnees brutes (lots)
|   +-- processed/    <- Donnees transformees
|   +-- sample/       <- Echantillon pour tests
|
+-- src/
|   +-- ingestion/    <- Script d'ingestion batch
|   +-- transformation/ <- Script de transformation
|   +-- utils/        <- Utilitaires (connexion DB)
|
+-- sql/              <- Scripts SQL
+-- tests/            <- Tests
+-- docs/             <- Documentation
```

## Installation

```bash
# Cloner le depot
git clone <url-du-depot>
cd transaction-data-platform

# Creer un environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt
```

## Utilisation

```bash
# 1. Ingestion des donnees
python -m src.ingestion.ingest_batch

# 2. Transformation
python -m src.transformation.transform_transactions

# 3. Chargement en base (a venir)
```

## Dependances

- Python 3.8+
- pandas
- sqlalchemy
- psycopg2-binary
