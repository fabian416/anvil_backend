from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.common.services.current_user import CurrentUserService
from app.application.notification.ports import NotificationRepository
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_notification_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/notifications", tags=["notifications"])

    @router.get(
        "/",
        description="Get paginated list of user's notifications",
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
    async def get_user_notifications(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=100, description="Items per page"),
        current_user_service: FromDishka[CurrentUserService] = None,  # type: ignore[assignment]
        repo: FromDishka[NotificationRepository] = None,  # type: ignore[assignment]
    ) -> list[dict]:
        current_user = await current_user_service.get_current_user()
        offset = (page - 1) * per_page
        return await repo.read_by_user_paginated(user_id=current_user.id_.value, offset=offset, limit=per_page)

    return router


