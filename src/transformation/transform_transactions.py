"""
Script de transformation des transactions.

Ce script lit les fichiers bruts (data/raw/day_XX.csv) et les transforme :
1. Convertit la colonne step en timestamp (date de reference : 2024-01-01)
2. Nettoie les donnees (doublons, valeurs manquantes)
3. Valide les types de donnees
4. Sauvegarde les resultats dans data/processed/

Convention de conversion step → timestamp :
    - step 1 = 2024-01-01 00:00:00
    - step 2 = 2024-01-01 01:00:00
    - step 24 = 2024-01-01 23:00:00
    - step 25 = 2024-01-02 00:00:00
    - etc.

Usage :
    python -m src.transformation.transform_transactions
"""

import pandas as pd
import os
import sys
from datetime import datetime, timedelta


# ============================================
# Configuration
# ============================================

# Chemins
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Date de reference pour la conversion step → timestamp
REFERENCE_DATE = datetime(2024, 1, 1, 0, 0, 0)


# ============================================
# Fonctions de transformation
# ============================================

def ensure_directories():
    """Cree le dossier processed s'il n'existe pas."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"Dossier de destination : {PROCESSED_DIR}")


def get_raw_files():
    """Liste tous les fichiers bruts disponibles."""
    files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith("day_") and f.endswith(".csv")])
    return files


def convert_step_to_timestamp(step_value):
    """Convertit un step en timestamp.
    
    Args:
        step_value: Valeur du step (entier)
    
    Returns:
        datetime correspondant
    """
    # Ajouter (step - 1) heures a la date de reference
    return REFERENCE_DATE + timedelta(hours=int(step_value) - 1)


def transform_single_file(filename):
    """Transforme un seul fichier brut.
    
    Etapes :
    1. Lire le CSV
    2. Convertir step en timestamp
    3. Ajouter les colonnes date et heure
    4. Nettoyer les doublons
    5. Valider les types
    """
    filepath = os.path.join(RAW_DIR, filename)
    
    # 1. Lire le CSV
    df = pd.read_csv(filepath)
    initial_rows = len(df)
    
    # 2. Convertir step en timestamp
    df["transaction_date"] = df["step"].apply(convert_step_to_timestamp)
    
    # 3. Extraire date et heure separes
    df["transaction_date_only"] = df["transaction_date"].dt.date
    df["transaction_hour"] = df["transaction_date"].dt.hour
    
    # 4. Nettoyer les doublons
    df = df.drop_duplicates()
    rows_after_dedup = len(df)
    
    # 5. Valider les types de donnees
    df["amount"] = df["amount"].astype(float)
    df["oldbalanceOrg"] = df["oldbalanceOrg"].astype(float)
    df["newbalanceOrig"] = df["newbalanceOrig"].astype(float)
    df["oldbalanceDest"] = df["oldbalanceDest"].astype(float)
    df["newbalanceDest"] = df["newbalanceDest"].astype(float)
    df["isFraud"] = df["isFraud"].astype(int)
    df["isFlaggedFraud"] = df["isFlaggedFraud"].astype(int)
    
    # 6. Reordonner les colonnes pour plus de lisibilite
    columns_order = [
        "transaction_date",
        "transaction_date_only",
        "transaction_hour",
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud"
    ]
    df = df[columns_order]
    
    return df, initial_rows, rows_after_dedup


def save_transformed_data(df, filename):
    """Sauvegarde les donnees transformees."""
    # Renommer le fichier : day_01.csv → transactions_day_01.csv
    output_filename = filename.replace("day_", "transactions_day_")
    filepath = os.path.join(PROCESSED_DIR, output_filename)
    df.to_csv(filepath, index=False)
    return filepath


def process_all_files():
    """Traite tous les fichiers bruts."""
    print("\nTraitement des fichiers...")
    print("-" * 60)
    
    files = get_raw_files()
    print(f"Fichiers trouves : {len(files)}")
    
    total_initial = 0
    total_final = 0
    
    for filename in files:
        # Transformer
        df, initial_rows, final_rows = transform_single_file(filename)
        
        # Sauvegarder
        filepath = save_transformed_data(df, filename)
        
        # Statistiques
        total_initial += initial_rows
        total_final += final_rows
        duplicates_removed = initial_rows - final_rows
        
        print(f"  {filename} → {os.path.basename(filepath)}")
        print(f"    Lignes: {initial_rows:,} → {final_rows:,} | Doublons supprimes: {duplicates_removed:,}")
    
    print("-" * 60)
    return total_initial, total_final


def print_summary(total_initial, total_final):
    """Affiche le resume de la transformation."""
    duplicates_total = total_initial - total_final
    
    print("\n" + "=" * 60)
    print("RESUME DE LA TRANSFORMATION")
    print("=" * 60)
    print(f"  Source            : {RAW_DIR}")
    print(f"  Destination       : {PROCESSED_DIR}")
    print(f"  Lignes initiales  : {total_initial:,}")
    print(f"  Lignes finales    : {total_final:,}")
    print(f"  Doublons supprimes: {duplicates_total:,}")
    print(f"  Date de reference : {REFERENCE_DATE}")
    print(f"  Format            : transactions_day_01.csv, ..., transactions_day_31.csv")
    print("=" * 60)


# ============================================
# Programme principal
# ============================================

def main():
    """Fonction principale de transformation."""
    print("=" * 60)
    print("TRANSFORMATION DES TRANSACTIONS")
    print("=" * 60)
    
    # 1. Creer les dossiers
    ensure_directories()
    
    # 2. Verifier les fichiers bruts
    files = get_raw_files()
    if not files:
        print("ERREUR : Aucun fichier brut trouve dans data/raw/")
        print("Veuillez d'abord executer l'ingestion : python -m src.ingestion.ingest_batch")
        sys.exit(1)
    
    # 3. Traiter tous les fichiers
    total_initial, total_final = process_all_files()
    
    # 4. Resume
    print_summary(total_initial, total_final)


if __name__ == "__main__":
    main()
