"""
Export Wallet Endpoint
Exports a user's embedded wallet private key.

Security:
- Verifies the authenticated user owns the wallet before export
- Returns 403 Forbidden if the wallet doesn't belong to the user
"""

import logging
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Security, status
from pydantic import BaseModel, Field

from app.application.commands.wallet.export_wallet import (
    ExportWallet,
    ExportWalletResult,
    WalletExportError,
    WalletNotFoundError,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    UserNotFoundError,
    WalletProviderError,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

logger = logging.getLogger(__name__)

router = APIRouter()


class ExportWalletRequest(BaseModel):
    """Request to export a wallet's private key."""

    wallet_id: str = Field(
        ...,
        description="The Privy wallet ID to export",
        examples=["g1644aqvat8qxkfqsfzvpuq0"],
    )
    wallet_address: str | None = Field(
        default=None,
        description="Optional wallet address for verification",
        examples=["0x19BFe2684Aedcbd57454bA80440C24a412CE04C7"],
    )


class ExportWalletResponse(BaseModel):
    """Response containing the exported wallet data."""

    wallet_id: str = Field(..., description="The Privy wallet ID")
    address: str = Field(..., description="The wallet address")
    private_key: str = Field(..., description="The decrypted private key")
    chain_type: str = Field(..., description="The blockchain type (e.g., ethereum)")

    @classmethod
    def from_result(cls, result: ExportWalletResult) -> "ExportWalletResponse":
        return cls(
            wallet_id=result.wallet_id,
            address=result.address,
            private_key=result.private_key,
            chain_type=result.chain_type,
        )


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str


@router.post(
    "/export",
    response_model=ExportWalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Export wallet private key",
    description=(
        "Exports the private key of an embedded wallet via Privy API. "
        "The key is decrypted server-side using HPKE and returned to the caller. "
        "**Security**: Only the authenticated user who owns the wallet can export it."
    ),
    responses={
        200: {"description": "Wallet exported successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to export wallet", "model": ErrorResponse},
        404: {"description": "Wallet not found", "model": ErrorResponse},
        500: {"description": "Export failed", "model": ErrorResponse},
    },
)
@inject
async def export_wallet(
    request: ExportWalletRequest,
    export_wallet_cmd: FromDishka[ExportWallet],
    current_user_service: FromDishka[CurrentUserService],
    wallet_provider: FromDishka[EmbeddedWalletProviderPort],
    wallet_repository: FromDishka[WalletRepository],
    authorization: Annotated[str, Security(bearer_scheme)],  # noqa: ARG001
) -> ExportWalletResponse:
    """
    Export a wallet's private key.

    This endpoint:
    1. Validates the user is authenticated
    2. Verifies the wallet belongs to the authenticated user
    3. Generates an HPKE key pair for secure key transfer
    4. Calls Privy API to export the wallet (encrypted)
    5. Decrypts the private key using HPKE
    6. Records the export timestamp (audit trail)
    7. Returns the decrypted private key

    **Important**: The private key is sensitive data. Only the wallet owner
    can export it. Private keys are NEVER logged or persisted.
    """
    # Step 1: Get the current authenticated user
    user = await current_user_service.get_current_user()
    privy_user_id = user.privy_user_id.value if user.privy_user_id else None

    if not privy_user_id:
        logger.warning(
            f"User {user.id_.value} attempted wallet export without Privy account"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a linked Privy account",
        )

    # Step 2: Verify the wallet belongs to the authenticated user
    try:
        user_wallets = await wallet_provider.list_user_wallets(privy_user_id)
        user_wallet_ids = {w.wallet_id for w in user_wallets}

        if request.wallet_id not in user_wallet_ids:
            logger.warning(
                f"User {user.id_.value} attempted to export wallet {request.wallet_id} "
                f"which does not belong to them"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet does not belong to the authenticated user",
            )

        logger.info(
            f"User {user.id_.value} authorized to export wallet {request.wallet_id}"
        )

    except UserNotFoundError:
        # User's privy_user_id exists in local DB but not in Privy
        # This can happen if the user was deleted from Privy
        logger.warning(
            f"User {user.id_.value} has invalid Privy account: {privy_user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privy account not found. Please re-authenticate.",
        ) from None

    except WalletProviderError as e:
        logger.error(f"Failed to verify wallet ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify wallet ownership",
        ) from None

    # Step 3: Proceed with export (user is authorized)
    try:
        result = await export_wallet_cmd.execute(
            wallet_id=request.wallet_id,
            wallet_address=request.wallet_address,
        )

        # Step 4: Record export timestamp for audit (best effort)
        try:
            await wallet_repository.mark_exported(request.wallet_id)
            logger.info(
                f"Recorded export timestamp for wallet {request.wallet_id} "
                f"(user {user.id_.value})"
            )
        except Exception as e:
            # Wallet might not be in local DB (Privy-only wallets)
            logger.debug(
                f"Could not record export timestamp for wallet {request.wallet_id}: {e}"
            )

        return ExportWalletResponse.from_result(result)

    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    except WalletExportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from None
