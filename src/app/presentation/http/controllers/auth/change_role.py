"""
Change role controller for the hexagonal architecture.
"""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel

from app.application.commands.auth.change_role import (
    ChangeRoleInteractor,
    ChangeRoleRequest,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.domain.exceptions.auth import (
    InvalidAuthorizationHeaderError,
    InsufficientPermissionsError,
    RoleChangeNotAllowedError,
)
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    ServiceUnavailableTranslator,
)
from app.presentation.http.schemas.user import UserResponse


class ChangeRoleRequestBody(BaseModel):
    """Request body for changing a user's role."""
    email: str
    new_role: str


def create_change_role_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/change-role",
        description=getdoc(ChangeRoleInteractor),
        response_model=UserResponse,
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            InvalidAuthorizationHeaderError: status.HTTP_401_UNAUTHORIZED,
            InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
            RoleChangeNotAllowedError: status.HTTP_400_BAD_REQUEST,
            UserNotFoundByEmailError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def change_role(
        request_body: ChangeRoleRequestBody,
        authorization: Annotated[str, Security(bearer_scheme)],
        interactor: FromDishka[ChangeRoleInteractor],
    ) -> UserResponse:
        request_data = ChangeRoleRequest(
            authorization=authorization,
            target_email=request_body.email,
            new_role=request_body.new_role,
        )
        updated_user = await interactor.execute(request_data)
        return UserResponse.from_domain(updated_user)

    return router
