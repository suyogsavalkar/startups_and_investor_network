"""Query and analytics helpers for startup network graphs."""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd

from .types import NetworkBundle


def connected_companies_for_graph(
    graph: nx.Graph,
    startup_id: str,
    investor_display_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Return neighboring startups with shared-investor details.

    Parameters
    ----------
    graph : nx.Graph
        Startup graph.
    startup_id : str
        Startup id to inspect.
    investor_display_map : dict[str, str]
        Mapping from normalized investor key to display label.

    Returns
    -------
    list[dict[str, Any]]
        Neighbor rows sorted by weight and company name.
    """
    if startup_id not in graph:
        return []

    neighbors: list[dict[str, Any]] = []
    for neighbor_id in graph.neighbors(startup_id):
        edge_data = graph[startup_id][neighbor_id]
        shared_norm = edge_data.get("shared_investors", [])
        neighbors.append(
            {
                "startup_id": neighbor_id,
                "company": graph.nodes[neighbor_id].get("company", ""),
                "shared_investor_count": int(edge_data.get("weight", 0)),
                "shared_investors": [investor_display_map.get(inv_norm, inv_norm) for inv_norm in shared_norm],
            }
        )

    neighbors.sort(key=lambda item: (-item["shared_investor_count"], item["company"]))
    return neighbors


def shortest_path_records(
    graph: nx.Graph,
    source_startup_id: str,
    target_startup_id: str,
    weighted: bool = False,
) -> list[dict[str, str]]:
    """Return shortest startup path as startup_id/company records.

    Parameters
    ----------
    graph : nx.Graph
        Startup graph.
    source_startup_id : str
        Source startup id.
    target_startup_id : str
        Target startup id.
    weighted : bool
        If True, use inverse edge weight as path distance.

    Returns
    -------
    list[dict[str, str]]
        Path rows in traversal order, or an empty list when no path exists.
    """
    if source_startup_id not in graph or target_startup_id not in graph:
        return []

    try:
        node_path = nx.shortest_path(
            graph,
            source=source_startup_id,
            target=target_startup_id,
            weight="distance" if weighted else None,
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

    return [{"startup_id": node_id, "company": graph.nodes[node_id].get("company", "")} for node_id in node_path]


def centrality_ranking(
    graph: nx.Graph,
    top_n: int = 25,
    sort_by: str = "weighted_degree",
) -> pd.DataFrame:
    """Compute startup centrality metrics and return a ranking table.

    Parameters
    ----------
    graph : nx.Graph
        Startup graph.
    top_n : int
        Number of rows to return.
    sort_by : str
        Sort metric: `degree`, `weighted_degree`, or `betweenness`.

    Returns
    -------
    pd.DataFrame
        Startup ranking dataframe.
    """
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["startup_id", "company", "degree", "weighted_degree", "betweenness"])

    degree = dict(graph.degree())
    weighted_degree = dict(graph.degree(weight="weight"))
    betweenness = nx.betweenness_centrality(graph, weight="distance", normalized=True)

    ranking = pd.DataFrame(
        {
            "startup_id": list(graph.nodes()),
            "company": [graph.nodes[node].get("company", "") for node in graph.nodes()],
            "degree": [float(degree[node]) for node in graph.nodes()],
            "weighted_degree": [float(weighted_degree[node]) for node in graph.nodes()],
            "betweenness": [float(betweenness[node]) for node in graph.nodes()],
        }
    )

    if sort_by not in {"degree", "weighted_degree", "betweenness"}:
        sort_by = "weighted_degree"

    ranking = ranking.sort_values(by=[sort_by, "company"], ascending=[False, True]).reset_index(drop=True)
    return ranking.head(max(top_n, 1))


def diagnostics_summary(
    startup_count: int,
    graph: nx.Graph,
    investor_to_startups: dict[str, set[str]],
    eligible_investors_set: set[str],
) -> dict[str, float | int]:
    """Return summary diagnostics for graph quality and scale.

    Parameters
    ----------
    startup_count : int
        Total startups represented in the source startup table.
    graph : nx.Graph
        Startup graph.
    investor_to_startups : dict[str, set[str]]
        Investor-to-startups index.
    eligible_investors_set : set[str]
        Investors that passed current filtering criteria.

    Returns
    -------
    dict[str, float | int]
        Diagnostics dictionary used by reporting layers.
    """
    investor_frequencies = [len(startups) for startups in investor_to_startups.values()]
    singleton_investor_count = sum(1 for freq in investor_frequencies if freq == 1)
    n_investors_total = len(investor_to_startups)
    singleton_investor_pct = (
        (singleton_investor_count / n_investors_total) * 100 if n_investors_total else 0.0
    )

    if graph.number_of_nodes() > 0:
        largest_component = max((len(component) for component in nx.connected_components(graph)), default=0)
    else:
        largest_component = 0

    return {
        "n_startups": int(startup_count),
        "n_investors_total": int(n_investors_total),
        "n_investors_eligible": int(len(eligible_investors_set)),
        "n_edges": int(graph.number_of_edges()),
        "density": float(nx.density(graph)) if graph.number_of_nodes() > 1 else 0.0,
        "largest_component": int(largest_component),
        "singleton_investor_pct": float(singleton_investor_pct),
    }


def connected_companies(bundle: NetworkBundle, startup_id: str, top_n: int = 25) -> pd.DataFrame:
    """Return connected companies for a startup from a `NetworkBundle`.

    Parameters
    ----------
    bundle : NetworkBundle
        Function-style graph bundle.
    startup_id : str
        Startup id to inspect.
    top_n : int
        Maximum number of neighbors to return.

    Returns
    -------
    pd.DataFrame
        Neighbor rows sorted by descending weight.
    """
    graph = bundle.graph
    if startup_id not in graph:
        return pd.DataFrame(columns=["company", "shared_investors", "weight"])

    rows: list[dict[str, Any]] = []
    for neighbor in graph.neighbors(startup_id):
        edge_data = graph[startup_id][neighbor]
        rows.append(
            {
                "startup_id": neighbor,
                "company": graph.nodes[neighbor].get("company", ""),
                "shared_investors": ", ".join(edge_data.get("shared_investors", [])),
                "weight": int(edge_data.get("weight", 0)),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["weight", "company"], ascending=[False, True]).head(top_n)


def shortest_path(bundle: NetworkBundle, source_id: str, target_id: str, weighted: bool = False) -> list[str]:
    """Return startup-id path between source and target in a `NetworkBundle`.

    Parameters
    ----------
    bundle : NetworkBundle
        Function-style graph bundle.
    source_id : str
        Source startup id.
    target_id : str
        Target startup id.
    weighted : bool
        If True, use inverse edge weight as path distance.

    Returns
    -------
    list[str]
        Startup id path, or an empty list when no path exists.
    """
    graph = bundle.graph
    if source_id not in graph or target_id not in graph:
        return []
    try:
        return nx.shortest_path(
            graph,
            source=source_id,
            target=target_id,
            weight="distance" if weighted else None,
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def path_edges(bundle: NetworkBundle, path: list[str]) -> pd.DataFrame:
    """Return edge-level details for each hop in a startup path.

    Parameters
    ----------
    bundle : NetworkBundle
        Function-style graph bundle.
    path : list[str]
        Startup-id path.

    Returns
    -------
    pd.DataFrame
        One row per hop with shared-investor metadata.
    """
    rows: list[dict[str, Any]] = []
    graph = bundle.graph
    for i in range(len(path) - 1):
        source = path[i]
        target = path[i + 1]
        edge_data = graph[source][target]
        rows.append(
            {
                "from_company": graph.nodes[source].get("company", ""),
                "to_company": graph.nodes[target].get("company", ""),
                "shared_investor_count": int(edge_data.get("weight", 0)),
                "shared_investors": ", ".join(edge_data.get("shared_investors", [])),
            }
        )
    return pd.DataFrame(rows)


def rank_startups(bundle: NetworkBundle, metric: str = "weighted_degree", top_n: int = 25) -> pd.DataFrame:
    """Return ranked startup rows for the selected metric.

    Parameters
    ----------
    bundle : NetworkBundle
        Function-style graph bundle.
    metric : str
        Ranking metric: `weighted_degree`, `degree`, or `betweenness`.
    top_n : int
        Number of rows to return. Values < 1 are coerced to 1.

    Returns
    -------
    pd.DataFrame
        Ranking rows with score and metadata columns.
    """
    graph = bundle.graph
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["company", "score", "metric"])

    if metric == "degree":
        scores = dict(graph.degree())
    elif metric == "betweenness":
        scores = nx.betweenness_centrality(graph, weight="distance", normalized=True)
    else:
        scores = dict(graph.degree(weight="weight"))
        metric = "weighted_degree"

    rows = [
        {
            "startup_id": node,
            "company": graph.nodes[node].get("company", ""),
            "industry": graph.nodes[node].get("industry", ""),
            "country": graph.nodes[node].get("country", ""),
            "score": float(score),
            "metric": metric,
        }
        for node, score in scores.items()
    ]
    return (
        pd.DataFrame(rows)
        .sort_values(["score", "company"], ascending=[False, True])
        .head(max(int(top_n), 1))
        .reset_index(drop=True)
    )
