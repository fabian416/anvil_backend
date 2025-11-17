from fastapi import APIRouter

from app.presentation.http.controllers.atlas.cities import create_cities_router
from app.presentation.http.controllers.atlas.countries import create_countries_router
from app.presentation.http.controllers.atlas.init import create_init_atlas_router


def create_atlas_router() -> APIRouter:
    router = APIRouter(
        prefix="/atlas",
        tags=["Atlas"],
    )

    sub_routers = (
        create_countries_router(),
        create_cities_router(),
        create_init_atlas_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router


