"""
Script d'exploration du dataset de transactions.

Ce script analyse le fichier CSV original pour comprendre :
- La structure (colonnes, types)
- Le volume des données
- Les valeurs manquantes
- Les doublons
- La distribution de la colonne step

Usage :
    python -m src.ingestion.explore_data
"""

import pandas as pd
import os


# ============================================
# Configuration
# ============================================

# Chemin vers le dataset original
SOURCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "source")
SOURCE_FILE = os.path.join(SOURCE_DIR, "PS_20174392719_1491204439457_log.csv")


# ============================================
# Fonctions d'exploration
# ============================================

def load_data(filepath):
    """Charge le dataset CSV."""
    print("=" * 60)
    print("CHARGEMENT DU DATASET")
    print("=" * 60)
    df = pd.read_csv(filepath)
    print(f"Fichier charge : {filepath}")
    print(f"Nombre de lignes : {len(df):,}")
    print(f"Nombre de colonnes : {df.shape[1]}")
    print()
    return df


def explore_structure(df):
    """Affiche la structure du dataset."""
    print("=" * 60)
    print("STRUCTURE DU DATASET")
    print("=" * 60)

    print("\n--- Colonnes et types ---")
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        print(f"  {col:20s} | Type: {str(dtype):10s} | Non-null: {non_null:,}")

    print("\n--- 5 premieres lignes ---")
    print(df.head())

    print("\n--- Statistiques descriptives ---")
    print(df.describe())
    print()


def check_missing_values(df):
    """Detecte les valeurs manquantes."""
    print("=" * 60)
    print("VALEURS MANQUANTES")
    print("=" * 60)

    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100

    has_missing = False
    for col in df.columns:
        if missing[col] > 0:
            has_missing = True
            print(f"  {col:20s} | Manquants: {missing[col]:>10,} | {missing_pct[col]:.2f}%")

    if not has_missing:
        print("  Aucune valeur manquante detectee.")

    print()


def check_duplicates(df):
    """Detecte les doublons."""
    print("=" * 60)
    print("DOUBLONS")
    print("=" * 60)

    total_rows = len(df)
    unique_rows = len(df.drop_duplicates())
    duplicates = total_rows - unique_rows

    print(f"  Nombre total de lignes    : {total_rows:,}")
    print(f"  Nombre de lignes uniques  : {unique_rows:,}")
    print(f"  Nombre de doublons        : {duplicates:,}")

    if duplicates > 0:
        pct = (duplicates / total_rows) * 100
        print(f"  Pourcentage de doublons   : {pct:.2f}%")
    else:
        print("  Aucun doublon detecte.")

    print()


def explore_step(df):
    """Analyse la colonne step."""
    print("=" * 60)
    print("ANALYSE DE LA COLONNE STEP")
    print("=" * 60)

    step_min = df["step"].min()
    step_max = df["step"].max()
    step_unique = df["step"].nunique()

    print(f"  Valeur min     : {step_min}")
    print(f"  Valeur max     : {step_max}")
    print(f"  Valeurs uniques: {step_unique}")
    print(f"  Total heures   : {step_max} h")
    print(f"  Jours couverts : {step_max / 24:.1f} jours")

    print("\n--- Distribution des transactions par step (10 premiers) ---")
    step_counts = df["step"].value_counts().sort_index()
    for step in range(step_min, min(step_min + 10, step_max + 1)):
        count = step_counts.get(step, 0)
        print(f"  Step {step:3d} | {count:>8,} transactions")

    print()


def explore_transaction_types(df):
    """Analyse les types de transactions."""
    print("=" * 60)
    print("TYPES DE TRANSACTIONS")
    print("=" * 60)

    type_counts = df["type"].value_counts()
    total = len(df)

    for txn_type, count in type_counts.items():
        pct = (count / total) * 100
        print(f"  {txn_type:12s} | {count:>10,} | {pct:.1f}%")

    print()


def explore_amounts(df):
    """Analyse des montants."""
    print("=" * 60)
    print("ANALYSE DES MONTANTS")
    print("=" * 60)

    print(f"  Montant min  : {df['amount'].min():>15,.2f}")
    print(f"  Montant max  : {df['amount'].max():>15,.2f}")
    print(f"  Montant moy  : {df['amount'].mean():>15,.2f}")
    print(f"  Montant median: {df['amount'].median():>15,.2f}")

    print("\n--- Montants par type de transaction ---")
    for txn_type in df["type"].unique():
        subset = df[df["type"] == txn_type]["amount"]
        print(f"  {txn_type:12s} | Moy: {subset.mean():>12,.2f} | Max: {subset.max():>12,.2f}")

    print()


def explore_fraud(df):
    """Analyse des fraudes."""
    print("=" * 60)
    print("ANALYSE DES FRAUDES")
    print("=" * 60)

    fraud_counts = df["isFraud"].value_counts()
    total = len(df)

    for label, count in fraud_counts.items():
        pct = (count / total) * 100
        label_text = "Non-fraude" if label == 0 else "Fraude"
        print(f"  {label_text:12s} | {count:>10,} | {pct:.2f}%")

    print()


# ============================================
# Programme principal
# ============================================

def main():
    """Fonction principale d'exploration."""
    # Verifier que le fichier existe
    if not os.path.exists(SOURCE_FILE):
        print(f"ERREUR : Fichier non trouve : {SOURCE_FILE}")
        return

    # Charger les donnees
    df = load_data(SOURCE_FILE)

    # Explorer la structure
    explore_structure(df)

    # Verifier les valeurs manquantes
    check_missing_values(df)

    # Verifier les doublons
    check_duplicates(df)

    # Explorer la colonne step
    explore_step(df)

    # Explorer les types de transactions
    explore_transaction_types(df)

    # Explorer les montants
    explore_amounts(df)

    # Explorer les fraudes
    explore_fraud(df)

    print("=" * 60)
    print("EXPLORATION TERMINEE")
    print("=" * 60)


if __name__ == "__main__":
    main()
