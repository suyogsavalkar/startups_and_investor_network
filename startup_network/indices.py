"""Index builders for startup/investor lookup structures."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .models import Company, Investor
from .parsing import normalize_investor_name, prefer_display_name, split_investors


def build_investor_indices(
    startup_table: pd.DataFrame,
) -> tuple[dict[str, str], dict[str, set[str]], dict[str, set[str]]]:
    """Build lookup indices from the canonical startup table.

    Parameters
    ----------
    startup_table : pd.DataFrame
        Canonical startup table with `startup_id` and `investors_raw` columns.

    Returns
    -------
    tuple[dict[str, str], dict[str, set[str]], dict[str, set[str]]]
        Investor display map, startup-to-investors map, and investor-to-startups map.
    """
    investor_display_map: dict[str, str] = {}
    startup_to_investors: dict[str, set[str]] = {}
    investor_to_startups: dict[str, set[str]] = {}

    for row in startup_table.itertuples(index=False):
        startup_id = str(row.startup_id)
        raw_names = split_investors(str(row.investors_raw))

        normalized_set: set[str] = set()
        for raw_name in raw_names:
            normalized = normalize_investor_name(raw_name)
            if not normalized:
                continue
            normalized_set.add(normalized)
            current_display = investor_display_map.get(normalized, "")
            investor_display_map[normalized] = prefer_display_name(current_display, raw_name)

        startup_to_investors[startup_id] = normalized_set
        for investor_norm in normalized_set:
            investor_to_startups.setdefault(investor_norm, set()).add(startup_id)

    return investor_display_map, startup_to_investors, investor_to_startups


def build_domain_objects(
    startup_table: pd.DataFrame,
    startup_to_investors: dict[str, set[str]],
    investor_to_startups: dict[str, set[str]],
    investor_display_map: dict[str, str],
) -> tuple[dict[str, Company], dict[str, Investor]]:
    """Build Company and Investor domain objects from parsed indices.

    Parameters
    ----------
    startup_table : pd.DataFrame
        Canonical startup table.
    startup_to_investors : dict[str, set[str]]
        Startup to normalized-investor mapping.
    investor_to_startups : dict[str, set[str]]
        Investor to startup-id mapping.
    investor_display_map : dict[str, str]
        Normalized-investor to display-name mapping.

    Returns
    -------
    tuple[dict[str, Company], dict[str, Investor]]
        Company and investor lookup maps.
    """
    companies_by_id: dict[str, Company] = {}
    for row in startup_table.itertuples(index=False):
        startup_id = str(row.startup_id)
        investors_norm = sorted(startup_to_investors.get(startup_id, set()))
        investors_display = tuple(
            investor_display_map.get(investor_norm, investor_norm) for investor_norm in investors_norm
        )
        companies_by_id[startup_id] = Company(
            startup_id=startup_id,
            name=str(row.company),
            industry=str(row.industry),
            country=str(row.country),
            city=str(row.city),
            valuation=str(row.valuation),
            dataset=str(row.dataset),
            investors=investors_display,
        )

    investors_by_norm: dict[str, Investor] = {}
    for investor_norm, startup_ids in investor_to_startups.items():
        investors_by_norm[investor_norm] = Investor(
            normalized_name=investor_norm,
            name=investor_display_map.get(investor_norm, investor_norm),
            companies_backed=tuple(sorted(startup_ids)),
        )

    return companies_by_id, investors_by_norm


def investor_co_investors(
    investor_name: str,
    get_investor_fn: Any,
    investor_to_startups: dict[str, set[str]],
    investor_display_map: dict[str, str],
    companies_by_id: dict[str, Company],
    min_shared_companies: int = 1,
) -> list[dict[str, Any]]:
    """Return co-investor rows for an investor name.

    Parameters
    ----------
    investor_name : str
        Raw or normalized investor name.
    get_investor_fn : Any
        Callable that resolves an investor object from name.
    investor_to_startups : dict[str, set[str]]
        Investor to startup-id mapping.
    investor_display_map : dict[str, str]
        Normalized-investor to display-name mapping.
    companies_by_id : dict[str, Company]
        Startup-id to company object mapping.
    min_shared_companies : int
        Minimum shared startup count for inclusion.

    Returns
    -------
    list[dict[str, Any]]
        Sorted co-investor rows.
    """
    investor = get_investor_fn(investor_name)
    if investor is None:
        return []

    base_set = set(investor.companies_backed)
    rows: list[dict[str, Any]] = []
    threshold = max(int(min_shared_companies), 1)

    for other_norm, other_startups in investor_to_startups.items():
        if other_norm == investor.normalized_name:
            continue
        shared = base_set.intersection(other_startups)
        if len(shared) < threshold:
            continue
        rows.append(
            {
                "investor": investor_display_map.get(other_norm, other_norm),
                "shared_company_count": len(shared),
                "shared_companies": sorted(
                    companies_by_id[startup_id].name
                    for startup_id in shared
                    if startup_id in companies_by_id
                ),
            }
        )

    rows.sort(key=lambda item: (-item["shared_company_count"], item["investor"]))
    return rows
