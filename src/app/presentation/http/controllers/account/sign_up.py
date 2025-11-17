from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.common.exceptions.authorization import AuthorizationError
from app.domain.exceptions.base import DomainFieldError
from app.domain.exceptions.user import (
    RoleAssignmentNotPermittedError,
    EmailAlreadyExistsError,
)
from app.infrastructure.auth.exceptions import AlreadyAuthenticatedError, AuthenticationError
from app.infrastructure.auth.handlers.sign_up import (
    SignUpHandler,
    SignUpRequest,
    SignUpResponse,
)
from app.domain.exceptions.location import CountryNotFoundError, CityNotFoundInCountryError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import (
    log_error,
    log_info,
)
from app.presentation.http.errors.translators import (
    ServiceUnavailableTranslator,
)


def create_sign_up_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/signup",
        description=getdoc(SignUpHandler),
        error_map={
            AlreadyAuthenticatedError: status.HTTP_403_FORBIDDEN,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            CountryNotFoundError: status.HTTP_400_BAD_REQUEST,
            CityNotFoundInCountryError: status.HTTP_400_BAD_REQUEST,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            DomainFieldError: status.HTTP_400_BAD_REQUEST,
            RoleAssignmentNotPermittedError: status.HTTP_422_UNPROCESSABLE_ENTITY,
            EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
            AuthenticationError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def sign_up(
        request_data: SignUpRequest,
        handler: FromDishka[SignUpHandler],
        request: Request,
    ) -> SignUpResponse:
        enriched_request = SignUpRequest(
            email=request_data.email,
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            password=request_data.password,
            country_id=getattr(request_data, "country_id", None),
            city_id=getattr(request_data, "city_id", None),
            language=getattr(request_data, "language", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return await handler.execute(enriched_request)

    return router
