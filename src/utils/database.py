"""
Module de connexion et chargement PostgreSQL.

Ce module fournit des fonctions pour :
1. Se connecter a PostgreSQL
2. Creer les tables
3. Charger les donnees transformees
4. Executer des requetes de verification

Usage :
    from src.utils.database import DatabaseManager
    
    db = DatabaseManager()
    db.connect()
    db.create_tables()
    db.load_csv_file("data/processed/transactions_day_01.csv")
    db.disconnect()
"""

import pandas as pd
import os
import sys
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ============================================
# Configuration
# ============================================

# Charger les variables d'environnement
load_dotenv()

# Configuration par defaut
DEFAULT_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "transaction_db"),
    "user": os.getenv("DB_USER", "kevin"),
    "password": os.getenv("DB_PASSWORD", "kevin123"),
}


# ============================================
# Classe DatabaseManager
# ============================================

class DatabaseManager:
    """Gestionnaire de connexion et operations PostgreSQL."""
    
    def __init__(self, config=None):
        """Initialise le gestionnaire.
        
        Args:
            config: Dictionnaire de configuration (optionnel)
        """
        self.config = config or DEFAULT_CONFIG
        self.engine = None
    
    def get_connection_string(self):
        """Construit la chaîne de connexion SQLAlchemy."""
        return (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}"
            f"/{self.config['database']}"
        )
    
    def connect(self):
        """Etablit la connexion a PostgreSQL."""
        print(f"Connexion a {self.config['database']}...")
        
        try:
            conn_str = self.get_connection_string()
            self.engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                pool_size=10,
                pool_recycle=300,
            )
            print("Connexion reussie!")
            return True
        except Exception as e:
            print(f"ERREUR de connexion : {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion."""
        if self.engine:
            self.engine.dispose()
        print("Connexion fermee.")
    
    def create_tables(self, sql_file="sql/create_tables.sql"):
        """Cree les tables a partir d'un fichier SQL.
        
        Args:
            sql_file: Chemin vers le fichier SQL
        """
        print(f"\nCreation des tables depuis {sql_file}...")
        
        # Chemin absolu vers le fichier SQL
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        sql_path = os.path.join(base_dir, sql_file)
        
        if not os.path.exists(sql_path):
            print(f"ERREUR : Fichier SQL non trouve : {sql_path}")
            return False
        
        try:
            with open(sql_path, "r") as f:
                sql_content = f.read()
            
            with self.engine.connect() as conn:
                conn.execute(text(sql_content))
                conn.commit()
            
            print("Tables creees avec succes!")
            return True
        except Exception as e:
            print(f"ERREUR lors de la creation des tables : {e}")
            return False
    
    def load_csv_file(self, csv_file, max_retries=3):
        """Charge un fichier CSV dans PostgreSQL.
        
        Args:
            csv_file: Chemin vers le fichier CSV
            max_retries: Nombre max de tentatives en cas d'echec
        """
        print(f"\nChargement de {csv_file}...")
        
        # Chemin absolu
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        csv_path = os.path.join(base_dir, csv_file)
        
        if not os.path.exists(csv_path):
            print(f"ERREUR : Fichier CSV non trouve : {csv_path}")
            return 0
        
        for attempt in range(1, max_retries + 1):
            try:
                # Lire le CSV
                df = pd.read_csv(csv_path)
                
                # Renommer les colonnes pour correspondre a la table SQL
                column_mapping = {
                    "transaction_date": "transaction_date",
                    "transaction_date_only": "transaction_date_only",
                    "transaction_hour": "transaction_hour",
                    "step": "step",
                    "type": "type",
                    "amount": "amount",
                    "nameOrig": "name_orig",
                    "oldbalanceOrg": "old_balance_org",
                    "newbalanceOrig": "new_balance_orig",
                    "nameDest": "name_dest",
                    "oldbalanceDest": "old_balance_dest",
                    "newbalanceDest": "new_balance_dest",
                    "isFraud": "is_fraud",
                    "isFlaggedFraud": "is_flagged_fraud",
                }
                df = df.rename(columns=column_mapping)
                
                # Nettoyer le pool avant chaque chargement
                self.engine.dispose()
                
                # Charger dans PostgreSQL
                rows_loaded = df.to_sql(
                    "transactions",
                    self.engine,
                    if_exists="append",
                    index=False,
                    chunksize=5000,
                )
                
                print(f"  {len(df):,} lignes chargees")
                return len(df)
                
            except Exception as e:
                print(f"  Tentative {attempt}/{max_retries} echouee : {e}")
                if attempt < max_retries:
                    wait = attempt * 5
                    print(f"  Nouvelle tentative dans {wait}s...")
                    time.sleep(wait)
                    # Nettoyer le pool avant retry
                    self.engine.dispose()
                else:
                    print(f"  ERREUR : Abandon apres {max_retries} tentatives.")
                    return 0
    
    def load_all_processed_files(self):
        """Charge tous les fichiers transformes."""
        print("\n" + "=" * 60)
        print("CHARGEMENT DE TOUS LES FICHIERS")
        print("=" * 60)
        
        # Chemin vers le dossier processed
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        processed_dir = os.path.join(base_dir, "data", "processed")
        
        # Lister les fichiers
        files = sorted([
            f for f in os.listdir(processed_dir)
            if f.startswith("transactions_day_") and f.endswith(".csv")
        ])
        
        print(f"Fichiers trouves : {len(files)}")
        
        total_rows = 0
        for i, filename in enumerate(files, 1):
            csv_path = f"data/processed/{filename}"
            rows = self.load_csv_file(csv_path)
            total_rows += rows
            
            # Disposal periodique pour nettoyer le pool
            if i % 5 == 0:
                self.engine.dispose()
                print(f"  [Pool reset apres {i} fichiers]")
        
        print("\n" + "-" * 60)
        print(f"Total : {total_rows:,} lignes chargees")
        print("-" * 60)
        
        return total_rows
    
    def verify_loading(self):
        """Verifie que les donnees ont ete chargees correctement."""
        print("\n" + "=" * 60)
        print("VERIFICATION DU CHARGEMENT")
        print("=" * 60)
        
        try:
            with self.engine.connect() as conn:
                # Compter les lignes
                result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
                count = result.scalar()
                print(f"Nombre total de transactions : {count:,}")
                
                # Compter par type
                result = conn.execute(text("""
                    SELECT type, COUNT(*) as count 
                    FROM transactions 
                    GROUP BY type 
                    ORDER BY count DESC
                """))
                
                print("\nPar type de transaction :")
                for row in result:
                    print(f"  {row[0]:12s} | {row[1]:>10,}")
                
                # Compter les fraudes
                result = conn.execute(text("""
                    SELECT is_fraud, COUNT(*) as count 
                    FROM transactions 
                    GROUP BY is_fraud
                """))
                
                print("\nPar statut de fraude :")
                for row in result:
                    label = "Non-fraude" if row[0] == 0 else "Fraude"
                    print(f"  {label:12s} | {row[1]:>10,}")
            
            print("\nVerification reussie!")
            return True
            
        except Exception as e:
            print(f"ERREUR lors de la verification : {e}")
            return False


# ============================================
# Fonction utilitaire
# ============================================

def test_connection():
    """Teste la connexion a PostgreSQL."""
    db = DatabaseManager()
    if db.connect():
        db.disconnect()
        return True
    return False


# ============================================
# Programme principal
# ============================================

def main():
    """Fonction principale de chargement."""
    print("=" * 60)
    print("CHARGEMENT POSTGRESQL")
    print("=" * 60)
    
    # Creer le gestionnaire
    db = DatabaseManager()
    
    # Connecter
    if not db.connect():
        print("Impossible de se connecter a PostgreSQL.")
        print("Verifiez que le serveur est demarre.")
        sys.exit(1)
    
    # Creer les tables
    if not db.create_tables():
        print("Impossible de creer les tables.")
        sys.exit(1)
    
    # Charger les donnees
    total_rows = db.load_all_processed_files()
    
    # Verifier
    db.verify_loading()
    
    # Deconnecter
    db.disconnect()
    
    print("\n" + "=" * 60)
    print("CHARGEMENT TERMINE")
    print("=" * 60)


if __name__ == "__main__":
    main()
