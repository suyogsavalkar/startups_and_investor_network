"""Service object for loading startup data and serving graph queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from .constants import (
    DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    DEFAULT_MIN_INVESTOR_FREQUENCY,
)
from .data_loader import load_unified_startup_table
from .graph_builder import build_graph_from_indices, eligible_investors
from .indices import build_domain_objects, build_investor_indices, investor_co_investors
from .models import Company, Investor
from .queries import (
    centrality_ranking,
    connected_companies_for_graph,
    diagnostics_summary,
    shortest_path_records,
)
from .types import GraphConfig


class InvestorNetwork:
    """Load startup datasets and expose graph queries.

    Parameters
    ----------
    data_dir : str | Path | None
        Directory containing project CSV files.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[1]

        self.startup_table: pd.DataFrame = load_unified_startup_table(self.data_dir)

        self.investor_display_map, self.startup_to_investors, self.investor_to_startups = build_investor_indices(
            self.startup_table
        )
        self.companies_by_id, self.investors_by_norm = build_domain_objects(
            startup_table=self.startup_table,
            startup_to_investors=self.startup_to_investors,
            investor_to_startups=self.investor_to_startups,
            investor_display_map=self.investor_display_map,
        )

        self._graph_cache: dict[GraphConfig, nx.Graph] = {}

    def get_company(self, startup_id: str) -> Company | None:
        """Return a company object for a startup id.

        Parameters
        ----------
        startup_id : str
            Startup identifier.

        Returns
        -------
        Company | None
            Matching company object when present.
        """
        return self.companies_by_id.get(startup_id)

    def get_investor(self, investor_name: str) -> Investor | None:
        """Return an investor object by raw or normalized name.

        Parameters
        ----------
        investor_name : str
            Raw or normalized investor name.

        Returns
        -------
        Investor | None
            Matching investor object when present.
        """
        from .parsing import normalize_investor_name

        normalized = normalize_investor_name(investor_name)
        if not normalized:
            return None
        return self.investors_by_norm.get(normalized)

    def investor_co_investors(
        self,
        investor_name: str,
        min_shared_companies: int = 1,
    ) -> list[dict[str, Any]]:
        """Return co-investor rows for the provided investor.

        Parameters
        ----------
        investor_name : str
            Investor name in raw or normalized form.
        min_shared_companies : int
            Minimum shared startup count required.

        Returns
        -------
        list[dict[str, Any]]
            Co-investor rows sorted by shared-company count.
        """
        return investor_co_investors(
            investor_name=investor_name,
            get_investor_fn=self.get_investor,
            investor_to_startups=self.investor_to_startups,
            investor_display_map=self.investor_display_map,
            companies_by_id=self.companies_by_id,
            min_shared_companies=min_shared_companies,
        )

    def eligible_investors(
        self,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> set[str]:
        """Return eligible investors for the provided thresholds.

        Parameters
        ----------
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.

        Returns
        -------
        set[str]
            Normalized investor keys that pass filtering.
        """
        return eligible_investors(
            investor_to_startups=self.investor_to_startups,
            n_startups=len(self.startup_table),
            min_investor_frequency=min_investor_frequency,
            max_investor_prevalence_fraction=max_investor_prevalence_fraction,
        )

    def build_graph(
        self,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> nx.Graph:
        """Build and return a weighted startup graph.

        Parameters
        ----------
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.

        Returns
        -------
        nx.Graph
            Startup graph where edge weight equals shared-investor count.
        """
        config = GraphConfig(min_investor_frequency, max_investor_prevalence_fraction)
        if config in self._graph_cache:
            return self._graph_cache[config]

        graph, _ = build_graph_from_indices(
            startup_table=self.startup_table,
            investor_to_startups=self.investor_to_startups,
            min_investor_frequency=min_investor_frequency,
            max_investor_prevalence_fraction=max_investor_prevalence_fraction,
        )
        self._graph_cache[config] = graph
        return graph

    def connected_companies(
        self,
        startup_id: str,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> list[dict[str, Any]]:
        """Return neighboring startups for one startup.

        Parameters
        ----------
        startup_id : str
            Startup id to inspect.
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.

        Returns
        -------
        list[dict[str, Any]]
            Neighbor rows with shared-investor details.
        """
        graph = self.build_graph(min_investor_frequency, max_investor_prevalence_fraction)
        return connected_companies_for_graph(
            graph=graph,
            startup_id=startup_id,
            investor_display_map=self.investor_display_map,
        )

    def shortest_path(
        self,
        source_startup_id: str,
        target_startup_id: str,
        weighted: bool = False,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> list[dict[str, str]]:
        """Return shortest startup path records between two startups.

        Parameters
        ----------
        source_startup_id : str
            Source startup id.
        target_startup_id : str
            Target startup id.
        weighted : bool
            If True, prefer stronger links using inverse distance.
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.

        Returns
        -------
        list[dict[str, str]]
            Path rows with `startup_id` and `company` fields.
        """
        graph = self.build_graph(min_investor_frequency, max_investor_prevalence_fraction)
        return shortest_path_records(
            graph=graph,
            source_startup_id=source_startup_id,
            target_startup_id=target_startup_id,
            weighted=weighted,
        )

    def centrality_ranking(
        self,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
        top_n: int = 25,
        sort_by: str = "weighted_degree",
    ) -> pd.DataFrame:
        """Return startup ranking table by centrality metric.

        Parameters
        ----------
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.
        top_n : int
            Number of rows to return.
        sort_by : str
            Sort metric: `degree`, `weighted_degree`, or `betweenness`.

        Returns
        -------
        pd.DataFrame
            Ranked startup rows.
        """
        graph = self.build_graph(min_investor_frequency, max_investor_prevalence_fraction)
        return centrality_ranking(graph=graph, top_n=top_n, sort_by=sort_by)

    def diagnostics_summary(
        self,
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> dict[str, float | int]:
        """Return graph diagnostics for current threshold settings.

        Parameters
        ----------
        min_investor_frequency : int
            Minimum startup count required for investor inclusion.
        max_investor_prevalence_fraction : float
            Maximum startup prevalence fraction allowed.

        Returns
        -------
        dict[str, float | int]
            Diagnostic statistics for data quality and graph structure.
        """
        graph = self.build_graph(min_investor_frequency, max_investor_prevalence_fraction)
        eligible = self.eligible_investors(min_investor_frequency, max_investor_prevalence_fraction)
        return diagnostics_summary(
            startup_count=len(self.startup_table),
            graph=graph,
            investor_to_startups=self.investor_to_startups,
            eligible_investors_set=eligible,
        )


def load_investor_network(data_dir: str | Path | None = None) -> InvestorNetwork:
    """Construct an `InvestorNetwork` instance.

    Parameters
    ----------
    data_dir : str | Path | None
        Directory containing the project CSV files.

    Returns
    -------
    InvestorNetwork
        Ready-to-query network service instance.
    """
    return InvestorNetwork(data_dir=data_dir)
