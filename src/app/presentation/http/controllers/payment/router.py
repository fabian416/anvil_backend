from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.common.services.current_user import CurrentUserService
from app.application.subscription.ports import PaymentRepository
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


def create_payment_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/payments", tags=["payments"])

    @router.get(
        "/user",
        description="Get paginated list of user's payments with related subscription data",
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
    async def get_user_payments(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=100, description="Items per page"),
        current_user_service: FromDishka[CurrentUserService] = None,  # type: ignore[assignment]
        payments: FromDishka[PaymentRepository] = None,  # type: ignore[assignment]
    ) -> dict:
        current_user = await current_user_service.get_current_user()
        offset = (page - 1) * per_page
        items = await payments.read_by_user_paginated(user_id=current_user.id_.value, offset=offset, limit=per_page)
        return {"items": items, "page": page, "per_page": per_page}

    @router.post(
        "/transaction",
        description="Create a new payment transaction",
        dependencies=[Security(bearer_scheme)],
        error_map={
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
    async def create_payment_transaction(
        amount: float = Body(..., embed=True),
        currency: str = Body(..., embed=True),
        description: str = Body(..., embed=True),
        current_user_service: FromDishka[CurrentUserService] = None,  # type: ignore[assignment]
        payments: FromDishka[PaymentRepository] = None,  # type: ignore[assignment]
    ) -> dict:
        current_user = await current_user_service.get_current_user()
        result = await payments.find_or_create_transaction(
            user_id=current_user.id_.value,
            amount=amount,
            currency=currency,
            description=description,
        )
        return {"status": "success", "payment": result}

    return router


