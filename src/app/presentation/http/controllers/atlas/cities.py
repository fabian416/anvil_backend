from inspect import getdoc
from typing import Annotated, Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.atlas.queries import (
    ListStatesByCountryQueryService,
    ListStatesByCountryRequest,
    SearchCitiesQueryService,
    SearchCitiesRequest,
    SearchCitiesResponse,
)
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    ServiceUnavailableTranslator,
)


def create_cities_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/cities/search",
        description=getdoc(SearchCitiesQueryService),
        error_map={},
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def search_cities(
        name: Optional[str] = None,
        country_id: Optional[int] = None,
        state_id: Optional[str] = None,
        state_code: Optional[str] = None,
        state_name: Optional[str] = None,
        country_code: Optional[str] = None,
        wikiDataId: Optional[str] = None,
        limit: Annotated[int, Depends(lambda: 10)] = 10,
        offset: Annotated[int, Depends(lambda: 0)] = 0,
        interactor: FromDishka[SearchCitiesQueryService] = None,  # type: ignore
    ) -> SearchCitiesResponse:
        request = SearchCitiesRequest(
            name=name,
            country_id=country_id,
            state_id=state_id,
            state_code=state_code,
            state_name=state_name,
            country_code=country_code,
            wiki_data_id=wikiDataId,
            limit=limit,
            offset=offset,
        )
        return await interactor.execute(request)

    @router.get(
        "/states/{country_id}",
        description=getdoc(ListStatesByCountryQueryService),
        error_map={},
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def list_states_by_country(
        country_id: Annotated[int, Path()],
        interactor: FromDishka[ListStatesByCountryQueryService] = None,  # type: ignore
    ) -> list:
        request = ListStatesByCountryRequest(country_id)
        return [s.__dict__ for s in await interactor.execute(request)]

    return router


