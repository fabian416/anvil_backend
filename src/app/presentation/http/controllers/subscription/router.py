from dataclasses import asdict
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.infrastructure.subscription.handlers.get_subscriptions import (
    GetSubscriptionsHandler,
)
from app.infrastructure.subscription.handlers.init_subscriptions import (
    InitSubscriptionsHandler,
)
from app.infrastructure.subscription.handlers.customer_subscription import (
    CreateSubscriptionHandler,
    CreateSubscriptionRequest,
)
from app.infrastructure.subscription.handlers.cancel_subscription import (
    CancelSubscriptionHandler,
    CancelSubscriptionRequest,
)
from app.infrastructure.subscription.handlers.success_subscription import (
    SubscriptionSuccessHandler,
    SubscriptionSuccessRequest,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_subscription_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/subscription", tags=["Subscription"])

    @router.get(
        "/",
        description="Get all available subscriptions",
        dependencies=[Security(bearer_scheme)],
        error_map={
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
    async def get_subscriptions(
        handler: FromDishka[GetSubscriptionsHandler],
    ) -> list[dict]:
        items = await handler.execute()
        return [asdict(item) for item in items]

    @router.post(
        "/init",
        description="Initialize default subscriptions (PRO and CORPORATE).",
        dependencies=[Security(bearer_scheme)],
        error_map={
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


    @router.post(
        "/{subscription_id}/subscribe",
        description="Create a subscription for a customer",
        dependencies=[Security(bearer_scheme)],
        error_map={
            Exception: status.HTTP_400_BAD_REQUEST,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def create_subscription(
        subscription_id: int,
        handler: FromDishka[CreateSubscriptionHandler],
        request_host: str | None = None,
    ) -> dict:
        # Build callback base url from request headers if available
        # Fallback handled in handler
        return await handler.execute(
            CreateSubscriptionRequest(
                subscription_id=subscription_id,
                callback_base_url=request_host,
            )
        )

    @router.post(
        "/{subscription_id}/cancel",
        description="Cancel a subscription",
        dependencies=[Security(bearer_scheme)],
        error_map={
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def cancel_subscription(
        subscription_id: int,
        handler: FromDishka[CancelSubscriptionHandler],
    ) -> dict:
        return await handler.execute(CancelSubscriptionRequest(subscription_id=subscription_id))

    @router.get(
        "/success",
        description="Handle successful subscription payment",
        error_map={
            Exception: status.HTTP_400_BAD_REQUEST,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def subscription_success(
        session_id: str,
        handler: FromDishka[SubscriptionSuccessHandler],
    ) -> dict:
        return await handler.execute(SubscriptionSuccessRequest(session_id=session_id))

    @router.get(
        "/cancel",
        description="Handle cancelled subscription payment",
        error_map={
            Exception: status.HTTP_400_BAD_REQUEST,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def subscription_cancel(
        session_id: str,
        handler: FromDishka[CancelSubscriptionHandler],
    ) -> dict:
        # reuse cancel handler to mark cancelled based on session id
        return await handler.execute(CancelSubscriptionRequest(subscription_user_id=int(session_id)))

    return router


