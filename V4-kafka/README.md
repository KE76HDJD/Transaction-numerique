# V4 — Kafka (Streaming Temps Réel)

## Qu'est-ce que cette version resout ?

V4 remplace l'ingestion batch par un **flux temps réel** avec Kafka. Le dataset CSV historique est utilisé comme source pour simuler un flux de transactions en temps réel.

### Ce que V4 ajoute par rapport a V3

| Avant (V3 - Batch) | Apres (V4 - Streaming) |
|--------------------|------------------------|
| Fichiers CSV lus une fois | Flux continu de messages |
| Traitement par lots | Traitement en temps réel |
| Pas de latence | Latence de quelques secondes |
| Pas de scaler horizontalement | Plusieurs consumers possibles |

### Ce que V4 ne resout PAS

- Monitoring avance → V5

## Architecture

```
Dataset CSV (6.36M lignes)
       │
       ▼
  PRODUCER (Python)
       │  Lit CSV → JSON → Kafka
       │  0.1-0.5s entre chaque envoi
       ▼
  KAFKA TOPIC "transactions"
       │
       ▼
  CONSUMER (Python)
       │  Écoute → INSERT PostgreSQL
       ▼
  POSTGRESQL (transactions_streamed)
```

## Démarrage

### 1. Créer la table PostgreSQL

```bash
psql -h localhost -p 5434 -U kevin -d transaction_db -f sql/create_streamed_table.sql
```

### 2. Démarrer Kafka

```bash
cd V4-kafka

# Build et démarrer
docker compose -f docker-compose.kafka.yml up -d --build

# Vérifier les services
docker compose -f docker-compose.kafka.yml ps
```

### 3. Lancer le Producer

```bash
# En terminal séparé
docker compose -f docker-compose.kafka.yml exec kafka-producer python producer.py
```

### 4. Lancer le Consumer

```bash
# En terminal séparé
docker compose -f docker-compose.kafka.yml exec kafka-consumer python consumer.py
```

### 5. Voir les données

```bash
# Vérifier dans PostgreSQL
psql -h localhost -p 5434 -U kevin -d transaction_db \
    -c "SELECT COUNT(*) FROM transactions_streamed"

# Voir les dernières transactions
psql -h localhost -p 5434 -U kevin -d transaction_db \
    -c "SELECT * FROM transactions_streamed ORDER BY id DESC LIMIT 10"
```

## Kafka UI

```
http://localhost:8081
Cluster: local
Topic: transactions
```

## Commandes utiles

```bash
# Voir les logs
docker compose -f docker-compose.kafka.yml logs -f

# Voir les logs du producer
docker compose -f docker-compose.kafka.yml logs -f kafka-producer

# Voir les logs du consumer
docker compose -f docker-compose.kafka.yml logs -f kafka-consumer

# Arrêter
docker compose -f docker-compose.kafka.yml down

# Tout supprimer
docker compose -f docker-compose.kafka.yml down -v
```

## Fichiers

```
V4-kafka/
├── producer/
│   ├── producer.py           # Lit CSV → envoie sur Kafka
│   ├── Dockerfile
│   └── requirements.txt
├── consumer/
│   ├── consumer.py           # Écoute Kafka → écrit PostgreSQL
│   ├── Dockerfile
│   └── requirements.txt
├── sql/
│   └── create_streamed_table.sql
├── docker-compose.kafka.yml  # Services Kafka
└── README.md
```

## Concepts Kafka

| Concept | Description |
|---------|-------------|
| **Topic** | File de messages (comme une table) |
| **Partition** | Parallelisation d'un topic |
| **Producer** | Envoie des messages sur un topic |
| **Consumer** | Reçoit des messages d'un topic |
| **Consumer Group** | Plusieurs consumers qui partagent la charge |
| **Offset** | Position du consumer dans la partition |
