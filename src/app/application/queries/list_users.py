import logging
from dataclasses import dataclass
from typing import TypedDict

from app.application.common.exceptions.query import SortingError
from app.application.common.ports.user_query_gateway import UserQueryGateway
from app.application.common.query_models.user import UserQueryModel
from app.application.common.query_params.pagination import Pagination
from app.application.common.query_params.sorting import SortingOrder
from app.application.common.query_params.user import (
    UserListParams,
    UserListSorting,
)
from app.application.common.services.authorization.authorize import (
    authorize,
)
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.user_role import UserRole

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListUsersRequest:
    limit: int
    offset: int
    sorting_field: str
    sorting_order: SortingOrder
    search: str | None = None


class ListUsersResponse(TypedDict):
    items: list[UserQueryModel]
    total: int
    limit: int
    offset: int


class ListUsersQueryService:
    """
    - Open to admins.
    - Retrieves a paginated list of existing users with relevant information.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_query_gateway: UserQueryGateway,
    ):
        self._current_user_service = current_user_service
        self._user_query_gateway = user_query_gateway

    async def execute(self, request_data: ListUsersRequest) -> ListUsersResponse:
        """
        :raises AuthenticationError:
        :raises DataMapperError:
        :raises AuthorizationError:
        :raises ReaderError:
        :raises PaginationError:
        :raises SortingError:
        """
        log.info("List users: started.")

        current_user = await self._current_user_service.get_current_user()

        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.USER,
            ),
        )

        log.debug("Retrieving list of users.")
        user_list_params = UserListParams(
            pagination=Pagination(
                limit=request_data.limit,
                offset=request_data.offset,
            ),
            sorting=UserListSorting(
                sorting_field=request_data.sorting_field,
                sorting_order=request_data.sorting_order,
            ),
            search=request_data.search,
        )

        users: list[UserQueryModel] | None = await self._user_query_gateway.read_all(
            user_list_params,
        )
        if users is None:
            log.error(
                "Retrieving list of users failed: invalid sorting column '%s'.",
                request_data.sorting_field,
            )
            raise SortingError("Invalid sorting field.")

        total = await self._user_query_gateway.count_all(search=request_data.search)

        response = ListUsersResponse(
            items=users,
            total=total,
            limit=request_data.limit,
            offset=request_data.offset,
        )

        log.info("List users: done.")
        return response
