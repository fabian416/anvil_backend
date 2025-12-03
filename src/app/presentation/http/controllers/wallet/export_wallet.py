"""
Export Wallet Endpoint
Exports a user's embedded wallet private key.
"""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Security, status
from pydantic import BaseModel, Field

from app.application.commands.wallet.export_wallet import (
    ExportWallet,
    ExportWalletResult,
    WalletExportError,
    WalletNotFoundError,
)
from fastapi import APIRouter
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

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
        "**Security Note**: This endpoint should only be accessible to authenticated users "
        "who own the wallet being exported."
    ),
    responses={
        200: {"description": "Wallet exported successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Wallet not found", "model": ErrorResponse},
        500: {"description": "Export failed", "model": ErrorResponse},
    },
)
@inject
async def export_wallet(
    request: ExportWalletRequest,
    export_wallet_cmd: FromDishka[ExportWallet],
    authorization: Annotated[str, Security(bearer_scheme)],
) -> ExportWalletResponse:
    """
    Export a wallet's private key.
    
    This endpoint:
    1. Validates the user is authenticated
    2. Generates an HPKE key pair for secure key transfer
    3. Calls Privy API to export the wallet (encrypted)
    4. Decrypts the private key using HPKE
    5. Returns the decrypted private key
    
    **Important**: The private key is sensitive data. Ensure proper
    security measures are in place when handling this response.
    """
    from fastapi import HTTPException

    try:
        result = await export_wallet_cmd.execute(
            wallet_id=request.wallet_id,
            wallet_address=request.wallet_address,
        )
        return ExportWalletResponse.from_result(result)

    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except WalletExportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

