from inspect import getdoc
from pathlib import Path
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter

from app.infrastructure.atlas.handlers.init_countries import (
    InitCountriesHandler,
    InitCountriesResult,
)
from app.infrastructure.atlas.handlers.init_cities import (
    InitCitiesHandler,
    InitCitiesResult,
)
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme


def create_init_atlas_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/countries/init",
        description=getdoc(InitCountriesHandler),
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def init_countries(
        handler: FromDishka[InitCountriesHandler],
    ) -> InitCountriesResult:
        return await handler.execute()

    @router.post(
        "/cities/init",
        description=getdoc(InitCitiesHandler),
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def init_cities(
        handler: FromDishka[InitCitiesHandler],
    ) -> InitCitiesResult:
        return await handler.execute()

    return router


