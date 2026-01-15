"""
Complete Swap Endpoint

POST /wallet/swaps/complete - Save completed swap transaction to database.

Called by frontend after successful Privy + 0x swap execution to persist
transaction data for history and analytics.
"""

import logging
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Security, status
from pydantic import BaseModel, Field

from app.application.commands.wallet.save_swap_transaction import (
    SaveSwapTransactionCommand,
    SaveSwapTransactionHandler,
)
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class CompleteSwapRequest(BaseModel):
    """Request to save completed swap transaction."""

    # Transaction details
    tx_hash: str = Field(..., description="Transaction hash (0x...)")
    chain: str = Field(..., description="Chain name (base, ethereum, etc)")

    # Swap details
    from_token: str = Field(..., description="Source token symbol (ETH, USDC, etc)")
    to_token: str = Field(..., description="Destination token symbol")
    from_amount: str = Field(..., description="Amount swapped (in token units)")
    to_amount: str = Field(..., description="Amount received (in token units)")

    # Optional metadata
    exchange_rate: str | None = Field(None, description="Exchange rate")
    gas_fee_usd: str | None = Field(None, description="Gas fee in USD")
    slippage: str | None = Field(None, description="Slippage percentage")
    conversation_id: str | None = Field(None, description="Chat conversation ID")

    class Config:
        json_schema_extra = {
            "example": {
                "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "chain": "base",
                "from_token": "ETH",
                "to_token": "USDC",
                "from_amount": "0.9",
                "to_amount": "3000.00",
                "exchange_rate": "3333.33",
                "gas_fee_usd": "0.99",
                "slippage": "1.0",
                "conversation_id": "conv_123",
            }
        }


class CompleteSwapResponse(BaseModel):
    """Response after saving swap transaction."""

    success: bool = Field(..., description="Whether save was successful")
    transaction_id: int = Field(..., description="Database transaction ID")
    tx_hash: str = Field(..., description="Transaction hash")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "transaction_id": 42,
                "tx_hash": "0x1234...cdef",
                "message": "Swap transaction saved successfully",
            }
        }


# ============================================================================
# Endpoint
# ============================================================================


@router.post(
    "/swaps/complete",
    response_model=CompleteSwapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save completed swap transaction",
    description="""
Save a completed swap transaction to the database.

This endpoint is called by the frontend after a successful Privy + 0x swap
to persist the transaction data for:
- Transaction history
- Portfolio analytics
- Audit trail

**Authentication Required:** Yes (Bearer token)

**Flow:**
1. User executes swap via Privy + 0x on frontend
2. Frontend waits for transaction confirmation
3. Frontend calls this endpoint to save transaction data
4. Backend persists to database
5. Frontend shows success message in chat

**Example Usage:**
```javascript
// After successful swap with Privy
const receipt = await provider.waitForTransaction(txHash);

await fetch('/api/v1/wallet/swaps/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    tx_hash: txHash,
    chain: 'base',
    from_token: 'ETH',
    to_token: 'USDC',
    from_amount: '0.9',
    to_amount: '3000.00',
    exchange_rate: '3333.33',
    gas_fee_usd: '0.99',
    conversation_id: conversationId
  })
});
```
""",
    responses={
        201: {
            "description": "Swap transaction saved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "transaction_id": 42,
                        "tx_hash": "0x1234...cdef",
                        "message": "Swap transaction saved successfully",
                    }
                }
            },
        },
        400: {"description": "Invalid request data"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"},
    },
)
@inject
async def complete_swap(
    request: CompleteSwapRequest,
    authorization: Annotated[str, Security(bearer_scheme)],  # noqa: ARG001
    handler: FromDishka[SaveSwapTransactionHandler],
    current_user_service: FromDishka[CurrentUserService],
) -> CompleteSwapResponse:
    """
    Save completed swap transaction.

    Args:
        request: Swap transaction data
        handler: Save swap transaction handler (injected)
        current_user_service: Current user service (injected)
        authorization: Bearer token (for OpenAPI docs)

    Returns:
        CompleteSwapResponse with transaction ID

    Raises:
        HTTPException: If save fails
    """
    try:
        # Get authenticated user
        current_user = await current_user_service.get_current_user()
        user_id = current_user.id_.value

        logger.info(
            "[COMPLETE_SWAP] User %d saving swap: %s %s → %s %s (tx: %s)",
            user_id,
            request.from_amount,
            request.from_token,
            request.to_amount,
            request.to_token,
            request.tx_hash[:10] + "...",
        )

        # Build command
        command = SaveSwapTransactionCommand(
            user_id=user_id,
            conversation_id=request.conversation_id,
            tx_hash=request.tx_hash,
            chain=request.chain,
            from_token=request.from_token,
            to_token=request.to_token,
            from_amount=request.from_amount,
            to_amount=request.to_amount,
            exchange_rate=request.exchange_rate,
            gas_fee_usd=request.gas_fee_usd,
            slippage=request.slippage,
        )

        # Execute command
        result = await handler.handle(command)

        logger.info(
            "[COMPLETE_SWAP] ✅ Swap saved: transaction_id=%d",
            result.transaction_id,
        )

        return CompleteSwapResponse(
            success=True,
            transaction_id=result.transaction_id,
            tx_hash=result.tx_hash,
            message="Swap transaction saved successfully",
        )

    except ValueError as e:
        logger.error("[COMPLETE_SWAP] ❌ Validation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "[COMPLETE_SWAP] ❌ Failed to save swap: %s",
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save swap transaction",
        )
