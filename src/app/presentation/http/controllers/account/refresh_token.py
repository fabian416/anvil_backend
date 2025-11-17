from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter

from app.infrastructure.auth.handlers.refresh_token import (
    RefreshTokenHandler,
    RefreshTokenRequest,
)


def create_refresh_token_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/refresh-token",
        description=getdoc(RefreshTokenHandler),
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def refresh_token(
        request: Request,
        request_data: RefreshTokenRequest,
        handler: FromDishka[RefreshTokenHandler],
    ) -> dict:
        enriched = RefreshTokenRequest(
            refresh_token=request_data.refresh_token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return await handler.execute(enriched)

    return router


