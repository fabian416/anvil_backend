from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.handlers.verify_email import VerifyEmailHandler, VerifyEmailRequest
from app.infrastructure.auth.handlers.send_email_verification import (
    SendEmailVerificationHandler,
    SendEmailVerificationRequest,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme


def create_email_verification_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.put(
        "/email/verify",
        description="Verify email using token for authenticated user.",
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthorizationError: status.HTTP_403_FORBIDDEN,
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
    async def verify_email(
        token: str,
        handler: FromDishka[VerifyEmailHandler],
    ) -> dict:
        await handler.execute(VerifyEmailRequest(token=token))
        return {"status": "success", "message": "Email verified"}

    @router.post(
        "/email/verify/send",
        description="Send a verification email to the authenticated user if not verified.",
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthorizationError: status.HTTP_403_FORBIDDEN,
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
    async def send_verification_email(
        handler: FromDishka[SendEmailVerificationHandler],
    ) -> dict:
        await handler.execute(SendEmailVerificationRequest())
        return {"status": "success", "message": "Verification email enqueued"}

    return router


