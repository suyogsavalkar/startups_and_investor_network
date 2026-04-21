"""Compatibility module that re-exports the modular startup network API.

This project originally implemented all graph/data logic in this single file.
The logic now lives in the ``startup_network`` package, and this module keeps
existing imports stable.
"""

from startup_network import (
    CSV_2021,
    CSV_STARTUPS,
    Company,
    DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    DEFAULT_MIN_INVESTOR_FREQUENCY,
    GraphConfig,
    Investor,
    InvestorNetwork,
    NetworkBundle,
    build_network,
    connected_companies,
    load_investor_network,
    load_startup_data,
    normalize_investor_name,
    path_edges,
    rank_startups,
    shortest_path,
)

__all__ = [
    "CSV_2021",
    "CSV_STARTUPS",
    "Company",
    "DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION",
    "DEFAULT_MIN_INVESTOR_FREQUENCY",
    "GraphConfig",
    "Investor",
    "InvestorNetwork",
    "NetworkBundle",
    "build_network",
    "connected_companies",
    "load_investor_network",
    "load_startup_data",
    "normalize_investor_name",
    "path_edges",
    "rank_startups",
    "shortest_path",
]
