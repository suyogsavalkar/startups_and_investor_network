"""Parsing and normalization helpers for investor and CSV values."""

from __future__ import annotations

from typing import Any
import re

import pandas as pd


def normalize_investor_name(name: str) -> str:
    """Normalize investor names for cross-row matching.

    Parameters
    ----------
    name : str
        Raw investor display name.

    Returns
    -------
    str
        Lowercased and whitespace-collapsed investor key.
    """
    collapsed = re.sub(r"\s+", " ", name.strip())
    return collapsed.lower()


def split_investors(investors_raw: str) -> list[str]:
    """Split a comma-separated investor string into cleaned names.

    Parameters
    ----------
    investors_raw : str
        Raw CSV value containing investor names.

    Returns
    -------
    list[str]
        Investor names in their display form.
    """
    if not isinstance(investors_raw, str) or not investors_raw.strip():
        return []
    return [piece.strip() for piece in investors_raw.split(",") if piece.strip()]


def parse_investor_cell(raw_value: Any) -> list[str]:
    """Parse an investor cell value into a list.

    Parameters
    ----------
    raw_value : Any
        CSV cell value, potentially null or NaN.

    Returns
    -------
    list[str]
        Cleaned investor display names.
    """
    if raw_value is None:
        return []
    if isinstance(raw_value, float) and pd.isna(raw_value):
        return []
    return [piece.strip() for piece in str(raw_value).split(",") if piece.strip()]


def title_like_score(name: str) -> tuple[int, int, int]:
    """Score a display string when selecting a canonical investor label.

    Parameters
    ----------
    name : str
        Candidate display name.

    Returns
    -------
    tuple[int, int, int]
        Tuple that favors title case, then case richness, then length.
    """
    stripped = name.strip()
    if not stripped:
        return (0, 0, 0)

    has_upper = int(any(ch.isupper() for ch in stripped))
    title_like = int(stripped == stripped.title())
    not_all_lower = int(not stripped.islower())
    return (title_like, has_upper + not_all_lower, len(stripped))


def prefer_display_name(existing: str, candidate: str) -> str:
    """Choose a stable investor display name for one normalized key.

    Parameters
    ----------
    existing : str
        Current chosen display value.
    candidate : str
        New display candidate.

    Returns
    -------
    str
        Preferred display label.
    """
    if not existing:
        return candidate
    if not candidate:
        return existing
    return candidate if title_like_score(candidate) > title_like_score(existing) else existing
