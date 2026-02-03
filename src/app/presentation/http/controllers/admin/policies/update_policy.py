"""
Update Policy Controller

Admin endpoint to update a Privy policy by id.
"""

from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.commands.policy.update_privy_policy import (
    PolicyNotFoundError,
    PolicyUpdateError,
    UpdatePrivyPolicy,
    UpdatePrivyPolicyRequest,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class UpdatePolicyRequestBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = None
    rules: list[dict[str, Any]] | None = Field(default=None)
    authorization_signature: str | None = Field(
        default=None,
        description="Optional privy-authorization-signature for owner-protected policies.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional app-defined metadata (stored locally for advanced search).",
    )


class UpdatePolicyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    version: str
    chain_type: str
    rules: list[dict[str, Any]] = Field(default_factory=list)
    owner_id: str | None = None


def create_update_policy_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{policy_id}",
        description=getdoc(UpdatePrivyPolicy),
        response_model=UpdatePolicyResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyNotFoundError: status.HTTP_404_NOT_FOUND,
            PolicyUpdateError: rule(
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
    async def update_policy(
        policy_id: str,
        request_body: UpdatePolicyRequestBody,
        command: FromDishka[UpdatePrivyPolicy],
    ) -> UpdatePolicyResponse:
        result = await command.execute(
            UpdatePrivyPolicyRequest(
                policy_id=policy_id,
                name=request_body.name,
                rules=request_body.rules,
                authorization_signature=request_body.authorization_signature,
                metadata=request_body.metadata,
            )
        )
        policy = result.policy
        return UpdatePolicyResponse(
            id=policy.id,
            name=policy.name,
            version=policy.version,
            chain_type=policy.chain_type,
            rules=policy.rules,
            owner_id=policy.owner_id,
        )

    return router
