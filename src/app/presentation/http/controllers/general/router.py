from fastapi import APIRouter

from app.presentation.http.controllers.general.healthcheck import (
    create_healthcheck_router,
)
from app.presentation.http.controllers.general.chat_shortcuts import (
    create_chat_shortcuts_router,
)


def create_general_router() -> APIRouter:
    router = APIRouter(
        tags=["General"],
    )

    sub_routers = (
        create_healthcheck_router(),
        create_chat_shortcuts_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
