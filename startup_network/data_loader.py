"""Data loading utilities for combining startup CSV sources."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import CSV_2021, CSV_STARTUPS


def load_unified_startup_table(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Load and unify both project CSV datasets into one canonical table.

    Parameters
    ----------
    data_dir : str | Path | None
        Directory containing the required CSV files.

    Returns
    -------
    pd.DataFrame
        Canonical startup table with consistent columns.

    Raises
    ------
    FileNotFoundError
        If one or both required CSV files are missing.
    """
    resolved_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[1]
    startups_path = resolved_dir / CSV_STARTUPS
    unicorns_2021_path = resolved_dir / CSV_2021

    if not startups_path.exists() and (resolved_dir / "data" / CSV_STARTUPS).exists():
        startups_path = resolved_dir / "data" / CSV_STARTUPS
    if not unicorns_2021_path.exists() and (resolved_dir / "data" / CSV_2021).exists():
        unicorns_2021_path = resolved_dir / "data" / CSV_2021

    if not startups_path.exists():
        raise FileNotFoundError(f"Missing required CSV: {startups_path}")
    if not unicorns_2021_path.exists():
        raise FileNotFoundError(f"Missing required CSV: {unicorns_2021_path}")

    legacy = pd.read_csv(startups_path)
    legacy_unified = pd.DataFrame(
        {
            "startup_id": [f"legacy_{i}" for i in legacy.index],
            "company": legacy.get("Company", pd.Series(dtype=str)).fillna("").astype(str),
            "industry": legacy.get("Categories", pd.Series(dtype=str)).fillna("").astype(str),
            "country": legacy.get("Headquarters (Country)", pd.Series(dtype=str)).fillna("").astype(str),
            "city": legacy.get("Headquarters (City)", pd.Series(dtype=str)).fillna("").astype(str),
            "valuation": pd.Series([""] * len(legacy), dtype=str),
            "investors_raw": legacy.get("Investors", pd.Series(dtype=str)).fillna("").astype(str),
            "dataset": pd.Series([CSV_STARTUPS] * len(legacy), dtype=str),
        }
    )

    unicorns_2021 = pd.read_csv(unicorns_2021_path)
    unicorns_2021_unified = pd.DataFrame(
        {
            "startup_id": [f"u2021_{i}" for i in unicorns_2021.index],
            "company": unicorns_2021.get("Company", pd.Series(dtype=str)).fillna("").astype(str),
            "industry": unicorns_2021.get("Industry", pd.Series(dtype=str)).fillna("").astype(str),
            "country": unicorns_2021.get("Country", pd.Series(dtype=str)).fillna("").astype(str),
            "city": unicorns_2021.get("City", pd.Series(dtype=str)).fillna("").astype(str),
            "valuation": unicorns_2021.get("Valuation ($B)", pd.Series(dtype=str)).fillna("").astype(str),
            "investors_raw": unicorns_2021.get("Select Investors", pd.Series(dtype=str)).fillna("").astype(str),
            "dataset": pd.Series([CSV_2021] * len(unicorns_2021), dtype=str),
        }
    )

    combined = pd.concat([legacy_unified, unicorns_2021_unified], ignore_index=True)

    return combined[
        [
            "startup_id",
            "company",
            "industry",
            "country",
            "city",
            "valuation",
            "investors_raw",
            "dataset",
        ]
    ]
