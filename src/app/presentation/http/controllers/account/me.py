from inspect import getdoc
from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Header, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.infrastructure.auth.handlers.account_me import (
    GetMeHandler,
    MeResponse,
    UpdateMeHandler,
    UpdateMeRequest,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_me_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/me",
        description="Get current authenticated user's profile",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_me(handler: FromDishka[GetMeHandler]) -> MeResponse:
        return await handler.execute()

    @router.put(
        "/me",
        description="Update current authenticated user's profile",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_me(
        req: UpdateMeRequest,
        handler: FromDishka[UpdateMeHandler],
    ) -> MeResponse:
        return await handler.execute(req)

    return router


