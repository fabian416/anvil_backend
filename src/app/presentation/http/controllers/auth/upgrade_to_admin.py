"""
Upgrade to admin controller for the hexagonal architecture.
"""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.commands.auth.upgrade_to_admin import (
    UpgradeToAdminInteractor,
    UpgradeToAdminRequest,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.domain.exceptions.auth import (
    InvalidAuthorizationHeaderError,
    InsufficientPermissionsError,
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


def create_upgrade_to_admin_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/upgrade-to-admin",
        description=getdoc(UpgradeToAdminInteractor),
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
            UserNotFoundByEmailError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def upgrade_to_admin(
        credentials: Annotated[HTTPAuthorizationCredentials, Security(bearer_scheme)],
        interactor: FromDishka[UpgradeToAdminInteractor],
    ) -> UserResponse:
        # Extract "Bearer <token>" format from credentials
        authorization = f"{credentials.scheme} {credentials.credentials}"
        request_data = UpgradeToAdminRequest(authorization=authorization)
        updated_user = await interactor.execute(request_data)
        return UserResponse.from_domain(updated_user)

    return router
