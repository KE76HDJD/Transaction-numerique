"""Tests unitaires pour la transformation des transactions."""

import pytest
from datetime import datetime
from src.transformation.transform_transactions import convert_step_to_timestamp, REFERENCE_DATE


class TestConvertStepToTimestamp:
    """Tests pour convert_step_to_timestamp()."""

    def test_step_1_is_reference_date(self):
        assert convert_step_to_timestamp(1) == datetime(2024, 1, 1, 0, 0, 0)

    def test_step_2_is_plus_1_hour(self):
        assert convert_step_to_timestamp(2) == datetime(2024, 1, 1, 1, 0, 0)

    def test_step_24_is_end_of_day_1(self):
        assert convert_step_to_timestamp(24) == datetime(2024, 1, 1, 23, 0, 0)

    def test_step_25_is_day_2(self):
        assert convert_step_to_timestamp(25) == datetime(2024, 1, 2, 0, 0, 0)

    def test_step_743_is_day_31(self):
        result = convert_step_to_timestamp(743)
        assert result.day == 31
        assert result.hour == 22

    def test_string_input(self):
        assert convert_step_to_timestamp("5") == datetime(2024, 1, 1, 4, 0, 0)
