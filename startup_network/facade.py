"""Function-style facade API for the startup network package."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import (
    DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    DEFAULT_MIN_INVESTOR_FREQUENCY,
)
from .graph_builder import build_network_bundle
from .parsing import parse_investor_cell
from .queries import connected_companies, path_edges, rank_startups, shortest_path
from .service import load_investor_network
from .types import NetworkBundle


def load_startup_data(base_dir: str | Path | None = None) -> pd.DataFrame:
    """Load canonical startup data with parsed investor lists.

    Parameters
    ----------
    base_dir : str | Path | None
        Directory containing CSV files.

    Returns
    -------
    pd.DataFrame
        Canonical startup rows plus `investors_list` parsed column.
    """
    network = load_investor_network(base_dir)
    df = network.startup_table.copy()
    df["investors_list"] = df["investors_raw"].apply(parse_investor_cell)
    return df


def build_network(
    startups_df: pd.DataFrame,
    min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
    max_investor_prevalence: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    min_edge_weight: int = 1,
) -> NetworkBundle:
    """Build a `NetworkBundle` from a startup dataframe.

    Parameters
    ----------
    startups_df : pd.DataFrame
        Startup rows to graph.
    min_investor_frequency : int
        Minimum startup count required for investor inclusion.
    max_investor_prevalence : float
        Maximum startup prevalence fraction allowed.
    min_edge_weight : int
        Minimum shared-investor count required for edge inclusion.

    Returns
    -------
    NetworkBundle
        Built graph bundle with diagnostics.
    """
    return build_network_bundle(
        startups_df=startups_df,
        min_investor_frequency=min_investor_frequency,
        max_investor_prevalence=max_investor_prevalence,
        min_edge_weight=min_edge_weight,
    )


__all__ = [
    "NetworkBundle",
    "build_network",
    "connected_companies",
    "load_startup_data",
    "path_edges",
    "rank_startups",
    "shortest_path",
]
