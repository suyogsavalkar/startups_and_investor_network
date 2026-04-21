"""Graph construction utilities for startup-investor networks."""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd

from .constants import (
    DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    DEFAULT_MIN_INVESTOR_FREQUENCY,
)
from .parsing import normalize_investor_name, parse_investor_cell
from .types import NetworkBundle


def eligible_investors(
    investor_to_startups: dict[str, set[str]],
    n_startups: int,
    min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
    max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
) -> set[str]:
    """Return investors passing frequency and prevalence filters.

    Parameters
    ----------
    investor_to_startups : dict[str, set[str]]
        Investor to startup-id mapping.
    n_startups : int
        Number of startups represented in the graph universe.
    min_investor_frequency : int
        Minimum startup count required for investor inclusion.
    max_investor_prevalence_fraction : float
        Maximum startup prevalence fraction allowed for inclusion.

    Returns
    -------
    set[str]
        Normalized investor keys that pass both filters.
    """
    if n_startups <= 0:
        return set()

    eligible: set[str] = set()
    for investor_norm, startup_ids in investor_to_startups.items():
        frequency = len(startup_ids)
        prevalence = frequency / n_startups
        if frequency >= min_investor_frequency and prevalence <= max_investor_prevalence_fraction:
            eligible.add(investor_norm)
    return eligible


def build_graph_from_indices(
    startup_table: pd.DataFrame,
    investor_to_startups: dict[str, set[str]],
    min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
    max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
) -> tuple[nx.Graph, set[str]]:
    """Build weighted startup graph from precomputed index mappings.

    Parameters
    ----------
    startup_table : pd.DataFrame
        Canonical startup table.
    investor_to_startups : dict[str, set[str]]
        Investor to startup-id mapping.
    min_investor_frequency : int
        Minimum startup count required for investor inclusion.
    max_investor_prevalence_fraction : float
        Maximum startup prevalence fraction allowed for inclusion.

    Returns
    -------
    tuple[nx.Graph, set[str]]
        Graph and set of eligible normalized investor keys.
    """
    graph = nx.Graph()
    startup_lookup = startup_table.set_index("startup_id", drop=False)

    for startup_id, startup_row in startup_lookup.iterrows():
        graph.add_node(
            startup_id,
            company=startup_row["company"],
            industry=startup_row["industry"],
            country=startup_row["country"],
            city=startup_row["city"],
            valuation=startup_row["valuation"],
            dataset=startup_row["dataset"],
        )

    eligible = eligible_investors(
        investor_to_startups=investor_to_startups,
        n_startups=len(startup_table),
        min_investor_frequency=min_investor_frequency,
        max_investor_prevalence_fraction=max_investor_prevalence_fraction,
    )

    for investor_norm in eligible:
        startups_for_investor = sorted(investor_to_startups.get(investor_norm, set()))
        if len(startups_for_investor) < 2:
            continue

        for source, target in combinations(startups_for_investor, 2):
            if graph.has_edge(source, target):
                graph[source][target]["weight"] += 1
                graph[source][target]["shared_investors"].append(investor_norm)
            else:
                graph.add_edge(
                    source,
                    target,
                    weight=1,
                    shared_investors=[investor_norm],
                )

    for source, target, edge_data in graph.edges(data=True):
        weight = float(edge_data["weight"])
        graph[source][target]["distance"] = 1.0 / weight if weight > 0 else float("inf")

    return graph, eligible


def build_network_bundle(
    startups_df: pd.DataFrame,
    min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
    max_investor_prevalence: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    min_edge_weight: int = 1,
) -> NetworkBundle:
    """Build a function-style NetworkBundle from a startup dataframe subset.

    Parameters
    ----------
    startups_df : pd.DataFrame
        Canonical startup rows with at least startup_id/company/investors data.
    min_investor_frequency : int
        Minimum startup count required for investor inclusion.
    max_investor_prevalence : float
        Maximum startup prevalence fraction allowed for investor inclusion.
    min_edge_weight : int
        Minimum shared-investor count required for edge inclusion.

    Returns
    -------
    NetworkBundle
        Startup rows, weighted graph, diagnostics, and eligible investor counts.
    """
    df = startups_df.copy()
    if "investors_list" not in df.columns:
        df["investors_list"] = df["investors_raw"].apply(parse_investor_cell)

    investor_to_startups: dict[str, set[str]] = {}
    startup_to_investors: dict[str, set[str]] = {}

    for row in df.itertuples(index=False):
        startup_id = str(row.startup_id)
        investors_list = row.investors_list if isinstance(row.investors_list, list) else []
        inv_norms = {normalize_investor_name(inv) for inv in investors_list if normalize_investor_name(inv)}
        startup_to_investors[startup_id] = inv_norms
        for inv in inv_norms:
            investor_to_startups.setdefault(inv, set()).add(startup_id)

    n_startups = max(len(df), 1)
    investor_counts = {inv: len(ids) for inv, ids in investor_to_startups.items()}
    eligible = {
        inv
        for inv, count in investor_counts.items()
        if count >= min_investor_frequency and (count / n_startups) <= max_investor_prevalence
    }

    graph = nx.Graph()
    for row in df.itertuples(index=False):
        sid = str(row.startup_id)
        invs = startup_to_investors.get(sid, set())
        graph.add_node(
            sid,
            company=getattr(row, "company", ""),
            industry=getattr(row, "industry", ""),
            country=getattr(row, "country", ""),
            city=getattr(row, "city", ""),
            valuation=getattr(row, "valuation", ""),
            dataset=getattr(row, "dataset", ""),
            investors_all=sorted(invs),
            investors_eligible=sorted(invs.intersection(eligible)),
        )

    pair_to_investors: dict[tuple[str, str], set[str]] = {}
    for inv in eligible:
        startups = sorted(investor_to_startups.get(inv, set()))
        for source, target in combinations(startups, 2):
            pair_to_investors.setdefault((source, target), set()).add(inv)

    for (source, target), shared_set in pair_to_investors.items():
        weight = len(shared_set)
        if weight < min_edge_weight:
            continue
        graph.add_edge(
            source,
            target,
            weight=weight,
            distance=1.0 / weight if weight > 0 else float("inf"),
            shared_investors=sorted(shared_set),
        )

    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    largest_component = len(components[0]) if components else 0

    singleton_count = sum(1 for c in investor_counts.values() if c == 1)
    singleton_pct = (singleton_count / max(len(investor_counts), 1)) * 100 if investor_counts else 0.0

    diagnostics = {
        "n_startups": int(graph.number_of_nodes()),
        "n_investors_total": int(len(investor_counts)),
        "n_investors_eligible": int(len(eligible)),
        "n_edges": int(graph.number_of_edges()),
        "density": float(nx.density(graph)) if graph.number_of_nodes() > 1 else 0.0,
        "largest_component": int(largest_component),
        "singleton_investor_pct": float(singleton_pct),
    }

    return NetworkBundle(
        startups=df,
        graph=graph,
        diagnostics=diagnostics,
        eligible_investor_counts={inv: investor_counts[inv] for inv in eligible},
    )
