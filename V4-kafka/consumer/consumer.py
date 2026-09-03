"""
Kafka Consumer — Écoute le topic 'transactions'
Écrit les transactions dans PostgreSQL en temps réel
"""

import json
import os
import sys
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import psycopg2
import psycopg2.extras

# Configuration Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC = "transactions"
GROUP_ID = "transaction-consumer-group"

# Configuration PostgreSQL
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "host.docker.internal"),
    "port": int(os.getenv("PG_PORT", "5434")),
    "database": os.getenv("PG_DB", "transaction_db"),
    "user": os.getenv("PG_USER", "kevin"),
    "password": os.getenv("PG_PASSWORD", "kevin123"),
}

INSERT_SQL = """
    INSERT INTO transactions_streamed 
    (step, type, amount, name_orig, old_balance_org, new_balance_orig,
     name_dest, old_balance_dest, new_balance_dest, is_fraud, 
     is_flagged_fraud, kafka_offset, kafka_partition)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def create_pg_connection():
    """Crée la connexion PostgreSQL avec retry."""
    for attempt in range(10):
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            print(f"Connecté à PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}")
            return conn
        except Exception as e:
            print(f"Tentative {attempt + 1}/10: PostgreSQL pas prêt: {e}")
            time.sleep(5)

    print("ERREUR: Impossible de se connecter à PostgreSQL")
    sys.exit(1)


def create_consumer():
    """Crée le consumer Kafka avec retry."""
    for attempt in range(10):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                enable_auto_commit=False,
                consumer_timeout_ms=10000,
            )
            print(f"Connecté à Kafka: {KAFKA_BROKER}")
            return consumer
        except NoBrokersAvailable:
            print(f"Tentative {attempt + 1}/10: Kafka pas encore prêt, attente 5s...")
            time.sleep(5)

    print("ERREUR: Impossible de se connecter à Kafka")
    sys.exit(1)


def create_table_if_not_exists(conn):
    """Crée la table transactions_streamed si elle n'existe pas."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions_streamed (
            id SERIAL PRIMARY KEY,
            step INTEGER,
            type VARCHAR(20),
            amount NUMERIC(15, 2),
            name_orig VARCHAR(20),
            old_balance_org NUMERIC(15, 2),
            new_balance_orig NUMERIC(15, 2),
            name_dest VARCHAR(20),
            old_balance_dest NUMERIC(15, 2),
            new_balance_dest NUMERIC(15, 2),
            is_fraud INTEGER,
            is_flagged_fraud INTEGER,
            kafka_offset BIGINT,
            kafka_partition INTEGER,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    print("Table 'transactions_streamed' prête")


def consume_and_write():
    """Écoute Kafka et écrit dans PostgreSQL."""
    consumer = create_consumer()
    conn = create_pg_connection()
    create_table_if_not_exists(conn)

    print(f"\nÉcoute le topic: {TOPIC}")
    print("En attente de messages...\n")

    count = 0
    try:
        for message in consumer:
            data = message.value
            cursor = conn.cursor()

            cursor.execute(INSERT_SQL, (
                data["step"], data["type"], data["amount"],
                data["nameOrig"], data["oldbalanceOrg"], data["newbalanceOrig"],
                data["nameDest"], data["oldbalanceDest"], data["newbalanceDest"],
                data["isFraud"], data["isFlaggedFraud"],
                message.offset, message.partition,
            ))
            conn.commit()
            cursor.close()

            count += 1
            if count % 100 == 0:
                print(f"Écrit: {count:,} transactions")

    except KeyboardInterrupt:
        print(f"\nArrêté. Total: {count:,} transactions")
    finally:
        consumer.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("KAFKA CONSUMER — Transaction Stream")
    print("=" * 50)
    consume_and_write()
