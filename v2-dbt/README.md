# V2 — dbt (Transformation as Code)

## Qu'est-ce que cette version resout ?

V2 remplace le script Python de transformation (`transform_transactions.py`) par des **modèles SQL dbt**.

### Ce que V2 ajoute par rapport a V1

| Avant (V1) | Apres (V2) |
|------------|------------|
| Script Python pour la transformation | Modeles SQL versionnes |
| Tests manuels (pytest) | Tests integres (not_null, unique, accepted_values) |
| Documentation manuelle | Documentation generee automatiquement |
| Pas de lineage | Git log des donnees |

### Ce que V2 ne resout PAS

- Orchestration automatique → V3 (Airflow)
- Traitement temps reel → V4 (Kafka)
- Monitoring et qualite → V5

## Architecture

```
PostgreSQL (table transactions, 6.36M lignes)
       │
       ▼
  STAGING (stg_transactions.sql)
       │  Nettoyage, normalisation colonnes
       ▼
  INTERMEDIATE (int_daily_agg.sql)
       │  Agregation quotidienne
       ▼
  MARTS (mart_transactions.sql)
       │  Business-ready (31 lignes, 1 par jour)
       ▼
  PostgreSQL (marts.mart_transactions)
```

## Modeles

### stg_transactions (staging)
- Lit la table `transactions` (source brute)
- Renomme les colonnes (camelCase → snake_case)
- Filtre les transactions avec amount > 0
- Valide les types

### int_daily_agg (intermediate)
- Agrege par jour : nombre de transactions, montant total, taux de fraude
- Compte par type (PAYMENT, TRANSFER, etc.)
- Taux de fraude calcule

### mart_transactions (mart)
- Table business-ready pour l'analyse
- 31 lignes (1 par jour)
- Metriques cles : volume, montant, fraude

## Tests

| Test | Type | Description |
|------|------|-------------|
| `not_null` | Generique | Pas de valeurs nulles |
| `unique` | Generique | Valeurs uniques |
| `accepted_values` | Generique | Valeurs autorisees (type, is_fraud) |
| `test_positive_amount` | Custom | Montants positifs |

## Utilisation

```bash
# Connexion
dbt debug

# Execution des modeles
dbt run

# Tests
dbt test

# Documentation
dbt docs generate
dbt docs serve
```

## Fichiers

```
v2-dbt/
├── dbt_project.yml           # Configuration dbt
├── profiles.yml              # Connexion PostgreSQL
├── models/
│   ├── staging/
│   │   ├── _sources.yml      # Definition des sources
│   │   └── stg_transactions.sql
│   ├── intermediate/
│   │   └── int_daily_agg.sql
│   └── marts/
│       └── mart_transactions.sql
└── tests/
    ├── schema.yml            # Tests generiques
    └── test_positive_amount.sql  # Test custom
```
