# V5 — Quality & Monitoring

## Qu'est-ce que cette version resout ?

V5 ajoute la **qualite des donnees** et le **monitoring** au pipeline. C'est la couche finale qui garantit que les donnees sont fiables et que le pipeline fonctionne correctement.

### Ce que V5 ajoute par rapport a V4

| Avant (V4 - Streaming) | Apres (V5 - Quality) |
|------------------------|----------------------|
| Donnees en temps reel | Donnees verifiees |
| Pas de monitoring | Dashboards visuels |
| Pas d'alertes | Alertes automatiques |
| Qualite non garantie | Score de qualite |

### Ce que V5 ne resout PAS

- C'est la derniere version du projet

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        V5 Architecture                          │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Great Expectations│    │    Prometheus     │                  │
│  │ (Data Quality)   │    │ (Metrics)         │                  │
│  │ - not_null       │    │ - pipeline_latency│                  │
│  │ - in_set         │    │ - row_count       │                  │
│  │ - between        │    │ - fraud_rate      │                  │
│  │ - regex          │    │ - quality_score   │                  │
│  │ - unique         │    │ - error_count     │                  │
│  └────────┬─────────┘    └────────┬───────────┘                  │
│           │                       │                              │
│           └───────────┬───────────┘                              │
│                       │                                          │
│              ┌────────▼────────┐                                 │
│              │     Grafana     │                                 │
│              │   (:3000)       │                                 │
│              │                 │                                 │
│              │ - Quality Score │                                 │
│              │ - Fraud Rate    │                                 │
│              │ - Pipeline View │                                 │
│              └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Demarrage

### 1. Lancer les services

```bash
cd V5-quality

# Build et demarrer
docker compose -f docker-compose.quality.yml up -d --build

# Voir les services
docker compose -f docker-compose.quality.yml ps
```

### 2. Lancer les checks qualite

```bash
# En ligne de commande
docker compose -f docker-compose.quality.yml run great-expectations

# Ou localement
python -m scripts.run_quality_checks
```

### 3. Voir les metriques

```bash
# Prometheus
http://localhost:9090

# Grafana
http://localhost:3000 (admin/admin)
```

### 4. Arreter

```bash
docker compose -f docker-compose.quality.yml down
```

## Expectations (8 regles)

| # | Expectation | Colonne | Regle |
|---|-------------|---------|-------|
| 1 | not_null | amount | Montant requis |
| 2 | not_null | type | Type requis |
| 3 | not_null | name_orig | Emetteur requis |
| 4 | in_set | type | PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT |
| 5 | between | amount | 0 - 10,000,000 |
| 6 | regex | name_orig | ^C[0-9]+$ |
| 7 | unique | id | Pas de doublons |
| 8 | row_count | - | 6M - 7M lignes |

## Metriques Prometheus

| Metrique | Type | Description |
|----------|------|-------------|
| tx_quality_score | Gauge | Score qualite (0-100) |
| tx_rows_total | Counter | Total lignes |
| tx_fraud_rate | Gauge | Taux de fraude |
| tx_expectations_passed_total | Counter | Tests passes |
| tx_expectations_failed_total | Counter | Tests echoues |
| tx_pipeline_latency_seconds | Histogram | Latence pipeline |
| tx_pipeline_errors_total | Counter | Erreurs pipeline |

## Dashboard Grafana

| Panel | Type | Donnees |
|-------|------|---------|
| Quality Score | Gauge | Score global 0-100 |
| Rows Processed | Time series | Lignes/heure |
| Fraud Rate | Time series | Taux fraude/heure |
| Pipeline Errors | Stat | Nombre d'erreurs |
| Pipeline Latency | Time series | p50, p95, p99 |
| Expectations Results | Time series | Passed vs Failed |

## Commandes utiles

```bash
# Voir les logs
docker compose -f docker-compose.quality.yml logs -f

# Voir les logs du quality check
docker compose -f docker-compose.quality.yml logs -f great-expectations

# Relancer les checks
docker compose -f docker-compose.quality.yml run --rm great-expectations

# Arreter tout
docker compose -f docker-compose.quality.yml down -v
```

## Fichiers

```
V5-quality/
├── great_expectations/
│   ├── great_expectations.yml       # Config GE
│   ├── expectations/
│   │   └── transactions.json        # 8 expectations
│   └── checkpoints/
│       └── checkpoint.yml           # Checkpoint GE
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml           # Config Prometheus
│   │   └── alert_rules.yml          # Regles d'alerte
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── prometheus.yml
│           └── dashboards/
│               ├── dashboard.yml
│               └── quality.json     # Dashboard Quality
├── scripts/
│   ├── run_quality_checks.py        # Lance les checks
│   └── export_metrics.py            # Exporte metrics
├── docker-compose.quality.yml       # Services
├── Dockerfile
├── requirements.txt
└── README.md
```
