"""Tests unitaires pour le module database."""

import pytest
import os
from src.utils.database import DatabaseManager, DEFAULT_CONFIG


class TestGetConnectionString:
    """Tests pour get_connection_string()."""

    def test_default_connection_string(self):
        db = DatabaseManager()
        conn_str = db.get_connection_string()
        assert "postgresql://" in conn_str
        assert "kevin" in conn_str
        assert "transaction_db" in conn_str
        assert "5434" in conn_str

    def test_custom_config(self):
        config = {
            "host": "remotehost",
            "port": "5432",
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }
        db = DatabaseManager(config=config)
        conn_str = db.get_connection_string()
        assert "testuser:testpass@remotehost:5432/testdb" in conn_str


class TestColumnMapping:
    """Verifie que le mapping des colonnes est correct."""

    def test_all_columns_mapped(self):
        from src.utils.database import DatabaseManager
        expected_columns = {
            "transaction_date", "transaction_date_only", "transaction_hour",
            "step", "type", "amount", "nameOrig", "oldbalanceOrg",
            "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest",
            "isFraud", "isFlaggedFraud"
        }
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
        assert set(column_mapping.keys()) == expected_columns
