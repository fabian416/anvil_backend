from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.infrastructure.subscription.handlers.init_subscriptions import (
    InitSubscriptionsHandler,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_subscription_init_router() -> APIRouter:
    router = ErrorAwareRouter(tags=["Subscription"])

    @router.post(
        "/subscription/init",
        description="Initialize default subscriptions (PRO and CORPORATE).",
        dependencies=[Security(bearer_scheme)],
        error_map={
            Exception: status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    async def init_subscriptions(
        handler: FromDishka[InitSubscriptionsHandler],
    ) -> list[dict]:
        return await handler.execute(None)

    return router


