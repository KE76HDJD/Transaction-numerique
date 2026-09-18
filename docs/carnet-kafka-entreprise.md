# Carnet mental — Kafka : implémenter & maîtriser (niveau entreprise)

> Objectif : après ce carnet, tu sais déployer Kafka, lire Kafka-UI comme un pro,
> brancher un producer/consumer, et répondre aux questions d'entretien data engineer.
> Références = fichiers réels du projet (`V4-kafka/`).

---

## 1. Modèle mental en 60 secondes

```
PRODUCTEUR ──send(topic, message)──→ BROKER ──stocke──→ TOPIC (découpé en PARTITIONS)
                                                              │  chaque message = OFFSET (0,1,2...)
                                                              ▼
                    CONSOMMER ◄── groupe ── CONSOMMATEUR lit, traite, COMMIT l'offset
```

- **Broker** : le serveur qui stocke (`transaction-kafka`, `KAFKA_BROKER_ID: 1`).
- **Topic** : le tuyau nommé (`transactions`). On ne lit jamais "le broker", on lit un topic.
- **Partition** : sous-tuyau parallèle. Même **clé** = même partition = **ordre garanti**.
  Sans clé (notre cas) = répartition round-robin.
- **Offset** : n° du message dans sa partition. Le consumer retient le dernier offset
  **committé** → reprise après crash exactement là.
- **Consumer group** (`transaction-consumer-group`) : N consumers se partagent les partitions.
  1 partition = 1 consumer max à la fois. Plus de partitions = plus de débit.
- **Lag = end_offset − current_offset** : messages en attente. **LA métrique n°1.**
  Lag qui grandit = consumer trop lent ou mort.

---

## 2. L'URL et sa lecture : `http://localhost:8081`

| Écran | Ce que tu regardes | Réflexe pro |
|---|---|---|
| Topics → `transactions` → Messages | offset, timestamp, key (vide chez nous), value JSON (`step, type, amount, nameOrig...`) | cliquer un message → retrouver sa ligne en PG par `kafka_offset` (= preuve 0 perte) |
| Consumers → `transaction-consumer-group` | current offset / end offset / **lag** | lag > 0 durable = alerter/scaler |
| Brokers → ID 1 | version, taille logs, réplicas | en prod : N brokers, replication factor ≥ 3 |
| Message JSON | `type: PAYMENT`, `isFraud: 0/1`, montants | valider le contrat producer ↔ consumer |

Exercices (faits dans ce projet) :
1. Offset 500 dans l'UI → `SELECT * FROM transactions_streamed WHERE kafka_offset = 500;` → même ligne.
2. Regarder le lag bouger pendant `docker logs -f transaction-consumer` (`Écrit: N`).
3. `transactions` (6 362 620, batch) vs `transactions_streamed` (croît, temps réel) : deux vitesses, deux usages.

---

## 3. Implémenter : recette minimaleentreprise

### 3.1 Compose qui marche (`V4-kafka/docker-compose.kafka.yml`)

```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  healthcheck:
    test: ["CMD-SHELL", "cub zk-ready zookeeper:2181 30 || exit 1"]
kafka:
  image: confluentinc/cp-kafka:7.5.0
  environment:
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
kafka-ui:
  image: provectuslabs/kafka-ui:latest   # UI :8081
```

### 3.2 Producer (`producer/producer.py`)

```python
producer = KafkaProducer(bootstrap_servers="kafka:29092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all", retries=3)
producer.send("transactions", value={"step":..., "type":..., "amount":...})
```

### 3.3 Consumer (`consumer/consumer.py`)

```python
consumer = KafkaConsumer("transactions", bootstrap_servers="kafka:29092",
    group_id="transaction-consumer-group", auto_offset_reset="earliest",
    enable_auto_commit=False)          # commit manuel = contrôle
for message in consumer:
    cur.execute(INSERT_SQL, (..., message.offset, message.partition))
    conn.commit()                       # message + offset atomiques
```

Table cible : `sql/create_streamed_table.sql` (colonnes métier + `kafka_offset, kafka_partition`).

### 3.4 Commandes

```bash
docker compose -f V4-kafka/docker-compose.kafka.yml up -d
docker logs -f transaction-consumer     # Écrit: N...
docker logs -f transaction-producer     # Envoyé: N / ...
# UI : http://localhost:8081 → cluster local → topic transactions
PGPASSWORD=kevin123 psql -h localhost -p 5434 -U kevin -d transaction_db \
  -t -c "SELECT count(*), min(kafka_offset), max(kafka_offset) FROM transactions_streamed;"
docker stop transaction-producer        # le producteur envoie 6,3M de messages : l'arrêter après la démo
```

---

## 4. Carnet de dépannage (erreurs réellement rencontrées)

| Symptôme | Cause | Fix (dans ce projet) |
|---|---|---|
| `transaction-zookeeper is unhealthy`, `ruok ... not in the whitelist` | Zookeeper 3.8+ désactive les 4-lettres ; `nc` absent de l'image | healthcheck → `cub zk-ready zookeeper:2181 30` (syntaxe `cub` v7.5 : positionnelle, pas de `-b`) |
| `Each listener must have a different port` (broker exit) | 2 listeners sur 9092 | interne `29092` / hôte `9092` + repointer producer, consumer, UI sur `kafka:29092` |
| `... read-only file system` (producer) | mount `.:/opt/app:ro` bloque le mount imbriqué `data` | retirer le mount inutile (l'image `COPY` déjà le code) |
| `can't open file '/opt/app/consumer.py'` | le même mount masquait le fichier copié dans l'image | idem côté consumer |
| logs vides alors que ça tourne | `python` bufferise stdout sans TTY | `command: ["python", "-u", ...]`, sans rebuild |
| `could not translate host name "host.docker.internal"` | inconnu sous Linux | `extra_hosts: ["host.docker.internal:host-gateway"]` |
| healthcheck Kafka `kafka-broker-api-versions` en WARN au démarrage | broker pas encore prêt | normal : `start_period: 30s` + retries, devient `healthy` seul |

---

## 5. Patterns entreprise à connaître

- **CDC / Outbox** : en prod on ne rejoue pas un CSV — Debezium capture les changements
  de la DB source (ou l'app écrit événement + ligne métier en 1 transaction = outbox),
  le producer lit le log, pas la table.
- **Clé de partition** : `key=client_id` → tous les événements d'un client dans l'ordre,
  répartis sur les partitions. Sans clé = pas d'ordre global (notre cas, OK pour démo).
- **Sémantiques** : at-least-once (défaut : doublons possibles → rendre le consumer
  **idempotent**, ex. `INSERT ... ON CONFLICT DO NOTHING` sur `(kafka_offset)` ou clé métier) ;
  exactly-once = transactions Kafka + idempotence, coûteux, rarement nécessaire.
- **Schema Registry** (Avro/Protobuf) : contrat versionné des messages au lieu du JSON libre.
- **Rétention** : le topic garde l'historique (ex. 7 jours) → rejeu possible après incident.
- **Dimensionnement** : débit visé ÷ débit par partition = nb partitions ; 1 consumer par partition.
- **Monitoring** : alerter sur **lag** par group, taux d'erreur consumer, espace disque broker.

## 6. Questions d'entretien (réponses en une phrase)

1. *Consumer crash, que se passe-t-il ?* → Reprend à l'offset committé : pas de perte,
   doublons possibles sans idempotence (at-least-once).
2. *Garantir l'ordre ?* → Clé de partition (même clé = même partition = ordre).
3. *Scaler la consommation ?* → Plus de partitions + consumers dans le group (max 1/partition).
4. *Que surveiller ?* → Le **lag** par consumer group, avant tout.
5. *Pourquoi les offsets en base (`kafka_offset`) ?* → Traçabilité + audit + rejeu ciblé
   (`WHERE kafka_offset = N`) + preuve 0 perte face à l'UI.
