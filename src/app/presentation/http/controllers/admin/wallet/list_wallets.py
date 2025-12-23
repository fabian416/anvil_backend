"""
List Wallets Controller.

Admin endpoint to list all wallets with pagination, sorting, and search.
"""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.exceptions.query import PaginationError, SortingError
from app.application.common.query_params.sorting import SortingOrder
from app.application.queries.list_wallets import (
    ListWalletsQueryService,
    ListWalletsRequest,
    ListWalletsResponse,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError, ReaderError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class ListWalletsRequestPydantic(BaseModel):
    """
    Request model for listing wallets.

    Rendered in Swagger UI (OpenAPI) schema.
    """

    model_config = ConfigDict(frozen=True)

    limit: Annotated[int, Field(ge=1, le=100, description="Max wallets per page")] = 20
    offset: Annotated[int, Field(ge=0, description="Number of wallets to skip")] = 0
    sorting_field: Annotated[
        str,
        Field(description="Field to sort by: id, address, provider, created_at"),
    ] = "created_at"
    sorting_order: Annotated[SortingOrder, Field(description="Sort direction")] = (
        SortingOrder.DESC
    )
    search: Annotated[
        str | None,
        Field(
            description="Search term (matches address, email, user name, or wallet ID)"
        ),
    ] = None


def create_list_wallets_router() -> APIRouter:
    """Create the list wallets router."""
    router = ErrorAwareRouter()

    @router.get(
        "/",
        description=getdoc(ListWalletsQueryService),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            PaginationError: status.HTTP_400_BAD_REQUEST,
            SortingError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def list_wallets(
        request_data_pydantic: Annotated[ListWalletsRequestPydantic, Depends()],
        interactor: FromDishka[ListWalletsQueryService],
    ) -> ListWalletsResponse:
        """
        List all wallets with pagination and search.

        Admin-only endpoint that returns:
        - Wallet details (address, provider, chain, status)
        - Owner information (user_id, email, name)
        - Total count for pagination

        Search supports: address, email, user name, privy_wallet_id.
        """
        request_data = ListWalletsRequest(
            limit=request_data_pydantic.limit,
            offset=request_data_pydantic.offset,
            sorting_field=request_data_pydantic.sorting_field,
            sorting_order=request_data_pydantic.sorting_order,
            search=request_data_pydantic.search,
        )
        return await interactor.execute(request_data)

    return router
