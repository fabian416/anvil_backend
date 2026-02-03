"""
Get Policy Controller

Admin endpoint to retrieve a Privy policy by id.
"""

from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.commands.policy.get_privy_policy import (
    GetPrivyPolicy,
    GetPrivyPolicyRequest,
    PolicyNotFoundError,
    PolicyQueryError,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class GetPolicyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    version: str
    chain_type: str
    rules: list[dict[str, Any]] = Field(default_factory=list)
    owner_id: str | None = None


def create_get_policy_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{policy_id}",
        description=getdoc(GetPrivyPolicy),
        response_model=GetPolicyResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyNotFoundError: status.HTTP_404_NOT_FOUND,
            PolicyQueryError: rule(
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
    async def get_policy(
        policy_id: str,
        query: FromDishka[GetPrivyPolicy],
    ) -> GetPolicyResponse:
        policy = await query.execute(GetPrivyPolicyRequest(policy_id=policy_id))
        return GetPolicyResponse(
            id=policy.id,
            name=policy.name,
            version=policy.version,
            chain_type=policy.chain_type,
            rules=policy.rules,
            owner_id=policy.owner_id,
        )

    return router
