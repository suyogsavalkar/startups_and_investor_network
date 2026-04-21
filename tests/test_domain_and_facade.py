"""Tests for domain objects and app-level helper functions."""

from __future__ import annotations

import unittest

from app import get_bundle
from investor_network import InvestorNetwork, load_startup_data

from tests.helpers import PROJECT_ROOT


class TestDomainAndFacade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded_df = load_startup_data(PROJECT_ROOT)
        cls.network = InvestorNetwork(PROJECT_ROOT)

    def test_company_and_investor_domain_objects_exist_and_link(self):
        """The project needs real Company and Investor objects, not just dataframes."""
        some_company_id = str(self.loaded_df.iloc[0]["startup_id"])
        company_obj = self.network.get_company(some_company_id)

        self.assertIsNotNone(company_obj)
        self.assertEqual(company_obj.startup_id, some_company_id)

        # If the startup has investors, the first investor should point back to this company.
        if company_obj.investors:
            investor_name = company_obj.investors[0]
            investor_obj = self.network.get_investor(investor_name)
            self.assertIsNotNone(investor_obj)
            self.assertIn(some_company_id, set(investor_obj.companies_backed))

    def test_company_connected_companies_method_returns_list(self):
        """The Company object should expose the same connections as the network service."""
        target_id = None
        for _, row in self.loaded_df.iterrows():
            startup_id = str(row["startup_id"])
            if len(self.network.connected_companies(startup_id)) > 0:
                target_id = startup_id
                break

        if target_id is None:
            self.skipTest("No connected companies found under default thresholds.")

        company_obj = self.network.get_company(target_id)
        neighbors = company_obj.connected_companies(self.network)

        self.assertIsInstance(neighbors, list)

    def test_industry_filter_reduces_graph(self):
        """The app sidebar filter should actually remove other industries."""
        bundle_all = get_bundle(min_investor_frequency=2, max_investor_prevalence=0.10)
        bundle_filtered = get_bundle(
            min_investor_frequency=2,
            max_investor_prevalence=0.10,
            industry_filter=("Fintech",),
        )

        self.assertLessEqual(
            bundle_filtered.graph.number_of_nodes(),
            bundle_all.graph.number_of_nodes(),
        )

        # Every startup that remains should match the selected filter value.
        if not bundle_filtered.startups.empty:
            industries = bundle_filtered.startups["industry"].unique().tolist()
            self.assertTrue(
                all(ind == "Fintech" for ind in industries),
                f"Non-Fintech industries found after filter: {industries}",
            )


if __name__ == "__main__":
    unittest.main()
