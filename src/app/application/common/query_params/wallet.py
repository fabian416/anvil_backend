"""
Wallet Query Parameters.

Defines parameters for wallet listing queries with pagination, sorting, and search.
"""

from dataclasses import dataclass

from app.application.common.query_params.pagination import Pagination
from app.application.common.query_params.sorting import SortingOrder


@dataclass(frozen=True, slots=True, kw_only=True)
class WalletListSorting:
    """Sorting parameters for wallet list."""

    sorting_field: str
    sorting_order: SortingOrder


@dataclass(frozen=True, slots=True, kw_only=True)
class WalletListParams:
    """
    Parameters for wallet listing query.

    Includes pagination, sorting, and optional search term.
    Search can match against address, user email, or user name.
    """

    pagination: Pagination
    sorting: WalletListSorting
    search: str | None = None
