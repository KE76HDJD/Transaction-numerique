# Carnet mental — Tout faire et maîtriser soi-même (V1 → V5 + URLs)

> Principe : **c'est toi qui tapes**. Chaque étape = commandes copiables,
> résultat attendu, URL où observer. Si un résultat diffère, va au §8 Dépannage.

---

## 0. Socle (une fois)

```bash
docker compose up -d                          # PostgreSQL :5434
source venv/bin/activate                      # Python du projet
```

## 1. V1 — Batch : CSV → PostgreSQL (6 362 620 lignes)

```bash
python -m V1-batch.src.ingestion.ingest_batch
# → 31 fichiers data/raw/. Attendu : "31 fichiers"

python -m V1-batch.src.transformation.transform_transactions
# → 31 fichiers data/processed/. Attendu : step → transaction_date, ~3 min

python -m V1-batch.src.utils.database
# → TRUNCATE + chargement ~8 min (1re fois), ou skip en secondes si déjà 6 362 620

PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db \
  -t -c "SELECT count(*) FROM transactions;"
# Attendu : 6362620
```

**À maîtriser :** `chunksize=5000` (paquets), pool (`pool_size`, `pre_ping`),
retry ×3, `TRUNCATE` vs `DROP`, `with engine.begin()` (commit garanti SQLAlchemy 1.4+2.0).

## 2. V2 — dbt : brut → métier testé

```bash
cd V2-dbt && dbt run && dbt test
# Attendu : 2 modèles OK (~58s), 23/23 PASS (~3 min 30)

PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -t \
  -c "SELECT count(*) FROM public_marts.mart_transactions;" \
  -c "SELECT count(*) FROM public_staging.stg_transactions;"
# Attendu : 31 et 6362604 (16 lignes amount<=0 filtrées par stg — normal)
```
**À maîtriser :** `source()` vs `ref()`, view/ephemeral/table, `accepted_values/unique/not_null`,
`dbt docs generate && dbt docs serve` (lineage `target/index.html`).

## 3. V3 — Airflow : orchestration — `http://localhost:8082` (admin/admin)

```bash
docker compose -f docker-compose.airflow.yml up -d
```
Sur l'UI : DAG `transaction_pipeline` → ▶ **Trigger** → vue **Grid** :
`ingest (~2 min) → transform (~3 min) → load (skip si 6,36M) → dbt_run → dbt_test` ≈ 5 min, 5/5 vert.
Historique 9 failed = runs de debug, normal.

**À maîtriser :** dépendances `>>`, `retries=2`, logs par tâche/tentative,
`BashOperator` + vérifs SQL légères (jamais dbt dans l'image Airflow).

## 4. V4 — Kafka temps réel — `http://localhost:8081`

```bash
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db \
  -f V4-kafka/sql/create_streamed_table.sql
# Attendu : CREATE TABLE (+ index)

docker compose -f V4-kafka/docker-compose.kafka.yml up -d
docker ps --format "{{.Names}} {{.Status}}" | grep -E "zookeeper|kafka|producer|consumer|ui"
# Attendu : zookeeper + kafka healthy, producer/consumer Up, ui Up
```
Terminal 1 : `docker logs -f transaction-consumer` → `Écrit: N...`
Terminal 2 : `docker logs -f transaction-producer` → `Envoyé: N / 6 362 620`
Sur `:8081` : cluster `local` → topic `transactions` → 1 message = JSON
(`step, type, amount...`), offset = n° de ligne, key vide (pas d'ordre global).

```bash
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db -t \
  -c "SELECT count(*), min(kafka_offset), max(kafka_offset) FROM transactions_streamed;"
# Relancé 2× : le count croît → flux vivant. Offset 500 de l'UI =
# SELECT * ... WHERE kafka_offset = 500 → 0 perte.
```
Stop après démo (6,3M à 0,1-0,5s/msg = des jours) : `docker stop transaction-producer`.
Détails : `docs/carnet-kafka-entreprise.md`.

**À maîtriser :** offset/partition, consumer group, **lag** (= retard, LA métrique),
`enable_auto_commit=False` + commit manuel, reprise sur offset (at-least-once),
clé de partition (ordre), idempotence.

## 5. V5 — Qualité + monitoring

```bash
venv/bin/python V5-quality/scripts/run_quality_checks.py
# Attendu : 8/8 PASS (100 %) en local ; 7/8 en Docker si l'échantillon
# accroche un montant négatif = les 16 anomalies connues (dbt les filtre). Honnête.
```
Services : exporter `:8002`, Prometheus `:9090`, Grafana `:3000` (admin/admin) :
```bash
docker compose -f V5-quality/docker-compose.quality.yml up -d
```
- `:9090` → Graph → taper `tx_quality_score` → **Execute** → courbe 0→100.
  `rate(tx_rows_total[5m])` → débit. Time range : **Last 1 hour**.
  "No data queried yet" = juste l'état vide avant Execute, pas une panne.
- `:3000` → dashboard *Transaction Quality Dashboard* (6 panels auto-requêtés).
  `tx_fraud_rate` / erreurs à **0** = ligne plate valide, pas du vide.
- `:8002` → métriques brutes (`tx_quality_score`, `tx_rows_total`...).

**À maîtriser :** Prometheus stocke (scrape 15-30s), Grafana interroge à ta place ;
on ne plotte jamais 6M de lignes mais des **agrégats** ; alerter sur seuils.

## 6. Tableau des URLs

| URL | Login | Voir |
|---|---|---|
| `:8082` | admin/admin | Airflow : runs, Grid, logs |
| `:8081` | — | Kafka-UI : topics, messages, lag du group |
| `:9090` | — | Prometheus : Graph (Execute !), Targets, Alerts |
| `:3000` | admin/admin | Grafana : dashboard qualité 6 panels |
| `:8002` | — | Exporter : métriques brutes |

## 7. Règle thermique (PC safe)

`sensor s` → Package < 90°C. **Une stack à la fois**, `docker stop/down` après chaque
démo (volumes = données sauves). Jamais 2 gros jobs ensemble.
`transaction-producer` seul = 2,4 Go + 1 cœur : le stopper après démo.

## 8. Dépannage express

| Symptôme | Fix |
|---|---|
| `cannot drop table ... depend on it` | `TRUNCATE` au lieu de `DROP` (`ensure_tables_exist`) |
| `'Connection' has no attribute 'commit'` (1.4) / TRUNCATE sans effet (2.0) | `with engine.begin()` |
| `'Engine' has no attribute 'cursor'` (pandas 3 + SQLA 1.4, conteneur) | charger depuis l'hôte (SQLA 2.0) ; fast-skip ensuite |
| `host.docker.internal` inconnu (Linux) | `extra_hosts: host-gateway` |
| Zookeeper unhealthy (`ruok ... whitelist`) | `cub zk-ready zookeeper:2181 30` |
| Kafka `Each listener must have a different port` | interne 29092 / hôte 9092 |
| Mount `read-only file system` / `can't open file` | retirer le mount `.:/opt/app:ro` inutile (code déjà `COPY`) |
| Logs conteneur vides | `python -u` (buffer stdout) |
| Grafana panel vide (Latency) | bon nom : `tx_pipeline_latency_seconds_bucket` |
| Prometheus "No data queried yet" | taper la métrique + **Execute** + Last 1 hour |
| PC 82°C+ / coupure | stop producer, down stacks inutilisées, une chose à la fois |
