"""
Policy Rules Controller

Admin endpoints to manage individual policy rules in Privy.
"""

from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.commands.policy.manage_privy_policy_rules import (
    CreatePrivyPolicyRule,
    CreatePrivyPolicyRuleRequest,
    DeletePrivyPolicyRule,
    DeletePrivyPolicyRuleRequest,
    PolicyNotFoundError,
    PolicyRuleOperationError,
    UpdatePrivyPolicyRule,
    UpdatePrivyPolicyRuleRequest,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class PolicyRuleRequestBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule: dict[str, Any] = Field(
        description="Rule payload as defined by Privy policy engine.",
    )
    authorization_signature: str | None = Field(
        default=None,
        description="Optional privy-authorization-signature for owner-protected policies.",
    )


class PolicyRuleResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    result: dict[str, Any]


def create_policy_rules_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{policy_id}/rules",
        description=getdoc(CreatePrivyPolicyRule),
        response_model=PolicyRuleResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyNotFoundError: status.HTTP_404_NOT_FOUND,
            PolicyRuleOperationError: rule(
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
    async def create_rule(
        policy_id: str,
        request_body: PolicyRuleRequestBody,
        command: FromDishka[CreatePrivyPolicyRule],
    ) -> PolicyRuleResponse:
        result = await command.execute(
            CreatePrivyPolicyRuleRequest(
                policy_id=policy_id,
                rule=request_body.rule,
                authorization_signature=request_body.authorization_signature,
            )
        )
        return PolicyRuleResponse(result=result)

    @router.patch(
        "/{policy_id}/rules/{rule_id}",
        description=getdoc(UpdatePrivyPolicyRule),
        response_model=PolicyRuleResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyNotFoundError: status.HTTP_404_NOT_FOUND,
            PolicyRuleOperationError: rule(
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
    async def update_rule(
        policy_id: str,
        rule_id: str,
        request_body: PolicyRuleRequestBody,
        command: FromDishka[UpdatePrivyPolicyRule],
    ) -> PolicyRuleResponse:
        result = await command.execute(
            UpdatePrivyPolicyRuleRequest(
                policy_id=policy_id,
                rule_id=rule_id,
                rule=request_body.rule,
                authorization_signature=request_body.authorization_signature,
            )
        )
        return PolicyRuleResponse(result=result)

    @router.delete(
        "/{policy_id}/rules/{rule_id}",
        description=getdoc(DeletePrivyPolicyRule),
        response_model=PolicyRuleResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyNotFoundError: status.HTTP_404_NOT_FOUND,
            PolicyRuleOperationError: rule(
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
    async def delete_rule(
        policy_id: str,
        rule_id: str,
        command: FromDishka[DeletePrivyPolicyRule],
        authorization_signature: str | None = None,
    ) -> PolicyRuleResponse:
        result = await command.execute(
            DeletePrivyPolicyRuleRequest(
                policy_id=policy_id,
                rule_id=rule_id,
                authorization_signature=authorization_signature,
            )
        )
        return PolicyRuleResponse(result=result)

    return router

