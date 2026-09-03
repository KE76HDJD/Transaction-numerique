"""
Script d'ingestion batch - Decoupage journalier.

Ce script lit le dataset original et le decoupe en lots journaliers.
Chaque lot represente 24 heures (steps) de transactions.

Convention :
    - step 1-24   → day_01.csv (Jour 1)
    - step 25-48  → day_02.csv (Jour 2)
    - step 49-72  → day_03.csv (Jour 3)
    - ...
    - step 721-743 → day_31.csv (Jour 31)

Usage :
    python -m src.ingestion.ingest_batch
"""

import pandas as pd
import os
import sys


# ============================================
# Configuration
# ============================================

# Chemins relatifs au script
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
SOURCE_DIR = os.path.join(BASE_DIR, "data", "source")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

# Fichier source
SOURCE_FILE = os.path.join(SOURCE_DIR, "PS_20174392719_1491204439457_log.csv")

# Nombre d'heures par jour
HOURS_PER_DAY = 24


# ============================================
# Fonctions
# ============================================

def ensure_directories():
    """Cree les dossiers necessaires s'ils n'existent pas."""
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Dossier de destination : {RAW_DIR}")


def load_source_data(filepath):
    """Charge le dataset source."""
    print(f"\nChargement du fichier : {filepath}")

    if not os.path.exists(filepath):
        print(f"ERREUR : Fichier non trouve : {filepath}")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"Charge : {len(df):,} lignes, {df.shape[1]} colonnes")
    return df


def get_step_range(df):
    """Retourne la plage de steps (min, max)."""
    step_min = int(df["step"].min())
    step_max = int(df["step"].max())
    return step_min, step_max


def calculate_days(step_min, step_max):
    """Calcule le nombre de jours a creer."""
    total_steps = step_max - step_min + 1
    num_days = (total_steps + HOURS_PER_DAY - 1) // HOURS_PER_DAY
    return num_days


def split_and_save(df, step_min, step_max, num_days):
    """Decoupe le dataframe par jour et sauvegarde chaque lot."""
    print(f"\nDecoupage en {num_days} lots journaliers...")
    print("-" * 50)

    total_rows = 0

    for day_num in range(1, num_days + 1):
        # Calculer la plage de steps pour ce jour
        day_start = step_min + (day_num - 1) * HOURS_PER_DAY
        day_end = min(day_start + HOURS_PER_DAY - 1, step_max)

        # Filtrer les donnees pour ce jour
        day_data = df[(df["step"] >= day_start) & (df["step"] <= day_end)]

        # Nom du fichier
        filename = f"day_{day_num:02d}.csv"
        filepath = os.path.join(RAW_DIR, filename)

        # Sauvegarder
        day_data.to_csv(filepath, index=False)

        # Stats
        num_rows = len(day_data)
        total_rows += num_rows
        print(f"  {filename} | Steps {day_start:3d}-{day_end:3d} | {num_rows:>8,} lignes")

    print("-" * 50)
    print(f"Total : {total_rows:,} lignes sauvegardees dans {num_days} fichiers")
    return total_rows


def print_summary(num_days, total_rows):
    """Affiche le resume de l'ingestion."""
    print("\n" + "=" * 50)
    print("RESUME DE L'INGESTION")
    print("=" * 50)
    print(f"  Source        : {SOURCE_FILE}")
    print(f"  Destination   : {RAW_DIR}")
    print(f"  Fichiers crees: {num_days}")
    print(f"  Total lignes  : {total_rows:,}")
    print(f"  Format        : day_01.csv, day_02.csv, ..., day_{num_days:02d}.csv")
    print("=" * 50)


# ============================================
# Programme principal
# ============================================

def main():
    """Fonction principale d'ingestion batch."""
    print("=" * 50)
    print("INGESTION BATCH - DECOUPAGE JOURNALIER")
    print("=" * 50)

    # 1. Creer les dossiers
    ensure_directories()

    # 2. Charger les donnees
    df = load_source_data(SOURCE_FILE)

    # 3. Obtenir la plage de steps
    step_min, step_max = get_step_range(df)
    print(f"\nPlage de steps : {step_min} a {step_max}")

    # 4. Calculer le nombre de jours
    num_days = calculate_days(step_min, step_max)
    print(f"Nombre de jours : {num_days}")

    # 5. Decouper et sauvegarder
    total_rows = split_and_save(df, step_min, step_max, num_days)

    # 6. Resume
    print_summary(num_days, total_rows)


if __name__ == "__main__":
    main()
