"""
Get Wallet Details Controller

Admin endpoint to retrieve detailed wallet information.
"""

from datetime import datetime
from inspect import getdoc
from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.queries.wallet.get_privy_wallet_details import (
    AdminWalletDetailsDTO,
    GetPrivyWalletDetails,
    GetPrivyWalletDetailsRequest,
    WalletNotFoundError,
    WalletQueryError,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class AdditionalSignerResponse(BaseModel):
    """Additional signer information."""

    model_config = ConfigDict(frozen=True)

    signer_id: str = Field(description="The signer ID")
    override_policy_ids: list[str] | None = Field(
        default=None,
        description="Override policy IDs for this signer",
    )


class AdminWalletDetailsResponse(BaseModel):
    """
    Admin-facing wallet details response.

    Contains both local database data and live Privy API data.
    """

    model_config = ConfigDict(frozen=True)

    # Identification
    local_wallet_id: int | None = Field(
        description="Local database wallet ID (null if not in local DB)"
    )
    privy_wallet_id: str = Field(description="Privy wallet ID")
    address: str = Field(description="Blockchain wallet address")
    chain_type: str = Field(description="Blockchain type (ethereum, base, etc.)")

    # User association
    user_id: int | None = Field(description="Local user ID (null if not in local DB)")
    owner_type: str | None = Field(
        description="Owner type (user, authorization_key, etc.)"
    )
    owner_id: str | None = Field(description="Owner ID in Privy")

    # Privy configuration (editable via admin)
    policy_ids: list[str] = Field(
        default_factory=list,
        description="Policy IDs attached to this wallet",
    )
    additional_signers: list[AdditionalSignerResponse] = Field(
        default_factory=list,
        description="Additional signers configured for this wallet",
    )

    # Status
    provider: str = Field(default="privy", description="Wallet provider")
    status: str = Field(default="active", description="Wallet status")
    is_recoverable: bool = Field(
        default=True,
        description="Whether the wallet is recoverable",
    )

    # Timestamps
    created_at: datetime | None = Field(description="When the wallet was created")
    exported_at: datetime | None = Field(
        description="When the wallet was last exported"
    )
    imported_at: datetime | None = Field(description="When the wallet was imported")
    last_privy_sync_at: datetime | None = Field(
        description="Last time we synced with Privy API"
    )

    # Raw data for debugging (optional, can be removed in production)
    privy_raw_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw Privy API response for debugging",
    )

    @classmethod
    def from_dto(cls, dto: AdminWalletDetailsDTO) -> "AdminWalletDetailsResponse":
        """Create response from DTO."""
        return cls(
            local_wallet_id=dto.local_wallet_id,
            privy_wallet_id=dto.privy_wallet_id,
            address=dto.address,
            chain_type=dto.chain_type,
            user_id=dto.user_id,
            owner_type=dto.owner_type,
            owner_id=dto.owner_id,
            policy_ids=dto.policy_ids,
            additional_signers=[
                AdditionalSignerResponse(
                    signer_id=s.signer_id,
                    override_policy_ids=s.override_policy_ids,
                )
                for s in dto.additional_signers
            ],
            provider=dto.provider,
            status=dto.status,
            is_recoverable=dto.is_recoverable,
            created_at=dto.created_at,
            exported_at=dto.exported_at,
            imported_at=dto.imported_at,
            last_privy_sync_at=dto.last_privy_sync_at,
            privy_raw_data=dto.privy_raw_data,
        )


def create_get_wallet_details_router() -> APIRouter:
    """Create the get wallet details router."""
    router = ErrorAwareRouter()

    @router.get(
        "/{privy_wallet_id}",
        description=getdoc(GetPrivyWalletDetails),
        response_model=AdminWalletDetailsResponse,
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            WalletNotFoundError: status.HTTP_404_NOT_FOUND,
            WalletQueryError: rule(
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
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_wallet_details(
        privy_wallet_id: str,
        query_service: FromDishka[GetPrivyWalletDetails],
    ) -> AdminWalletDetailsResponse:
        """
        Get detailed wallet information for admin management.

        This endpoint retrieves wallet configuration from both the local
        database and Privy API, merging the data for admin viewing.

        **Admin only.**
        """
        request = GetPrivyWalletDetailsRequest(privy_wallet_id=privy_wallet_id)
        result = await query_service.execute(request)
        return AdminWalletDetailsResponse.from_dto(result)

    return router
