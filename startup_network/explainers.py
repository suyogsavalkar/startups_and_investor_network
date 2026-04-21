"""Deterministic path explanation helpers."""

from __future__ import annotations

import pandas as pd


def deterministic_path_explanation(
    path_companies: list[str],
    edge_df: pd.DataFrame,
    weighted: bool,
) -> str:
    """Generate a deterministic text explanation for a startup path.

    Parameters
    ----------
    path_companies : list[str]
        Company names in path order.
    edge_df : pd.DataFrame
        Edge details for each path hop.
    weighted : bool
        Whether weighted shortest path was used.

    Returns
    -------
    str
        Human-readable explanation text.
    """
    if len(path_companies) < 2 or edge_df.empty:
        return "No explanation available because the path has fewer than two companies."

    lines: list[str] = []
    lines.append(
        f"This route links {path_companies[0]} to {path_companies[-1]} in {len(path_companies) - 1} hop(s)."
    )
    if weighted:
        lines.append(
            "It uses weighted shortest path, which favors links with more shared investors."
        )
    else:
        lines.append("It uses unweighted shortest path, which favors fewer hops.")

    strongest_pair = ("", "", 0)
    for idx, row in enumerate(edge_df.itertuples(index=False), start=1):
        from_company = str(getattr(row, "from_company", ""))
        to_company = str(getattr(row, "to_company", ""))
        shared_count = int(getattr(row, "shared_investor_count", 0))
        shared_raw = str(getattr(row, "shared_investors", ""))
        shared_list = [piece.strip() for piece in shared_raw.split(",") if piece.strip()]
        sample = ", ".join(shared_list[:3]) if shared_list else "none listed"

        if shared_count > strongest_pair[2]:
            strongest_pair = (from_company, to_company, shared_count)

        lines.append(
            f"Step {idx}: {from_company} -> {to_company} share {shared_count} investor(s) "
            f"(examples: {sample})."
        )

    if strongest_pair[2] > 0:
        lines.append(
            "Strongest connection on this route is "
            f"{strongest_pair[0]} -> {strongest_pair[1]} with {strongest_pair[2]} shared investors."
        )

    return " ".join(lines)
