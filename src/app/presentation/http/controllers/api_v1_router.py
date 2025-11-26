from fastapi import APIRouter

from app.presentation.http.controllers.account.router import create_account_router
from app.presentation.http.controllers.general.router import create_general_router
from app.presentation.http.controllers.admin.user.router import create_users_router
from app.presentation.http.controllers.atlas.router import create_atlas_router
from app.presentation.http.controllers.subscription.router import create_subscription_router
from app.presentation.http.controllers.notification.router import create_notification_router
from app.presentation.http.controllers.payment.router import create_payment_router
from app.presentation.http.controllers.auth.router import create_auth_router
from app.presentation.http.controllers.metrics.router import router as metrics_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/v1",
    )

    sub_routers = (
        create_account_router(),
        create_general_router(),
        create_users_router(),
        create_atlas_router(),
        create_subscription_router(),
        create_notification_router(),
        create_payment_router(),
        create_auth_router(),
        metrics_router,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
