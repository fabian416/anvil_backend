"""
Update Wallet Controller

Admin endpoint to update wallet configuration in Privy.
"""

from datetime import datetime
from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.application.commands.wallet.update_privy_wallet import (
    UpdatePrivyWallet,
    UpdatePrivyWalletRequest,
    WalletNotFoundError,
    WalletUpdateError,
)
from app.application.common.exceptions.authorization import AuthorizationError
from app.application.queries.wallet.get_privy_wallet_details import (
    AdminWalletDetailsDTO,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class AdditionalSignerRequest(BaseModel):
    """Additional signer configuration."""

    model_config = ConfigDict(frozen=True)

    signer_id: str = Field(description="The signer ID")
    override_policy_ids: list[str] | None = Field(
        default=None,
        description="Override policy IDs for this signer",
    )


class UpdateWalletRequest(BaseModel):
    """
    Request to update wallet configuration.

    All fields are optional - only provided fields will be updated.
    """

    model_config = ConfigDict(frozen=True)

    policy_ids: list[str] | None = Field(
        default=None,
        description="Policy IDs to attach to this wallet",
    )
    owner: dict[str, Any] | None = Field(
        default=None,
        description="New owner object (e.g., {'user_id': 'did:privy:xxx'})",
    )
    owner_id: str | None = Field(
        default=None,
        description="New owner ID (alternative to owner object)",
    )
    additional_signers: list[AdditionalSignerRequest] | None = Field(
        default=None,
        description="Additional signers to configure",
    )

    @model_validator(mode="after")
    def validate_owner_fields(self) -> "UpdateWalletRequest":
        """Ensure only one of owner or owner_id is provided."""
        if self.owner is not None and self.owner_id is not None:
            raise ValueError("Cannot provide both 'owner' and 'owner_id'")
        return self


class AdditionalSignerResponse(BaseModel):
    """Additional signer information."""

    model_config = ConfigDict(frozen=True)

    signer_id: str = Field(description="The signer ID")
    override_policy_ids: list[str] | None = Field(
        default=None,
        description="Override policy IDs for this signer",
    )


class UpdateWalletResponse(BaseModel):
    """Response from wallet update operation."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(description="Whether the update was successful")
    changes_applied: dict[str, Any] = Field(
        default_factory=dict,
        description="Changes that were applied",
    )

    # Updated wallet details
    local_wallet_id: int | None = Field(description="Local database wallet ID")
    privy_wallet_id: str = Field(description="Privy wallet ID")
    address: str = Field(description="Blockchain wallet address")
    chain_type: str = Field(description="Blockchain type")
    user_id: int | None = Field(description="Local user ID")
    owner_type: str | None = Field(description="Owner type")
    owner_id: str | None = Field(description="Owner ID in Privy")
    policy_ids: list[str] = Field(default_factory=list)
    additional_signers: list[AdditionalSignerResponse] = Field(default_factory=list)
    provider: str = Field(default="privy")
    status: str = Field(default="active")
    is_recoverable: bool = Field(default=True)
    created_at: datetime | None = None
    exported_at: datetime | None = None
    imported_at: datetime | None = None
    last_privy_sync_at: datetime | None = None

    @classmethod
    def from_result(
        cls,
        success: bool,
        wallet_details: AdminWalletDetailsDTO,
        changes_applied: dict[str, Any],
    ) -> "UpdateWalletResponse":
        """Create response from command result."""
        return cls(
            success=success,
            changes_applied=changes_applied,
            local_wallet_id=wallet_details.local_wallet_id,
            privy_wallet_id=wallet_details.privy_wallet_id,
            address=wallet_details.address,
            chain_type=wallet_details.chain_type,
            user_id=wallet_details.user_id,
            owner_type=wallet_details.owner_type,
            owner_id=wallet_details.owner_id,
            policy_ids=wallet_details.policy_ids,
            additional_signers=[
                AdditionalSignerResponse(
                    signer_id=s.signer_id,
                    override_policy_ids=s.override_policy_ids,
                )
                for s in wallet_details.additional_signers
            ],
            provider=wallet_details.provider,
            status=wallet_details.status,
            is_recoverable=wallet_details.is_recoverable,
            created_at=wallet_details.created_at,
            exported_at=wallet_details.exported_at,
            imported_at=wallet_details.imported_at,
            last_privy_sync_at=wallet_details.last_privy_sync_at,
        )


def create_update_wallet_router() -> APIRouter:
    """Create the update wallet router."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{privy_wallet_id}",
        description=getdoc(UpdatePrivyWallet),
        response_model=UpdateWalletResponse,
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            WalletNotFoundError: status.HTTP_404_NOT_FOUND,
            WalletUpdateError: rule(
                status=status.HTTP_502_BAD_GATEWAY,
                on_error=log_error,
            ),
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_wallet(
        privy_wallet_id: str,
        request_body: UpdateWalletRequest,
        command_service: FromDishka[UpdatePrivyWallet],
    ) -> UpdateWalletResponse:
        """
        Update wallet configuration in Privy.

        This endpoint allows admins to update wallet configuration
        including policy IDs, owner, and additional signers.

        Changes are synced to the local database.

        **Admin only.**
        """
        # Convert request to command format
        additional_signers = None
        if request_body.additional_signers is not None:
            additional_signers = [
                {
                    "signer_id": s.signer_id,
                    "override_policy_ids": s.override_policy_ids,
                }
                for s in request_body.additional_signers
            ]

        request = UpdatePrivyWalletRequest(
            privy_wallet_id=privy_wallet_id,
            policy_ids=request_body.policy_ids,
            owner=request_body.owner,
            owner_id=request_body.owner_id,
            additional_signers=additional_signers,
        )

        result = await command_service.execute(request)

        return UpdateWalletResponse.from_result(
            success=result.success,
            wallet_details=result.wallet_details,
            changes_applied=result.changes_applied,
        )

    return router
