"""
Kafka Producer — Simule un flux temps réel de transactions
Lit le CSV historique et envoie sur le topic 'transactions'
"""

import json
import time
import random
import os
import sys
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC = "transactions"
CSV_PATH = os.getenv("CSV_PATH", "/opt/app/data/source/PS_20174392719_1491204439457_log.csv")


def create_producer():
    """Crée le producer Kafka avec retry."""
    for attempt in range(10):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                request_timeout_ms=30000,
                max_block_ms=30000,
            )
            print(f"Connecté à Kafka: {KAFKA_BROKER}")
            return producer
        except NoBrokersAvailable:
            print(f"Tentative {attempt + 1}/10: Kafka pas encore prêt, attente 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(5)

    print("ERREUR: Impossible de se connecter à Kafka")
    sys.exit(1)


def stream_transactions():
    """Lit le CSV et envoie les transactions en flux."""
    producer = create_producer()

    # Lire le CSV
    print(f"Chargement du CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Chargé {len(df):,} transactions")

    # Envoyer ligne par ligne
    count = 0
    for idx, row in df.iterrows():
        message = {
            "step": int(row["step"]),
            "type": row["type"],
            "amount": float(row["amount"]),
            "nameOrig": row["nameOrig"],
            "oldbalanceOrg": float(row["oldbalanceOrg"]),
            "newbalanceOrig": float(row["newbalanceOrig"]),
            "nameDest": row["nameDest"],
            "oldbalanceDest": float(row["oldbalanceDest"]),
            "newbalanceDest": float(row["newbalanceDest"]),
            "isFraud": int(row["isFraud"]),
            "isFlaggedFraud": int(row["isFlaggedFraud"]),
        }

        # Envoyer sur Kafka
        producer.send(TOPIC, value=message)
        count += 1

        if count % 1000 == 0:
            print(f"Envoyé: {count:,} / {len(df):,}")

        # Simuler temps réel (0.1 - 0.5 secondes)
        time.sleep(random.uniform(0.1, 0.5))

    producer.flush()
    producer.close()
    print(f"Terminé: {count:,} transactions envoyées")


if __name__ == "__main__":
    print("=" * 50)
    print("KAFKA PRODUCER — Transaction Stream")
    print("=" * 50)
    stream_transactions()
