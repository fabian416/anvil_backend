"""
Create Policy Controller

Admin endpoint to create a Privy policy.
"""

from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.application.commands.policy.create_privy_policy import (
    CreatePrivyPolicy,
    CreatePrivyPolicyRequest,
    PolicyCreateError,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class CreatePolicyRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str = Field(default="1.0")
    name: str
    chain_type: str = Field(default="ethereum")
    rules: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional app-defined metadata (stored locally for advanced search).",
    )

    owner: dict[str, Any] | None = Field(
        default=None,
        description="Optional owner object (e.g., {'public_key': '...'}).",
    )
    owner_id: str | None = Field(
        default=None,
        description="Optional owner_id (do not provide if owner provided).",
    )
    authorization_signature: str | None = Field(
        default=None,
        description="Optional privy-authorization-signature for owner-protected policies.",
    )

    @field_validator("owner", mode="before")
    @classmethod
    def normalize_owner(cls, v: Any) -> Any:
        """
        Privy expects `owner` to be either omitted/null, or contain required keys
        like `user_id` or `public_key`.

        Some clients may send `{}`; normalize that to `None`.
        """
        if v is None:
            return None
        if isinstance(v, dict) and len(v) == 0:
            return None
        return v

    @model_validator(mode="after")
    def validate_owner_fields(self) -> "CreatePolicyRequest":
        """Validate `owner` shape and mutual exclusivity with `owner_id`."""
        if self.owner is not None and self.owner_id is not None:
            raise ValueError("Cannot provide both 'owner' and 'owner_id'")

        if self.owner is not None:
            if not isinstance(self.owner, dict):
                raise ValueError("'owner' must be an object")
            owner_user_id = self.owner.get("user_id")
            owner_public_key = self.owner.get("public_key")
            if not owner_user_id and not owner_public_key:
                raise ValueError(
                    "'owner' must include either 'user_id' or 'public_key'"
                )

        return self


class CreatePolicyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    version: str
    chain_type: str
    rules: list[dict[str, Any]] = Field(default_factory=list)
    owner_id: str | None = None


def create_create_policy_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/",
        description=getdoc(CreatePrivyPolicy),
        response_model=CreatePolicyResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Security(bearer_scheme)],
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PolicyCreateError: rule(
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
    async def create_policy(
        request_body: CreatePolicyRequest,
        command: FromDishka[CreatePrivyPolicy],
    ) -> CreatePolicyResponse:
        request = CreatePrivyPolicyRequest(
            version=request_body.version,
            name=request_body.name,
            chain_type=request_body.chain_type,
            rules=request_body.rules,
            owner=request_body.owner,
            owner_id=request_body.owner_id,
            authorization_signature=request_body.authorization_signature,
            metadata=request_body.metadata,
        )
        result = await command.execute(request)
        policy = result.policy
        return CreatePolicyResponse(
            id=policy.id,
            name=policy.name,
            version=policy.version,
            chain_type=policy.chain_type,
            rules=policy.rules,
            owner_id=policy.owner_id,
        )

    return router
