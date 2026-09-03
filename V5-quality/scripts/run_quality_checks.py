"""
V5 — Great Expectations Quality Checks
Verifie la qualite des donnees dans PostgreSQL
"""

import os
import sys
import json
import pandas as pd
import psycopg2
from datetime import datetime

# Configuration
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5434")),
    "database": os.getenv("PG_DB", "transaction_db"),
    "user": os.getenv("PG_USER", "kevin"),
    "password": os.getenv("PG_PASSWORD", "kevin123"),
}


def get_connection():
    """Cree la connexion PostgreSQL."""
    return psycopg2.connect(**PG_CONFIG)


def load_expectations():
    """Charge les expectations depuis le fichier JSON."""
    expectations_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "great_expectations",
        "expectations",
        "transactions.json"
    )
    with open(expectations_path) as f:
        return json.load(f)


def check_not_null(df, column):
    """Verifie que la colonne n'a pas de null."""
    null_count = df[column].isnull().sum()
    total = len(df)
    passed = null_count == 0
    return {
        "expectation": f"not_null({column})",
        "passed": passed,
        "null_count": int(null_count),
        "total": total,
        "success_rate": (total - null_count) / total if total > 0 else 0,
    }


def check_in_set(df, column, value_set):
    """Verifie que les valeurs sont dans l'ensemble autorise."""
    invalid = df[~df[column].isin(value_set)]
    total = len(df)
    passed = len(invalid) == 0
    return {
        "expectation": f"in_set({column})",
        "passed": passed,
        "invalid_count": len(invalid),
        "total": total,
        "success_rate": (total - len(invalid)) / total if total > 0 else 0,
    }


def check_between(df, column, min_val, max_val):
    """Verifie que les valeurs sont dans la plage."""
    out_of_range = df[(df[column] < min_val) | (df[column] > max_val)]
    total = len(df)
    passed = len(out_of_range) == 0
    return {
        "expectation": f"between({column}, {min_val}, {max_val})",
        "passed": passed,
        "out_of_range_count": len(out_of_range),
        "total": total,
        "success_rate": (total - len(out_of_range)) / total if total > 0 else 0,
    }


def check_regex(df, column, regex):
    """Verifie que les valeurs matchent le regex."""
    import re
    pattern = re.compile(regex)
    non_matching = df[~df[column].astype(str).str.match(pattern)]
    total = len(df)
    passed = len(non_matching) == 0
    return {
        "expectation": f"regex({column}, {regex})",
        "passed": passed,
        "non_matching_count": len(non_matching),
        "total": total,
        "success_rate": (total - len(non_matching)) / total if total > 0 else 0,
    }


def check_unique(df, column):
    """Verifie l'unicite des valeurs."""
    duplicates = df[df.duplicated(subset=[column], keep=False)]
    total = len(df)
    unique_count = df[column].nunique()
    passed = len(duplicates) == 0
    return {
        "expectation": f"unique({column})",
        "passed": passed,
        "duplicate_count": len(duplicates),
        "unique_count": unique_count,
        "total": total,
        "success_rate": unique_count / total if total > 0 else 0,
    }


def run_quality_checks():
    """Lance tous les checks de qualite."""
    print("=" * 60)
    print("GREAT EXPECTATIONS — Quality Checks")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Connexion
    conn = get_connection()
    print("Connecte a PostgreSQL")

    # Charger les donnees (echantillon pour rapidite)
    query = "SELECT * FROM transactions LIMIT 100000"
    df = pd.read_sql(query, conn)
    print(f"Charge {len(df):,} lignes (echantillon)")
    print()

    # Results
    results = []

    # 1. Not null checks
    for col in ["amount", "type", "name_orig"]:
        result = check_not_null(df, col)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['expectation']}")

    # 2. In set check
    valid_types = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]
    result = check_in_set(df, "type", valid_types)
    results.append(result)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['expectation']}")

    # 3. Between check
    result = check_between(df, "amount", 0, 10000000)
    results.append(result)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['expectation']}")

    # 4. Regex check
    result = check_regex(df, "name_orig", r"^C[0-9]+$")
    results.append(result)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['expectation']}")

    # 5. Unique check
    result = check_unique(df, "id")
    results.append(result)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['expectation']}")

    # 6. Row count check (query total count from DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_count = cursor.fetchone()[0]
    cursor.close()
    row_count_passed = 6000000 <= total_count <= 7000000
    results.append({
        "expectation": "row_count_between(6M, 7M)",
        "passed": row_count_passed,
        "actual_count": total_count,
    })
    status = "PASS" if row_count_passed else "FAIL"
    print(f"[{status}] row_count: {total_count:,}")

    # Resume
    print()
    print("=" * 60)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    score = (passed / total) * 100 if total > 0 else 0

    print(f"RESULTAT: {passed}/{total} tests passés")
    print(f"SCORE: {score:.1f}%")

    if score >= 90:
        print("STATUS: EXCELLENT")
    elif score >= 70:
        print("STATUS: BON")
    else:
        print("STATUS: ATTENTION REQUISE")

    print("=" * 60)

    # Sauvegarder les resultats
    save_results(results, score)

    conn.close()
    return results, score


def save_results(results, score):
    """Sauvegarde les resultats dans un fichier JSON."""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(output_dir, exist_ok=True)

    # Convert numpy types to Python types for JSON serialization
    def convert(obj):
        if hasattr(obj, 'item'):
            return obj.item()
        return obj

    output = {
        "timestamp": datetime.now().isoformat(),
        "score": convert(score),
        "results": [{k: convert(v) for k, v in r.items()} for r in results],
    }

    output_path = os.path.join(output_dir, "quality_results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResultats sauvegardes: {output_path}")


if __name__ == "__main__":
    run_quality_checks()
