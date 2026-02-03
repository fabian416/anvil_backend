"""Flash Loan API endpoints.

REST API for flash loan operations and management.
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from decimal import Decimal

from app.application.ultra.flash_loan_engine import (
    FlashLoanEngine,
    FlashLoanProtocol,
    FlashLoanRequest,
    LoanStatus,
)


class ProtocolInfoResponse(BaseModel):
    """Response model for protocol information."""

    protocol: str = Field(..., description="Protocol identifier")
    name: str = Field(..., description="Protocol name")
    fee_percentage: float = Field(..., description="Fee percentage")
    max_loan_usd: str = Field(..., description="Maximum loan amount USD")
    supported_tokens: List[str] = Field(..., description="Supported tokens")
    requires_collateral: bool = Field(..., description="Requires collateral")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "protocol": "aave_v3",
                "name": "Aave V3",
                "fee_percentage": 0.09,
                "max_loan_usd": "10000000",
                "supported_tokens": ["USDC", "USDT", "DAI"],
                "requires_collateral": False,
            }
        }
    )


class FlashLoanSimulateRequest(BaseModel):
    """Request model for loan simulation."""

    protocol: str = Field(..., description="Flash loan protocol")
    token_address: str = Field(..., description="Token contract address")
    amount: str = Field(..., description="Loan amount (in token units)")
    receiver_address: str = Field(..., description="Receiver contract address")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "protocol": "balancer",
                "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "amount": "100000",
                "receiver_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            }
        }
    )


class FlashLoanResultResponse(BaseModel):
    """Response model for flash loan result."""

    status: str = Field(..., description="Execution status")
    tx_hash: Optional[str] = Field(None, description="Transaction hash")
    gas_used: Optional[int] = Field(None, description="Gas used")
    gas_price_gwei: Optional[int] = Field(None, description="Gas price (gwei)")
    profit_usd: Optional[str] = Field(None, description="Estimated profit USD")
    fees_paid: str = Field(..., description="Fees paid USD")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "tx_hash": "0x1234567890abcdef...",
                "gas_used": 300000,
                "gas_price_gwei": 30,
                "profit_usd": "450.50",
                "fees_paid": "5.00",
                "error_message": None,
            }
        }
    )


class ProtocolLiquidityResponse(BaseModel):
    """Response model for protocol liquidity."""

    protocol: str = Field(..., description="Protocol identifier")
    token: str = Field(..., description="Token symbol")
    available_liquidity_usd: str = Field(..., description="Available liquidity USD")
    max_loan_usd: str = Field(..., description="Maximum single loan USD")


def create_flash_loans_router() -> APIRouter:
    """Create flash loans router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/user/ultra/flash-loans", tags=["ultra-flash-loans"])

    @router.get(
        "/protocols",
        response_model=List[ProtocolInfoResponse],
        summary="Get flash loan protocols",
        description="Get available flash loan protocols with fees and limits",
    )
    async def get_protocols() -> List[ProtocolInfoResponse]:
        """Get available flash loan protocols.

        Returns information about all supported flash loan protocols including:
        - Protocol name and identifier
        - Fee structure
        - Maximum loan amounts
        - Supported tokens
        - Collateral requirements

        Returns:
            List of protocol information

        Example:
            GET /api/v1/ultra/flash-loans/protocols

            Response:
            [
                {
                    "protocol": "aave_v3",
                    "name": "Aave V3",
                    "fee_percentage": 0.09,
                    "max_loan_usd": "10000000",
                    "supported_tokens": ["USDC", "USDT", "DAI", "WETH", "WBTC"],
                    "requires_collateral": false
                },
                {
                    "protocol": "balancer",
                    "name": "Balancer",
                    "fee_percentage": 0.0,
                    "max_loan_usd": "5000000",
                    "supported_tokens": ["USDC", "USDT", "DAI", "WETH"],
                    "requires_collateral": false
                }
            ]
        """
        try:
            engine = FlashLoanEngine()
            protocols = await engine.get_protocols()

            return [ProtocolInfoResponse(**p.to_dict()) for p in protocols]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get protocols: {str(e)}",
            )

    @router.get(
        "/best-protocol",
        response_model=Dict,
        summary="Get best protocol for loan",
        description="Find the best protocol for a flash loan based on token and amount",
    )
    async def get_best_protocol(
        token: str = Query(..., description="Token symbol (e.g., USDC, USDT)"),
        amount_usd: float = Query(..., ge=0, description="Loan amount in USD"),
    ) -> Dict:
        """Get best flash loan protocol.

        Selects the optimal protocol based on:
        1. Token support
        2. Lowest fees
        3. Sufficient liquidity

        Args:
            token: Token symbol
            amount_usd: Loan amount in USD

        Returns:
            Best protocol recommendation with fee estimate

        Example:
            GET /api/v1/ultra/flash-loans/best-protocol?token=USDC&amount_usd=100000

            Response:
            {
                "recommended_protocol": "balancer",
                "protocol_name": "Balancer",
                "fee_percentage": 0.0,
                "estimated_fees_usd": "5.00",
                "reason": "No protocol fee, only gas cost"
            }
        """
        try:
            engine = FlashLoanEngine()
            amount = Decimal(str(amount_usd))

            protocol = await engine.get_best_protocol(token, amount)

            if not protocol:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No protocol supports {token} with amount ${amount_usd}",
                )

            protocol_info = engine.get_protocol_info(protocol)
            fees = await engine.calculate_fees(protocol, amount)

            return {
                "recommended_protocol": protocol.value,
                "protocol_name": protocol_info.name,
                "fee_percentage": float(protocol_info.fee_percentage * 100),
                "estimated_fees_usd": str(fees),
                "reason": (
                    "No protocol fee, only gas cost"
                    if protocol_info.fee_percentage == 0
                    else f"{float(protocol_info.fee_percentage * 100)}% protocol fee + gas"
                ),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get best protocol: {str(e)}",
            )

    @router.post(
        "/simulate",
        response_model=FlashLoanResultResponse,
        summary="Simulate flash loan",
        description="Simulate flash loan execution without actual transaction",
    )
    async def simulate_flash_loan(
        request: FlashLoanSimulateRequest,
    ) -> FlashLoanResultResponse:
        """Simulate flash loan execution.

        Runs a simulation of the flash loan to estimate:
        - Gas costs
        - Protocol fees
        - Expected profit
        - Success/failure

        No actual blockchain transaction is executed.

        Args:
            request: Flash loan simulation request

        Returns:
            Simulation result with estimated profit and costs

        Example:
            POST /api/v1/ultra/flash-loans/simulate
            Body:
            {
                "protocol": "balancer",
                "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "amount": "100000",
                "receiver_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            }

            Response:
            {
                "status": "success",
                "gas_used": 240000,
                "gas_price_gwei": 30,
                "profit_usd": "495.00",
                "fees_paid": "5.00"
            }
        """
        try:
            engine = FlashLoanEngine()

            # Parse protocol
            try:
                protocol = FlashLoanProtocol(request.protocol)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid protocol: {request.protocol}",
                )

            # Create flash loan request
            loan_request = FlashLoanRequest(
                protocol=protocol,
                token_address=request.token_address,
                amount=Decimal(request.amount),
                receiver_address=request.receiver_address,
                callback_data=b"",  # Mock callback data
            )

            # Simulate
            result = await engine.simulate_loan(loan_request)

            return FlashLoanResultResponse(**result.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Simulation failed: {str(e)}",
            )

    @router.get(
        "/liquidity/{protocol}",
        response_model=ProtocolLiquidityResponse,
        summary="Get protocol liquidity",
        description="Get available liquidity for a protocol and token",
    )
    async def get_protocol_liquidity(
        protocol: str,
        token: str = Query(..., description="Token symbol"),
    ) -> ProtocolLiquidityResponse:
        """Get protocol liquidity.

        Returns the available liquidity for flash loans on a specific protocol.

        Args:
            protocol: Protocol identifier (aave_v3, balancer, uniswap_v3)
            token: Token symbol

        Returns:
            Available liquidity information

        Example:
            GET /api/v1/ultra/flash-loans/liquidity/balancer?token=USDC

            Response:
            {
                "protocol": "balancer",
                "token": "USDC",
                "available_liquidity_usd": "2000000",
                "max_loan_usd": "5000000"
            }
        """
        try:
            engine = FlashLoanEngine()

            # Parse protocol
            try:
                protocol_enum = FlashLoanProtocol(protocol)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid protocol: {protocol}",
                )

            liquidity = await engine.get_protocol_liquidity(protocol_enum, token)
            protocol_info = engine.get_protocol_info(protocol_enum)

            return ProtocolLiquidityResponse(
                protocol=protocol,
                token=token,
                available_liquidity_usd=str(liquidity),
                max_loan_usd=str(protocol_info.max_loan_usd),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get liquidity: {str(e)}",
            )

    @router.get(
        "/estimate-fees",
        response_model=Dict,
        summary="Estimate flash loan fees",
        description="Calculate estimated fees for a flash loan",
    )
    async def estimate_fees(
        protocol: str = Query(..., description="Protocol identifier"),
        amount_usd: float = Query(..., ge=0, description="Loan amount in USD"),
    ) -> Dict:
        """Estimate flash loan fees.

        Calculates total fees including:
        - Protocol fees
        - Gas costs
        - Total cost

        Args:
            protocol: Protocol identifier
            amount_usd: Loan amount in USD

        Returns:
            Fee breakdown

        Example:
            GET /api/v1/ultra/flash-loans/estimate-fees?protocol=aave_v3&amount_usd=100000

            Response:
            {
                "protocol": "aave_v3",
                "loan_amount_usd": "100000",
                "protocol_fee_usd": "90.00",
                "gas_cost_usd": "5.00",
                "total_fees_usd": "95.00",
                "fee_percentage": 0.095
            }
        """
        try:
            engine = FlashLoanEngine()

            # Parse protocol
            try:
                protocol_enum = FlashLoanProtocol(protocol)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid protocol: {protocol}",
                )

            amount = Decimal(str(amount_usd))
            total_fees = await engine.calculate_fees(protocol_enum, amount)
            protocol_info = engine.get_protocol_info(protocol_enum)

            protocol_fee = amount * protocol_info.fee_percentage
            gas_cost = total_fees - protocol_fee

            return {
                "protocol": protocol,
                "loan_amount_usd": str(amount),
                "protocol_fee_usd": str(protocol_fee),
                "gas_cost_usd": str(gas_cost),
                "total_fees_usd": str(total_fees),
                "fee_percentage": float((total_fees / amount) * 100),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to estimate fees: {str(e)}",
            )

    return router
