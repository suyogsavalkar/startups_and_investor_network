"""Shared test fixtures for the startup investor network tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def synthetic_startups() -> pd.DataFrame:
    """Small graph where the shared investors and edge weights are easy to check."""
    return pd.DataFrame(
        [
            {
                "startup_id": "s1",
                "company": "Alpha",
                "industry": "Fintech",
                "country": "US",
                "city": "NYC",
                "valuation": "",
                "investors_raw": "A, B",
                "dataset": "synthetic.csv",
            },
            {
                "startup_id": "s2",
                "company": "Beta",
                "industry": "Health",
                "country": "US",
                "city": "SF",
                "valuation": "",
                "investors_raw": "B, C",
                "dataset": "synthetic.csv",
            },
            {
                "startup_id": "s3",
                "company": "Gamma",
                "industry": "AI",
                "country": "US",
                "city": "Boston",
                "valuation": "",
                "investors_raw": "A, B",
                "dataset": "synthetic.csv",
            },
        ]
    )


def disconnected_startups() -> pd.DataFrame:
    """Tiny graph where two companies have no shared investors at all."""
    return pd.DataFrame(
        [
            {
                "startup_id": "x1",
                "company": "Node One",
                "industry": "AI",
                "country": "US",
                "city": "NYC",
                "valuation": "",
                "investors_raw": "Investor A",
                "dataset": "synthetic.csv",
            },
            {
                "startup_id": "x2",
                "company": "Node Two",
                "industry": "AI",
                "country": "US",
                "city": "SF",
                "valuation": "",
                "investors_raw": "Investor B",
                "dataset": "synthetic.csv",
            },
        ]
    )


def weighted_path_startups() -> pd.DataFrame:
    """Graph where weighted path-finding should prefer one strong edge over two weak hops."""
    return pd.DataFrame(
        [
            {
                "startup_id": "a",
                "company": "Alpha",
                "industry": "Fintech",
                "country": "US",
                "city": "NYC",
                "valuation": "",
                "investors_raw": "Direct Weak, Strong One, Strong Two, Strong Three",
                "dataset": "synthetic.csv",
            },
            {
                "startup_id": "b",
                "company": "Beta",
                "industry": "Health",
                "country": "US",
                "city": "SF",
                "valuation": "",
                "investors_raw": "Direct Weak, Bridge One, Bridge Two, Bridge Three",
                "dataset": "synthetic.csv",
            },
            {
                "startup_id": "c",
                "company": "Gamma",
                "industry": "AI",
                "country": "US",
                "city": "Boston",
                "valuation": "",
                "investors_raw": (
                    "Strong One, Strong Two, Strong Three, "
                    "Bridge One, Bridge Two, Bridge Three"
                ),
                "dataset": "synthetic.csv",
            },
        ]
    )
