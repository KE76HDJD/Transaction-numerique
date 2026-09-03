"""Tests unitaires pour l'ingestion batch."""

import pytest
from src.ingestion.ingest_batch import calculate_days, get_step_range


class TestCalculateDays:
    """Tests pour calculate_days()."""

    def test_24_steps_equals_1_day(self):
        assert calculate_days(1, 24) == 1

    def test_48_steps_equals_2_days(self):
        assert calculate_days(1, 48) == 2

    def test_743_steps_equals_31_days(self):
        assert calculate_days(1, 743) == 31

    def test_25_steps_equals_2_days(self):
        assert calculate_days(1, 25) == 2

    def test_non_zero_start(self):
        assert calculate_days(25, 48) == 1


class TestGetStepRange:
    """Tests pour get_step_range()."""

    def test_simple_range(self):
        import pandas as pd
        df = pd.DataFrame({"step": [1, 5, 10, 24]})
        assert get_step_range(df) == (1, 24)

    def test_single_step(self):
        import pandas as pd
        df = pd.DataFrame({"step": [42]})
        assert get_step_range(df) == (42, 42)
