from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.infrastructure.auth.handlers.password_reset import (
    ForgotPasswordHandler,
    ForgotPasswordRequest,
    ResetPasswordHandler,
    ResetPasswordRequest,
)
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_password_reset_router() -> APIRouter:
    router = ErrorAwareRouter(tags=["Account - Password Reset"])

    @router.post(
        "/forgot-password",
        description="Request a password reset token to be emailed to the user.",
        error_map={
            UserNotFoundByEmailError: status.HTTP_404_NOT_FOUND,
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
    async def forgot_password(
        handler: FromDishka[ForgotPasswordHandler],
        email: str = Body(..., embed=True),
    ) -> dict:
        await handler.execute(ForgotPasswordRequest(email=email))
        return {"status": "success", "message": "Password reset email sent"}

    @router.post(
        "/reset-password",
        description="Reset password using a valid token.",
        error_map={
            AttributeError: status.HTTP_400_BAD_REQUEST,
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
    async def reset_password(
        handler: FromDishka[ResetPasswordHandler],
        token: str = Body(..., embed=True),
        new_password: str = Body(..., embed=True),
    ) -> dict:
        await handler.execute(ResetPasswordRequest(token=token, new_password=new_password))
        return {"status": "success", "message": "Password has been reset"}

    return router


