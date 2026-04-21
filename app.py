"""Core, UI-free helpers for the startup investor network project.

This module intentionally contains no Streamlit (or any other UI) code.
It exposes convenience functions for loading filtered data, building the
network bundle, and generating path reports using the core logic modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from startup_network import (
    NetworkBundle,
    build_network,
    connected_companies,
    load_startup_data,
    parse_investor_cell,
    path_edges,
    rank_startups,
    shortest_path,
)
from startup_network.explainers import deterministic_path_explanation


BASE_DIR = Path(__file__).resolve().parent


def startup_label_map(df: pd.DataFrame) -> dict[str, str]:
    """Return startup_id -> display label mapping."""
    labels: dict[str, str] = {}
    for _, row in df.sort_values(["company", "dataset"]).iterrows():
        sid = row["startup_id"]
        labels[sid] = f'{row["company"]} ({row["dataset"]})'
    return labels


def get_raw_data(base_dir: str | Path | None = None) -> pd.DataFrame:
    """Load the unified startup dataframe from disk."""
    resolved = Path(base_dir) if base_dir else BASE_DIR
    return load_startup_data(resolved)


def get_bundle(
    min_investor_frequency: int = 2,
    max_investor_prevalence: float = 0.10,
    min_edge_weight: int = 1,
    industry_filter: tuple[str, ...] = (),
    country_filter: tuple[str, ...] = (),
    base_dir: str | Path | None = None,
) -> NetworkBundle:
    """Build a filtered NetworkBundle (graph + diagnostics + startup subset)."""
    df = get_raw_data(base_dir=base_dir)
    if industry_filter:
        df = df[df["industry"].isin(industry_filter)]
    if country_filter:
        df = df[df["country"].isin(country_filter)]

    return build_network(
        startups_df=df,
        min_investor_frequency=min_investor_frequency,
        max_investor_prevalence=max_investor_prevalence,
        min_edge_weight=min_edge_weight,
    )


def startup_details(bundle: NetworkBundle, startup_id: str) -> dict[str, Any] | None:
    """Return core details for a startup within the bundle."""
    graph = bundle.graph
    if startup_id not in graph:
        return None

    node = graph.nodes[startup_id]
    row_df = bundle.startups[bundle.startups["startup_id"] == startup_id]
    investors_all: list[str] = []
    if not row_df.empty:
        investors_all = parse_investor_cell(row_df.iloc[0]["investors_raw"])

    return {
        "startup_id": startup_id,
        "company": node.get("company", ""),
        "industry": node.get("industry", ""),
        "country": node.get("country", ""),
        "city": node.get("city", ""),
        "valuation": node.get("valuation", ""),
        "dataset": node.get("dataset", ""),
        "investors_all": investors_all,
        "investors_eligible": node.get("investors_eligible", []),
    }


def connected_startups(bundle: NetworkBundle, startup_id: str, top_n: int = 25) -> pd.DataFrame:
    """Return connected startups sorted by connection strength."""
    return connected_companies(bundle, startup_id, top_n=top_n)


def ranking_table(bundle: NetworkBundle, metric: str = "weighted_degree", top_n: int = 25) -> pd.DataFrame:
    """Return startup ranking table for the requested metric."""
    return rank_startups(bundle, metric=metric, top_n=top_n)


def path_report(
    bundle: NetworkBundle,
    source_id: str,
    target_id: str,
    weighted: bool = False,
) -> dict[str, Any]:
    """Return structured path info and deterministic explanation."""
    graph = bundle.graph
    path = shortest_path(bundle, source_id, target_id, weighted=weighted)
    if not path:
        return {
            "path_startup_ids": [],
            "path_companies": [],
            "edges": pd.DataFrame(columns=["from_company", "to_company", "shared_investor_count", "shared_investors"]),
            "explanation": "No path found under current filters and thresholds.",
        }

    names = [graph.nodes[node_id].get("company", "") for node_id in path]
    edge_df = path_edges(bundle, path)
    explanation = deterministic_path_explanation(names, edge_df, weighted=weighted)

    return {
        "path_startup_ids": path,
        "path_companies": names,
        "edges": edge_df,
        "explanation": explanation,
    }
