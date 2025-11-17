from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, Request, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.infrastructure.auth.handlers.change_password import (
    ChangeOwnPasswordHandler,
    ChangeOwnPasswordRequest,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_change_own_password_router() -> APIRouter:
    router = ErrorAwareRouter(tags=["Account - Change Password"])

    @router.put(
        "/change-password",
        description="Change the authenticated user's password, invalidate all sessions, and issue new tokens.",
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ValueError: status.HTTP_400_BAD_REQUEST,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def change_password(
        request: Request,
        handler: FromDishka[ChangeOwnPasswordHandler],
        current_password: str = Body(..., embed=True),
        new_password: str = Body(..., embed=True),
        confirm_password: str = Body(..., embed=True),
    ) -> dict:
        data = ChangeOwnPasswordRequest(
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return await handler.execute(data)

    return router


