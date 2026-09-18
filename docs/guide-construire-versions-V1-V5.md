# Guide de construction — Monter chaque version seul (V1 → V5)

> Objectif : après lecture, tu reconstruis chaque version **sans aide**.
> Chaque chapitre = objectif, prérequis, architecture, commandes pas-à-pas
> (avec résultat attendu), code expliqué, vérifications, pièges réels + fixes,
> preuve livrable, questions d'entretien.
> Socle commun : Ubuntu, Python 3.11+, Docker, 6 Go RAM libres, dataset
> `data/source/PS_20174392719_1491204439457_log.csv` (6 362 620 lignes).

---

## V1 — Batch Python + PostgreSQL

### Objectif
Charger 6,3M de lignes CSV en base, proprement : découper, transformer, créer
la table, charger avec robustesse (retry, pool, reprise).

### Prérequis
```bash
python3 -m venv venv && source venv/bin/activate
venv/bin/pip install pandas sqlalchemy psycopg2-binary python-dotenv pytest
docker compose up -d   # PostgreSQL :5434 (DB transaction_db, user kevin / kevin123)
```
Vérifie : `PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -c "SELECT 1;"` → `1`.

### Architecture
```
CSV source (471 Mo)
 │ ingest_batch.py  (step 1-24 → day_01 ... step 721-743 → day_31)
 ▼ data/raw/day_XX.csv (31 fichiers)
 │ transform_transactions.py (step→timestamp, snake_case, filtres)
 ▼ data/processed/transactions_day_XX.csv (31 fichiers)
 │ database.py + sql/create_tables.sql (CREATE TABLE + index, TRUNCATE, to_sql)
 ▼ PostgreSQL public.transactions (6 362 620)
```

### Pas-à-pas
```bash
# 1. Ingestion (~2 min) — Convention: 24 steps = 1 jour (HOURS_PER_DAY=24)
python -m V1-batch.src.ingestion.ingest_batch
# Attendu : "31 fichiers", data/raw/day_01.csv … day_31.csv

# 2. Transformation (~3 min) — REFERENCE_DATE=2024-01-01, step N → +N-1 heures ;
#    dérivés transaction_date_only / transaction_hour ; renommage camelCase→snake_case
python -m V1-batch.src.transformation.transform_transactions
# Attendu : data/processed/transactions_day_*.csv

# 3. Table + chargement (~8 min la 1re fois)
python -m V1-batch.src.utils.database
# Attendu : "TRUNCATE effectue" (ou CREATE si 1re fois), "6 362 620 lignes chargees"

# 4. Vérification
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -t \
  -c "SELECT count(*) FROM transactions;" \
  -c "SELECT type, count(*) FROM transactions GROUP BY type;"
# Attendu : 6362620 ; CASH_OUT ~35 %, PAYMENT ~34 %, CASH_IN ~22 %, TRANSFER ~8 %, DEBIT ~1 %

# 5. Tests
pytest V1-batch/tests/ -v   # Attendu : 16 tests PASS
```

### Code à maîtriser (`database.py:DatabaseManager`)
- `create_engine(..., pool_pre_ping=True, pool_size=10, pool_recycle=300)` : pool
  réutilisé, connexions mortes recyclées, mortes testées avant usage.
- `df.to_sql(..., if_exists="append", chunksize=5000)` : INSERT par paquets
  (pas de transaction géante) ; `engine.dispose()` tous les 5 fichiers.
- `ensure_tables_exist()` : table présente → `TRUNCATE` (vide en ms, garde
  structure+index) ; absente → `create_tables()` (lit `create_tables.sql`).
- `with engine.begin()` (jamais `connect()` seul) : commit garanti en
  SQLAlchemy **1.4 et 2.0** (`connect()` seul rollback en 2.0 !).
- Fast-skip : si `COUNT(*) >= 6362620` → skip TRUNCATE/LOAD (démos en secondes).
- Alternative 10× : `COPY transactions FROM 'f.csv' WITH CSV HEADER` (psycopg2).

### Pièges réels + fixes
| Symptôme | Cause | Fix |
|---|---|---|
| `cannot drop table ... depend on it` | vue dbt dépend de la table | `TRUNCATE` au lieu de `DROP` |
| `'Connection' has no attribute 'commit'` (SQLA 1.4) | `conn.commit()` inexistant | `with engine.begin()`, commit auto |
| TRUNCATE sans effet (SQLA 2.0) | `connect()` rollback à la sortie | idem `begin()` |
| `'Engine' has no attribute 'cursor'` (pandas 3 + SQLA 1.4, conteneur) | incompatibilité versions | charger depuis l'hôte (SQLA 2.0) |
| `host.docker.internal` inconnu (Linux) | que Mac/Win le résolvent | `extra_hosts: host-gateway` |

### Preuve : table 6 362 620 + 16 tests. Entretien : *TRUNCATE vs DROP ? chunksize pourquoi ? pool à quoi sert ?*

---

## V2 — dbt : Transformation as Code

### Objectif
Transformer le brut en tables métier **versionnées, testées, documentées** :
`stg (view) → int (ephemeral) → mart (table)` + 23 tests + lineage.

### Prérequis
```bash
venv/bin/pip install dbt-postgres   # dbt 1.12.x, adapter postgres 1.11.x
```
`V2-dbt/profiles.yml` : `host: "{{ env_var('DB_HOST','localhost') }}"`,
port 5434, `transaction_db`, schema `public` (sur hôte → `localhost`, en
Docker → `DB_HOST=host.docker.internal`).

### Architecture
```
public.transactions ──source(raw)──→ stg_transactions (view, WHERE amount>0, renommage sender/receiver)
 ──ref()──→ int_daily_agg (ephemeral → injecté en CTE : totaux, moyennes, fraud_count/rate, pivot par type)
 ──ref()──→ mart_transactions (table, 31 lignes/jour, triée)
tests/schema.yml : unique, not_null, accepted_values (type ×5, is_fraud 0/1)
```

### Pas-à-pas
```bash
cd V2-dbt
dbt debug                          # connexion OK ? profile transaction_platform / target dev
dbt run                            # Attendu : 2 OK en ~58s (stg view 0.4s, mart table 57s)
dbt test                           # Attendu : 23/23 PASS (~3 min 30 ; les tests count() sur 6,3M sont lents)
dbt docs generate && dbt docs serve # lineage target/index.html
cd ..
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -t \
  -c "SELECT count(*) FROM public_marts.mart_transactions;" \
  -c "SELECT count(*) FROM public_staging.stg_transactions;"
# Attendu : 31 et 6362604 (= 6362620 − 16 lignes amount<=0 filtrées : NORMAL)
```

### Code à maîtriser
- `_sources.yml` : déclare `raw.public.transactions` (+ tests source `unique/not_null id`).
- `{{ source() }}` = entrée brute ; `{{ ref() }}` = dépendance interne (= lineage auto).
- `dbt_project.yml:18-28` : matérialisations par couche (view / ephemeral / table).
- `schema.yml` : le test `accepted_values type` documente le contrat métier.

### Pièges + fixes
| Symptôme | Cause | Fix |
|---|---|---|
| `No module named dbt` (dans Airflow) | dbt absent de l'image | **ne jamais** bundler dbt+Airflow (300 déps, conflit) → sidecar `ghcr.io/dbt-labs/dbt-postgres` ou vérif SQL légère |
| `stg` ≠ `transactions` (16 d'écart) | filtre `amount > 0` | attendu : c'est le nettoyage, pas une perte |

### Preuve : `target/run_results.json` (23 PASS), `manifest.json`, `index.html`.
### Entretien : *ref vs source ? ephemeral à quoi sert ? fait vs dimension ?*
→ Dans ce projet `mart` = agrégat jour ; une star schema complète ajouterait
`dim_date/dim_client` + `fact_transactions` (grain transaction, FK vers dims).

---

## V3 — Airflow : orchestration Docker

### Objectif
Enchaîner automatiquement `ingest → transform → load → dbt_run → dbt_test`
avec ordre, retry, logs, historique. Image **légère** (pas de dbt dedans).

### Prérequis
`V3-airflow/Dockerfile` : `python:3.11-slim` + `airflow==2.10.5` + `psycopg2` +
`pandas` + `dotenv` (+ `providers-docker` si sidecar). LocalExecutor (pas de
Redis). `docker-compose.airflow.yml` : `DB_HOST/DB_PORT` env, `extra_hosts`,
volumes dags/logs + projet, UI `:8082`.

### Architecture (DAG `transaction_pipeline.py`)
```
ingest_batch (Bash) → transform_transactions (Bash) → load_postgresql (Bash, fast-skip)
 → dbt_run (vérif SQL psycopg2 : counts stg/mart) → dbt_test (vérif SQL : 4 checks)
retries=2, retry_delay=1min, schedule=None (manuel)
```

### Pas-à-pas
```bash
docker compose -f docker-compose.airflow.yml up -d --build   # build ~2 min avec cache
# UI http://localhost:8082 (admin/admin) → DAG transaction_pipeline → ▶ Trigger
# Grid : ingest ~2 min → transform ~3 min → load skip (~s) → dbt_run/dbt_test (~s) : 5/5 vert
docker exec transaction_numerique-airflow-webserver-1 \
  airflow dags trigger transaction_pipeline                  # même chose en CLI
docker exec transaction_numerique-airflow-webserver-1 \
  airflow tasks states-for-dag-run transaction_pipeline "manual__<DATE>__" -o table
```

### Code à maîtriser
- `BashOperator` + `PROJECT_ROOT=/opt/airflow/project` (volume monté).
- `dbt_run/dbt_test` = **vérifs SQL psycopg2** (pas `python -m dbt`) : V2 reste
  la preuve dbt ; en prod → `DockerOperator(ghcr.io/dbt-labs/dbt-postgres:1.8.7)`.
- Check `amount > 0` sur **`stg`** (pas `transactions`) : le brut contient
  16 lignes ≤ 0 que dbt filtre — tester le brut = faux FAIL.

### Pièges + fixes
| Symptôme | Cause | Fix |
|---|---|---|
| 9 runs failed d'affilée (historique) | bugs successifs (connexion, DROP, commit...) | normal en debug ; seul le dernier run compte |
| webserver `unhealthy` mais UI OK | healthcheck `curl /health` trop strict | ignorer, `/health` répond 200 |
| `load` 8 min à chaque trigger | recharge 6,3M | fast-skip (COUNT ≥ 6362620 → skip) |

### Preuve : run `success` 5/5 sur l'UI. Entretien : *ETL vs ELT ? idempotence ? retry à quoi sert ?*

---

## V4 — Kafka : streaming temps réel

### Objectif
Simuler un flux continu : CSV rejoué événement par événement →
topic → consumer → `transactions_streamed` (+ offsets), observable dans Kafka-UI.

### Prérequis
Images : `confluentinc/cp-zookeeper:7.5.0`, `cp-kafka:7.5.0`,
`provectuslabs/kafka-ui:latest` (~1,5 Go, une fois). Libs : `kafka-python-ng`,
`psycopg2` (requirements producer/consumer).

### Architecture
```
CSV ──producer.py (1 JSON/msg, acks=all, sleep 0.1-0.5s)──→ topic 'transactions' (broker :29092 interne / :9092 hôte)
  consumer.py (group transaction-consumer-group, auto_commit=False) ──INSERT + offset/partition──→ transactions_streamed
  Kafka-UI :8081 (topics, messages, lag du group)
```

### Pas-à-pas
```bash
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db \
  -f V4-kafka/sql/create_streamed_table.sql          # CREATE TABLE + index
docker compose -f V4-kafka/docker-compose.kafka.yml up -d
docker ps --format "{{.Names}} {{.Status}}" | grep -E "zookeeper|kafka|producer|consumer|ui"
# Attendu : zookeeper + kafka healthy, producer/consumer Up, ui Up
docker logs -f transaction-consumer   # T1 : "Écoute le topic", "Écrit: N..."
docker logs -f transaction-producer   # T2 : "Chargé 6 362 620", "Envoyé: N"
# :8081 → cluster local → topic transactions → message JSON (offset, timestamp, key vide, value)
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -t \
  -c "SELECT count(*), min(kafka_offset), max(kafka_offset) FROM transactions_streamed;"
# Relancé 2× : count croît, offsets 0..N continus → 0 perte
# Preuve bout-en-bout : offset 500 de l'UI → SELECT ... WHERE kafka_offset = 500 → même ligne
docker stop transaction-producer      # 6,3M à ce rythme = des jours : stopper après démo
```

### Code à maîtriser (`consumer.py:103-126`)
- `group_id` + `auto_offset_reset="earliest"` + `enable_auto_commit=False`.
- `INSERT ... (..., message.offset, message.partition)` + `conn.commit()` :
  message et offset atomiques = reprise exacte après crash (at-least-once ;
  idempotence via `ON CONFLICT` si besoin).
- **Lag = end − current** par group : LA métrique (grandit = consumer lent/mort).

### Pièges + fixes (tous vécus)
| Symptôme | Cause | Fix |
|---|---|---|
| zookeeper unhealthy (`ruok ... whitelist`) | ZK 3.8+ désactive 4-lettres, `nc` absent | `cub zk-ready zookeeper:2181 30` (syntaxe positionnelle v7.5) |
| `Each listener must have a different port` | 2 listeners sur 9092 | interne `29092` / hôte `9092`, repointer producer/consumer/UI |
| `read-only file system` / `can't open file` | mount `.:/opt/app:ro` inutile (code déjà `COPY`) | le retirer (producer ET consumer) |
| logs vides | `python` bufferisé sans TTY | `command: python -u` |
| `host.docker.internal` inconnu | Linux | `extra_hosts: host-gateway` |
Détails : `docs/carnet-kafka-entreprise.md`.

### Preuve : count croissant + offsets continus + capture UI.
### Entretien : *ordre garanti ? (clé=partition) ; crash consumer ? (reprise offset) ; scaler ? (partitions+consumers) ; surveiller ? (lag).*

---

## V5 — Qualité + monitoring léger

### Objectif
Détecter les anomalies (8 checks), exposer des métriques, alerter, visualiser —
**sans lib lourde** (pas de `great-expectations` 500 Mo : checks en pandas natif).

### Prérequis
`venv` : `pandas psycopg2-binary prometheus-client`. Images : `prom/prometheus`
(~200 Mo, une fois), `grafana:11.6.12` déjà en cache (`docker tag ... :latest`).
Ports libres : `:8002` (exporter ; `:8000` pris par un autre projet), `:9090`, `:3000`.

### Architecture
```
PG ──run_quality_checks.py (8 checks, échantillon 100k)──→ results/quality_results.json (score)
PG ──export_metrics.py :8000 (tx_quality_score, tx_rows_total, tx_fraud_rate,
     tx_expectations_*, tx_pipeline_latency_seconds, tx_pipeline_errors_total)
     ──scrape 30s──→ Prometheus :9090 (alert_rules.yml : 4 alertes)
     ──requêtes──→ Grafana :3000 (dashboard 6 panels, datasource Prometheus)
```

### Pas-à-pas
```bash
venv/bin/python V5-quality/scripts/run_quality_checks.py
# Attendu : 8/8 PASS, 100 % (en Docker 7/8 possible si l'échantillon accroche
# un montant négatif = les 16 anomalies connues → HONNÊTE, dbt les filtre)
docker tag grafana/grafana:11.6.12 grafana/grafana:latest   # 0 octet
docker compose -f V5-quality/docker-compose.quality.yml up -d --build  # build ~2 min (pas d'apt)
# :8002 → lignes tx_* ; :9090 → Targets (prometheus+transaction-quality UP)
#   → Graph : taper tx_quality_score + Execute + Last 1 hour → courbe
# :3000 (admin/admin) → Transaction Quality Dashboard (6 panels)
```

### Code à maîtriser
- `run_quality_checks.py:115-180` : `not_null / in_set / between / regex / unique / row_count(6M-7M)`.
- `export_metrics.py:collect_metrics()` : Gauge/Counter/Histogram, boucle 30s,
  **retry 3×10s** avant `PIPELINE_ERRORS.inc()` (évite les faux +1 au reboot PG).
- `alert_rules.yml` : `QualityScoreTooLow (<80)`, `HighFraudRate (>2 %)`,
  `PipelineErrors (rate>0)`, `ServiceDown (up==0)`.
- Panels : Score (`tx_quality_score`), Rows (`rate(tx_rows_total[5m])*3600`),
  Fraud (`tx_fraud_rate*100`), Errors (`tx_pipeline_errors_total`),
  Latency (`histogram_quantile(..., tx_pipeline_latency_seconds_bucket)` —
  nom exact avec `_seconds` !), Expectations (passed/failed).

### Pièges + fixes
| Symptôme | Cause | Fix |
|---|---|---|
| build 10 min bloqué sur apt | `build-essential` inutile (wheels) | Dockerfile sans apt |
| `:8000` occupé | autre projet | exporter sur `:8002` |
| Prometheus "No data queried yet" | état vide avant Execute | taper métrique + Execute + Last 1 hour |
| Panel Latency vide | `tx_pipeline_latency_bucket` inexistant | `..._seconds_bucket` |
| `tx_pipeline_errors_total = 6` | 6 cycles pendant recovery PG post-coupure (`FATAL: starting up`) | retry 3× ; compteur monotone = cicatrice, pas panne |
| Fraud/Errors "vides" | valent 0 | ligne à 0 = donnée valide |

### Preuve : `quality_results.json` + targets UP + dashboard 6 panels.
### Entretien : *Prometheus tire ou reçoit ? (tire/scrape) ; Gauge vs Counter vs Histogram ? ; pourquoi agréger avant Grafana ?*

---

## Tableau de bord final (URLs + preuves)

| URL | Voir | Preuve |
|---|---|---|
| `:5434` psql | `transactions` 6362620, `mart` 31, `streamed` croissant | données |
| `:8082` Airflow | run 5/5 success | orchestration |
| `:8081` Kafka-UI | topic, messages, lag | streaming |
| `:9090` Prometheus | targets UP, `tx_*` | collecte |
| `:3000` Grafana | 6 panels | visualisation |

Règle thermique : `sensors` Package < 90 °C, **une stack à la fois**, `docker stop/down`
après chaque démo (volumes = données sauves). Bon build — prouve-le en rejouant ce guide.
