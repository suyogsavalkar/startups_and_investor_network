"""Tests for turning startup rows into a weighted investor graph."""

from __future__ import annotations

import unittest

from investor_network import build_network, load_startup_data

from tests.helpers import PROJECT_ROOT, synthetic_startups


class TestGraphBuilding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded_df = load_startup_data(PROJECT_ROOT)

    def test_build_graph_diagnostics_have_expected_keys_and_sane_values(self):
        """The Home page depends on these graph summary numbers being reliable."""
        bundle = build_network(
            self.loaded_df,
            min_investor_frequency=2,
            max_investor_prevalence=0.10,
            min_edge_weight=1,
        )

        expected_keys = {
            "n_startups",
            "n_investors_total",
            "n_investors_eligible",
            "n_edges",
            "density",
            "largest_component",
            "singleton_investor_pct",
        }
        self.assertTrue(expected_keys.issubset(set(bundle.diagnostics.keys())))

        n_startups = bundle.diagnostics["n_startups"]
        n_edges = bundle.diagnostics["n_edges"]
        density = bundle.diagnostics["density"]
        largest_component = bundle.diagnostics["largest_component"]
        n_total = bundle.diagnostics["n_investors_total"]
        n_eligible = bundle.diagnostics["n_investors_eligible"]
        singleton_pct = bundle.diagnostics["singleton_investor_pct"]

        # These checks catch impossible stats, like more eligible investors than total investors.
        self.assertEqual(n_startups, bundle.graph.number_of_nodes())
        self.assertEqual(n_edges, bundle.graph.number_of_edges())
        self.assertGreaterEqual(n_startups, 0)
        self.assertGreaterEqual(n_edges, 0)
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)
        self.assertGreaterEqual(largest_component, 0)
        self.assertLessEqual(largest_component, n_startups)
        self.assertGreaterEqual(n_total, 0)
        self.assertGreaterEqual(n_eligible, 0)
        self.assertLessEqual(n_eligible, n_total)
        self.assertGreaterEqual(singleton_pct, 0.0)
        self.assertLessEqual(singleton_pct, 100.0)

    def test_shared_investor_edges_created_correctly_on_synthetic_data(self):
        """A tiny hand-checkable dataset keeps the graph math obvious."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )
        graph = bundle.graph

        # Alpha, Beta, and Gamma should all connect because each pair shares at least one investor.
        self.assertTrue(graph.has_edge("s1", "s2"))
        self.assertTrue(graph.has_edge("s1", "s3"))
        self.assertTrue(graph.has_edge("s2", "s3"))

        # Alpha and Gamma share A and B, so that edge should be stronger than the others.
        self.assertEqual(graph["s1"]["s2"]["weight"], 1)
        self.assertEqual(graph["s2"]["s3"]["weight"], 1)
        self.assertEqual(graph["s1"]["s3"]["weight"], 2)
        self.assertEqual(set(graph["s1"]["s3"]["shared_investors"]), {"a", "b"})

    def test_min_edge_weight_filters_weak_connections(self):
        """The advanced sidebar can hide weak one-investor connections."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=2,
        )
        graph = bundle.graph

        # Only the pair with two shared investors should survive this stricter threshold.
        self.assertTrue(graph.has_edge("s1", "s3"))
        self.assertFalse(graph.has_edge("s1", "s2"))
        self.assertFalse(graph.has_edge("s2", "s3"))


if __name__ == "__main__":
    unittest.main()
