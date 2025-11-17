from inspect import getdoc
from typing import Annotated, Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Security, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.atlas.queries import (
    SearchCountriesQueryService,
    SearchCountriesRequest,
    SearchCountriesResponse,
)
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    ServiceUnavailableTranslator,
)


def create_countries_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/countries/search",
        description=getdoc(SearchCountriesQueryService),
        error_map={},
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def search_countries(
        name: Optional[str] = None,
        iso2: Optional[str] = None,
        iso3: Optional[str] = None,
        region: Optional[str] = None,
        subregion: Optional[str] = None,
        currency: Optional[str] = None,
        limit: Annotated[int, Depends(lambda: 10)] = 10,
        offset: Annotated[int, Depends(lambda: 0)] = 0,
        interactor: FromDishka[SearchCountriesQueryService] = None,  # type: ignore
    ) -> SearchCountriesResponse:
        request = SearchCountriesRequest(
            name=name,
            iso2=iso2,
            iso3=iso3,
            region=region,
            subregion=subregion,
            currency=currency,
            limit=limit,
            offset=offset,
        )
        return await interactor.execute(request)

    return router


