"""Domain models for startups and investors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from .constants import (
    DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    DEFAULT_MIN_INVESTOR_FREQUENCY,
)

if TYPE_CHECKING:
    from .service import InvestorNetwork


@dataclass(frozen=True)
class Company:
    """A startup entity enriched with metadata and investors.

    Parameters
    ----------
    startup_id : str
        Unique identifier for the startup row.
    name : str
        Company name.
    industry : str
        Startup industry/category.
    country : str
        Country value from source data.
    city : str
        City value from source data.
    valuation : str
        Valuation field (string from CSV).
    dataset : str
        Source dataset file name.
    investors : tuple[str, ...]
        Investor display names associated with the startup.
    """

    startup_id: str
    name: str
    industry: str
    country: str
    city: str
    valuation: str
    dataset: str
    investors: tuple[str, ...]

    def connected_companies(
        self,
        network: "InvestorNetwork",
        min_investor_frequency: int = DEFAULT_MIN_INVESTOR_FREQUENCY,
        max_investor_prevalence_fraction: float = DEFAULT_MAX_INVESTOR_PREVALENCE_FRACTION,
    ) -> list[dict[str, Any]]:
        """Return startups connected to this company by shared investors.

        Parameters
        ----------
        network : InvestorNetwork
            Active network service instance.
        min_investor_frequency : int
            Minimum investor frequency for eligibility.
        max_investor_prevalence_fraction : float
            Maximum investor prevalence for eligibility.

        Returns
        -------
        list[dict[str, Any]]
            Connected startup rows with shared-investor details.
        """
        return network.connected_companies(
            startup_id=self.startup_id,
            min_investor_frequency=min_investor_frequency,
            max_investor_prevalence_fraction=max_investor_prevalence_fraction,
        )


@dataclass(frozen=True)
class Investor:
    """An investor entity with the startups it backed.

    Parameters
    ----------
    normalized_name : str
        Normalized investor key.
    name : str
        Preferred investor display name.
    companies_backed : tuple[str, ...]
        Startup IDs funded by this investor.
    """

    normalized_name: str
    name: str
    companies_backed: tuple[str, ...]

    def company_objects(self, network: "InvestorNetwork") -> list[Company]:
        """Return full company objects for startups this investor backed.

        Parameters
        ----------
        network : InvestorNetwork
            Active network service instance.

        Returns
        -------
        list[Company]
            Company objects available in the current network.
        """
        companies: list[Company] = []
        for startup_id in self.companies_backed:
            company = network.get_company(startup_id)
            if company is not None:
                companies.append(company)
        return companies

    def co_investors(
        self,
        network: "InvestorNetwork",
        min_shared_companies: int = 1,
    ) -> list[dict[str, Any]]:
        """Return co-investors that share startups with this investor.

        Parameters
        ----------
        network : InvestorNetwork
            Active network service instance.
        min_shared_companies : int
            Minimum shared startup count for inclusion.

        Returns
        -------
        list[dict[str, Any]]
            Co-investor rows with shared-company metadata.
        """
        return network.investor_co_investors(self.name, min_shared_companies=min_shared_companies)
