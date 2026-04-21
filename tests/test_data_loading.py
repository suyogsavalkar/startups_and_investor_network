"""Tests for CSV loading and investor parsing."""

from __future__ import annotations

import unittest

from investor_network import load_startup_data
from startup_network.parsing import normalize_investor_name, parse_investor_cell

from tests.helpers import PROJECT_ROOT


class TestDataLoading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded_df = load_startup_data(PROJECT_ROOT)

    def test_load_startup_data_has_required_columns_and_non_empty(self):
        """Everything else depends on the two CSVs becoming one clean table."""
        required = {
            "startup_id",
            "company",
            "industry",
            "country",
            "city",
            "valuation",
            "investors_raw",
            "dataset",
            "investors_list",
        }

        # If one of these columns disappears, the app pages and graph builder will break later.
        self.assertTrue(required.issubset(set(self.loaded_df.columns)))
        self.assertGreater(len(self.loaded_df), 0)

    def test_parse_investor_cell_removes_blank_entries(self):
        """Messy comma-separated investor cells should become usable lists."""
        parsed = parse_investor_cell(" Sequoia Capital, , Accel,  ")

        # Empty pieces should not become fake investor names in the graph.
        self.assertEqual(parsed, ["Sequoia Capital", "Accel"])

    def test_normalize_investor_name_matches_different_spacing_and_case(self):
        """Shared-investor edges only work if the same name normalizes consistently."""
        left = normalize_investor_name("  Sequoia   Capital ")
        right = normalize_investor_name("sequoia capital")

        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
