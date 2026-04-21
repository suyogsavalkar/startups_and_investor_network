"""Tests for search, path-finding, rankings, and explanations."""

from __future__ import annotations

import unittest

from investor_network import (
    build_network,
    connected_companies,
    path_edges,
    rank_startups,
    shortest_path,
)
from startup_network.explainers import deterministic_path_explanation

from tests.helpers import disconnected_startups, synthetic_startups, weighted_path_startups


class TestQueries(unittest.TestCase):
    def test_no_shared_investor_case_returns_no_path(self):
        """The Connections page should fail cleanly when no route exists."""
        bundle = build_network(
            disconnected_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        path = shortest_path(bundle, "x1", "x2", weighted=False)
        self.assertEqual(path, [])

    def test_connected_companies_sorted_by_weight_descending(self):
        """This because the Search page should show strongest related startups first."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        neighbors = connected_companies(bundle, "s1", top_n=10)

        # Gamma is first because it shares two investors with Alpha, while Beta shares one.
        self.assertEqual(list(neighbors["startup_id"]), ["s3", "s2"])
        self.assertEqual(list(neighbors["weight"]), [2, 1])

    def test_rank_startups_expected_columns_and_top_n_behavior(self):
        """This because the Rankings page needs a stable table shape and limit behavior."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        ranked = rank_startups(bundle, metric="weighted_degree", top_n=2)
        expected_columns = {"startup_id", "company", "industry", "country", "score", "metric"}

        self.assertTrue(expected_columns.issubset(set(ranked.columns)))
        self.assertEqual(len(ranked), 2)
        self.assertEqual(list(ranked["company"]), ["Alpha", "Gamma"])
        self.assertTrue((ranked["metric"] == "weighted_degree").all())

        # A top_n of zero is not useful, so the code intentionally returns at least one row.
        ranked_min = rank_startups(bundle, metric="weighted_degree", top_n=0)
        self.assertEqual(len(ranked_min), 1)

    def test_path_edges_returns_correct_hop_details(self):
        """This because the path display needs one row of investor details per hop."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        edge_df = path_edges(bundle, ["s1", "s2"])

        self.assertEqual(len(edge_df), 1)
        self.assertEqual(edge_df.iloc[0]["from_company"], "Alpha")
        self.assertEqual(edge_df.iloc[0]["to_company"], "Beta")
        self.assertEqual(int(edge_df.iloc[0]["shared_investor_count"]), 1)

    def test_same_startup_path_returns_single_node_no_edges(self):
        """This because selecting the same startup should not create a fake connection path."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        path = shortest_path(bundle, "s1", "s1", weighted=False)
        edge_df = path_edges(bundle, path)

        self.assertEqual(path, ["s1"])
        self.assertTrue(edge_df.empty)

    def test_weighted_shortest_path_prefers_stronger_connection(self):
        """weighted toggle should prefer stronger links, not just fewer hops."""
        bundle = build_network(
            weighted_path_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        unweighted = shortest_path(bundle, "a", "b", weighted=False)
        weighted = shortest_path(bundle, "a", "b", weighted=True)

        # The direct path is fewer hops, but the weighted path goes through the stronger Alpha-Gamma edge.
        self.assertEqual(unweighted, ["a", "b"])
        self.assertEqual(weighted, ["a", "c", "b"])

    def test_path_explanation_describes_every_hop(self):
        """the explanation shown in the app should name the companies on the path."""
        bundle = build_network(
            synthetic_startups(),
            min_investor_frequency=1,
            max_investor_prevalence=1.0,
            min_edge_weight=1,
        )

        path = shortest_path(bundle, "s1", "s3", weighted=False)
        edge_df = path_edges(bundle, path)
        companies = [bundle.graph.nodes[node_id].get("company", "") for node_id in path]
        explanation = deterministic_path_explanation(companies, edge_df, weighted=False)

        for company in companies:
            self.assertIn(company, explanation)
        self.assertIn(str(len(path) - 1), explanation)


if __name__ == "__main__":
    unittest.main()
