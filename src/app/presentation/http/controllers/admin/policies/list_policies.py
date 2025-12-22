"""
List Policies Controller

Admin endpoint to list Privy policies.
"""

from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.queries.policy.list_privy_policies import (
    ListPrivyPolicies,
    ListPrivyPoliciesRequest,
    PolicyListError,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class PolicySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    version: str
    chain_type: str
    owner_id: str | None = None


class ListPoliciesResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    policies: list[PolicySummary] = Field(default_factory=list)
    next_cursor: str | None = None
    total_count: int | None = None
    raw: Any | None = None


def create_list_policies_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        description=getdoc(ListPrivyPolicies),
        response_model=ListPoliciesResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyListError: rule(
                status=status.HTTP_502_BAD_GATEWAY,
                on_error=log_error,
            ),
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
    )
    @inject
    async def list_policies(
        query: FromDishka[ListPrivyPolicies],
        cursor: str | None = Query(default=None),
        limit: int | None = Query(default=None, ge=1, le=1000),
        chain_type: str | None = Query(default=None),
        include_raw: bool = Query(default=False),
        refresh: bool = Query(default=False, description="If true, refresh from Privy before returning."),
        meta_key: str | None = Query(default=None, description="Filter by local metadata key."),
        meta_value: str | None = Query(default=None, description="Filter by local metadata key value."),
    ) -> ListPoliciesResponse:
        result = await query.execute(
            ListPrivyPoliciesRequest(
                cursor=cursor,
                limit=limit,
                chain_type=chain_type,
                refresh=refresh,
                meta_key=meta_key,
                meta_value=meta_value,
            )
        )

        policies = [
            PolicySummary(
                id=p.id,
                name=p.name,
                version=p.version,
                chain_type=p.chain_type,
                owner_id=p.owner_id,
            )
            for p in result.policies
        ]

        return ListPoliciesResponse(
            policies=policies,
            next_cursor=result.next_cursor,
            total_count=result.total_count,
            raw=result.raw if include_raw else None,
        )

    return router

