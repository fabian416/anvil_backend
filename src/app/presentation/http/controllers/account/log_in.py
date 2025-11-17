from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.common.exceptions.authorization import AuthorizationError
from app.domain.exceptions.base import DomainFieldError
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.infrastructure.auth.exceptions import AlreadyAuthenticatedError, AuthenticationError
from app.infrastructure.auth.handlers.log_in import LogInHandler, LogInRequest
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    ServiceUnavailableTranslator,
)
from app.presentation.http.auth.constants import REQUEST_STATE_NEW_ACCESS_TOKEN_KEY


def create_log_in_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/login",
        description=getdoc(LogInHandler),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AlreadyAuthenticatedError: status.HTTP_403_FORBIDDEN,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            DomainFieldError: status.HTTP_400_BAD_REQUEST,
            UserNotFoundByEmailError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def login(
        request_data: LogInRequest,
        handler: FromDishka[LogInHandler],
        request: Request,
    ) -> dict:
        enriched_request = LogInRequest(
            email=request_data.email,
            password=request_data.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return await handler.execute(enriched_request)

    return router
