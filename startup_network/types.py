"""Shared datatypes for graph configuration and bundled outputs."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import pandas as pd


@dataclass(frozen=True)
class GraphConfig:
    """Configuration values used to cache graph builds.

    Parameters
    ----------
    min_investor_frequency : int
        Minimum number of startups an investor must appear in.
    max_investor_prevalence_fraction : float
        Maximum startup-prevalence fraction an investor may have.
    """

    min_investor_frequency: int
    max_investor_prevalence_fraction: float


@dataclass
class NetworkBundle:
    """Container for the filtered startup table, graph, and diagnostics.

    Parameters
    ----------
    startups : pd.DataFrame
        Filtered startup rows used to build the graph.
    graph : nx.Graph
        Startup-to-startup graph with shared-investor edge metadata.
    diagnostics : dict[str, float | int]
        Summary stats for the current graph build.
    eligible_investor_counts : dict[str, int]
        Mapping of eligible investor (normalized name) to startup count.
    """

    startups: pd.DataFrame
    graph: nx.Graph
    diagnostics: dict[str, float | int]
    eligible_investor_counts: dict[str, int]
