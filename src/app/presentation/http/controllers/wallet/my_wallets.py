"""
My Wallets Endpoint.

Get all wallets for the current authenticated user.
Combines data from local database and Privy API.
"""

from typing import Annotated, Optional
from dataclasses import asdict

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, Field

from app.infrastructure.auth.handlers.wallet_me import (
    GetMyWalletsHandler,
    SyncWalletsHandler,
    WalletsResponse,
)
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


# ============================================================
# Pydantic Response Models
# ============================================================


class WalletResponseModel(BaseModel):
    """Individual wallet in the response."""

    wallet_id: str = Field(..., description="Unique wallet identifier")
    address: str = Field(..., description="Blockchain address")
    chain_type: str = Field(..., description="Blockchain type (ethereum, solana, etc.)")
    wallet_type: str = Field(..., description="Type: embedded, external, server_controlled")
    is_primary: bool = Field(..., description="Whether this is the primary wallet")
    source: str = Field(..., description="Data source: privy, local, or both")
    created_at: Optional[str] = Field(None, description="When the wallet was created")


class MyWalletsResponseModel(BaseModel):
    """Response containing all user wallets."""

    user_id: int = Field(..., description="Local user ID")
    privy_user_id: Optional[str] = Field(None, description="Privy user ID if linked")
    wallets: list[WalletResponseModel] = Field(..., description="List of all wallets")
    primary_wallet_address: Optional[str] = Field(None, description="Primary wallet address")
    privy_connected: bool = Field(..., description="Whether Privy data was fetched")
    message: Optional[str] = Field(None, description="Optional status message")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "privy_user_id": "did:privy:abc123",
                "wallets": [
                    {
                        "wallet_id": "wallet_xyz",
                        "address": "0x1234567890abcdef1234567890abcdef12345678",
                        "chain_type": "ethereum",
                        "wallet_type": "embedded",
                        "is_primary": True,
                        "source": "privy",
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                ],
                "primary_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
                "privy_connected": True,
                "message": None,
            }
        }


class SyncWalletItem(BaseModel):
    """Individual wallet to sync from the frontend."""

    address: str = Field(
        ...,
        description="Wallet blockchain address (0x...)",
        examples=["0x1234567890abcdef1234567890abcdef12345678"],
    )
    chain_type: str = Field(
        default="ethereum",
        description="Blockchain type",
        examples=["ethereum", "polygon", "base"],
    )
    wallet_type: str = Field(
        default="embedded",
        description="Type of wallet: embedded, external, imported",
        examples=["embedded", "external", "imported"],
    )
    privy_wallet_id: Optional[str] = Field(
        None,
        description="Privy wallet ID if available",
        examples=["wallet_abc123"],
    )


class SyncWalletsRequest(BaseModel):
    """Request to sync wallets from frontend."""

    wallet_addresses: list[str] = Field(
        default=[],
        description="(Deprecated) List of wallet addresses - use 'wallets' instead",
        examples=[["0x123...", "0x456..."]],
    )
    wallets: Optional[list[SyncWalletItem]] = Field(
        None,
        description="List of wallet details to sync (preferred over wallet_addresses)",
    )


# ============================================================
# Router
# ============================================================


def create_my_wallets_router() -> APIRouter:
    """Create router for /me wallet endpoints."""

    router = ErrorAwareRouter(tags=["wallet"])

    @router.get(
        "/me",
        response_model=MyWalletsResponseModel,
        status_code=status.HTTP_200_OK,
        summary="Get my wallets",
        description=(
            "Get all wallets associated with the current authenticated user. "
            "This combines data from the local database (primary wallet) and "
            "the Privy API (all linked wallets). If Privy is unavailable, "
            "only local data is returned."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_my_wallets(
        handler: FromDishka[GetMyWalletsHandler],
    ) -> MyWalletsResponseModel:
        """
        Get all wallets for the authenticated user.

        Returns wallets from:
        - Local database (primary wallet stored during login)
        - Privy API (all linked wallets)

        If Privy fetch fails, only local data is returned with a message.
        """
        result = await handler.execute()

        return MyWalletsResponseModel(
            user_id=result.user_id,
            privy_user_id=result.privy_user_id,
            wallets=[
                WalletResponseModel(
                    wallet_id=w.wallet_id,
                    address=w.address,
                    chain_type=w.chain_type,
                    wallet_type=w.wallet_type,
                    is_primary=w.is_primary,
                    source=w.source,
                    created_at=w.created_at,
                )
                for w in result.wallets
            ],
            primary_wallet_address=result.primary_wallet_address,
            privy_connected=result.privy_connected,
            message=result.message,
        )

    @router.post(
        "/sync",
        response_model=MyWalletsResponseModel,
        status_code=status.HTTP_200_OK,
        summary="Sync wallets from frontend",
        description=(
            "Sync the list of connected wallets from the frontend. "
            "This allows the backend to know about wallets that were "
            "connected via the Privy SDK in the browser. "
            "Supports both legacy 'wallet_addresses' and new 'wallets' format."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def sync_wallets(
        request: SyncWalletsRequest,
        handler: FromDishka[SyncWalletsHandler],
    ) -> MyWalletsResponseModel:
        """
        Sync wallets from the frontend.

        The frontend should call this after connecting or importing wallets
        to inform the backend of all connected addresses and their types.
        
        Supports:
        - Legacy format: wallet_addresses (list of strings)
        - New format: wallets (list of SyncWalletItem with metadata)
        """
        # Convert to handler format - prefer 'wallets' if provided
        if request.wallets:
            wallet_data = [
                {
                    "address": w.address,
                    "chain_type": w.chain_type,
                    "wallet_type": w.wallet_type,
                    "privy_wallet_id": w.privy_wallet_id,
                }
                for w in request.wallets
            ]
        else:
            # Legacy format - convert addresses to dict format
            wallet_data = [
                {
                    "address": addr,
                    "chain_type": "ethereum",
                    "wallet_type": "unknown",
                    "privy_wallet_id": None,
                }
                for addr in request.wallet_addresses
            ]

        result = await handler.execute(wallet_data)

        return MyWalletsResponseModel(
            user_id=result.user_id,
            privy_user_id=result.privy_user_id,
            wallets=[
                WalletResponseModel(
                    wallet_id=w.wallet_id,
                    address=w.address,
                    chain_type=w.chain_type,
                    wallet_type=w.wallet_type,
                    is_primary=w.is_primary,
                    source=w.source,
                    created_at=w.created_at,
                )
                for w in result.wallets
            ],
            primary_wallet_address=result.primary_wallet_address,
            privy_connected=result.privy_connected,
            message=result.message,
        )

    return router
