"""
List Wallets Query Service.

Admin endpoint to list all wallets with pagination, sorting, and search.
"""

import logging
from dataclasses import dataclass
from typing import TypedDict

from app.application.common.exceptions.query import SortingError
from app.application.common.ports.wallet_query_gateway import WalletQueryGateway
from app.application.common.query_models.wallet import WalletQueryModel
from app.application.common.query_params.pagination import Pagination
from app.application.common.query_params.sorting import SortingOrder
from app.application.common.query_params.wallet import (
    WalletListParams,
    WalletListSorting,
)
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.user_role import UserRole

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListWalletsRequest:
    """Request parameters for listing wallets."""

    limit: int
    offset: int
    sorting_field: str
    sorting_order: SortingOrder
    search: str | None = None


class ListWalletsResponse(TypedDict):
    """Response for wallet listing."""

    wallets: list[WalletQueryModel]
    total: int


class ListWalletsQueryService:
    """
    Admin-only query service to list all wallets.

    Features:
    - Pagination (limit/offset)
    - Sorting by any valid column
    - Search by address, user email, or user name
    - Returns wallet details with owner information
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_query_gateway: WalletQueryGateway,
    ):
        self._current_user_service = current_user_service
        self._wallet_query_gateway = wallet_query_gateway

    async def execute(self, request_data: ListWalletsRequest) -> ListWalletsResponse:
        """
        Execute the list wallets query.

        :raises AuthenticationError: If user is not authenticated.
        :raises AuthorizationError: If user is not an admin.
        :raises ReaderError: If database query fails.
        :raises PaginationError: If pagination parameters are invalid.
        :raises SortingError: If sorting field is invalid.
        """
        log.info("List wallets: started.")

        current_user = await self._current_user_service.get_current_user()

        # Only admins can list all wallets
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.USER,
            ),
        )

        log.debug(
            "Retrieving list of wallets. limit=%d, offset=%d, search=%s",
            request_data.limit,
            request_data.offset,
            request_data.search,
        )

        wallet_list_params = WalletListParams(
            pagination=Pagination(
                limit=request_data.limit,
                offset=request_data.offset,
            ),
            sorting=WalletListSorting(
                sorting_field=request_data.sorting_field,
                sorting_order=request_data.sorting_order,
            ),
            search=request_data.search,
        )

        wallets = await self._wallet_query_gateway.read_all(wallet_list_params)
        if wallets is None:
            log.error(
                "Retrieving list of wallets failed: invalid sorting column '%s'.",
                request_data.sorting_field,
            )
            raise SortingError("Invalid sorting field.")

        # Get total count for pagination info
        total = await self._wallet_query_gateway.count_all(search=request_data.search)

        response = ListWalletsResponse(wallets=wallets, total=total)

        log.info("List wallets: done. count=%d, total=%d", len(wallets), total)
        return response
