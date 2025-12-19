"""
Portfolio router for risk analysis and portfolio holdings endpoints.

Provides:
- GET /portfolio/me - Get authenticated user's portfolio
- GET /portfolio/{address} - Get portfolio for a specific wallet address
- GET /portfolio/risk - Get risk analysis for user's portfolio
- POST /portfolio/risk/simulate-cascade - Simulate cascade failure impact
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security, Query
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.schemas.portfolio import (
    PortfolioResponse,
    PortfolioHistoryResponse,
    PortfolioHistoryPoint,
    TokenHoldingResponse,
    PortfolioRiskResponse,
    CascadeSimulationRequest,
    CascadeSimulationResponse,
)
from app.application.portfolio import PortfolioRiskAnalysis, PortfolioService
from app.domain.entities.user_portfolio import UserPortfolio
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.ports.wallet.wallet_repository import WalletRepository


def create_portfolio_router() -> APIRouter:
    router = APIRouter(
        prefix="/user/portfolio",
        tags=["portfolio"],
    )

    # ============================================================
    # Portfolio Holdings Endpoints
    # ============================================================

    @router.get(
        "/me",
        status_code=status.HTTP_200_OK,
        response_model=PortfolioResponse,
        dependencies=[Security(bearer_scheme)],
        summary="Get authenticated user's portfolio",
        description="Calculate and return the current portfolio for the authenticated user's primary wallet.",
    )
    @inject
    async def get_my_portfolio(
        current_user: FromDishka[CurrentUserService],
        portfolio_service: FromDishka[PortfolioService],
        wallet_repository: FromDishka[WalletRepository],
        chain: Optional[str] = Query(
            None,
            description="Chain to calculate for (ethereum, base, arbitrum, polygon, optimism). Defaults to wallet's default chain.",
        ),
        save_snapshot: bool = Query(
            False,
            description="Whether to save a snapshot of the portfolio for history.",
        ),
    ) -> PortfolioResponse:
        """
        Get the current portfolio for the authenticated user.

        This endpoint:
        1. Fetches on-chain balances via RPC
        2. Resolves USD prices via DeFiLlama
        3. Returns total value, native balance, and token holdings
        """
        user = await current_user.get_current_user()

        # Get user's wallets - user.id_ is already a UserId value object
        all_wallets = await wallet_repository.get_by_user_id(user.id_)

        if not all_wallets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No wallets found for this user. Create a wallet first.",
            )

        # Helper: Check if address is a Bitcoin address
        def is_bitcoin_address(address: str) -> bool:
            if not address:
                return False
            return (
                address.startswith("bc1") or  # Mainnet SegWit
                address.startswith("tb1") or  # Testnet SegWit
                address.startswith("1") or    # Mainnet P2PKH
                address.startswith("3") or    # Mainnet P2SH
                address.startswith("m") or    # Testnet P2PKH
                address.startswith("n") or    # Testnet P2PKH
                address.startswith("2")       # Testnet P2SH
            )

        # Filter to only EVM wallets (exclude Bitcoin wallets for portfolio)
        # Portfolio tracking is for EVM tokens, not Bitcoin
        # Check BOTH by chain_type AND by address pattern (in case DB has wrong chain_type)
        evm_wallets = [
            w for w in all_wallets 
            if w.default_chain not in (ChainType.BITCOIN, ChainType.BITCOIN_TESTNET)
            and not is_bitcoin_address(w.address)
        ]

        if not evm_wallets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No EVM wallets found for this user. Portfolio requires an Ethereum/Base wallet.",
            )

        # Use the first EVM wallet (primary)
        wallet = evm_wallets[0]

        # Parse chain if provided
        # NOTE: ChainType enum values are lowercase (e.g. "ethereum", "base"),
        # so we normalize the query parameter to lowercase before parsing.
        target_chain = None
        if chain:
            try:
                target_chain = ChainType(chain.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid chain: {chain}. "
                        "Valid options: ethereum, base, arbitrum, polygon, optimism"
                    ),
                )

        # Calculate portfolio
        portfolio = await portfolio_service.get_current_portfolio(
            wallet.id_,
            target_chain,
            save_snapshot=save_snapshot,
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate portfolio",
            )

        return PortfolioResponse(
            wallet_address=portfolio.wallet_address,
            chain=portfolio.chain,
            total_usd=portfolio.total_usd,
            native_balance=portfolio.native_balance,
            native_usd_value=portfolio.native_usd_value,
            native_symbol=portfolio.native_symbol,
            tokens=[
                TokenHoldingResponse(
                    token_address=t.get("token_address"),
                    symbol=t["symbol"],
                    name=t["name"],
                    decimals=t["decimals"],
                    amount=t["amount"],
                    usd_value=t.get("usd_value"),
                    usd_price=t.get("usd_price"),
                    percentage=t.get("percentage", 0.0),
                )
                for t in portfolio.tokens
            ],
            captured_at=portfolio.captured_at,
            has_value=portfolio.has_value,
        )

    @router.get(
        "/{wallet_address}",
        status_code=status.HTTP_200_OK,
        response_model=PortfolioResponse,
        summary="Get portfolio for a wallet address",
        description="Calculate and return the current portfolio for any wallet address.",
    )
    @inject
    async def get_portfolio_by_address(
        wallet_address: str,
        portfolio_service: FromDishka[PortfolioService],
        chain: str = Query(
            "base",
            description="Chain to calculate for (ethereum, base, arbitrum, polygon, optimism)",
        ),
        save_snapshot: bool = Query(
            False,
            description="Whether to save a snapshot (only works if wallet is registered)",
        ),
    ) -> PortfolioResponse:
        """
        Get the current portfolio for any wallet address.

        This endpoint is public and doesn't require authentication.
        It fetches on-chain balances and USD prices in real-time.
        """
        # Validate address format
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid wallet address format. Must be a 42-character hex string starting with 0x",
            )

        # Parse chain
        # Normalize to lowercase to match ChainType enum values
        try:
            target_chain = ChainType(chain.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid chain: {chain}. "
                    "Valid options: ethereum, base, arbitrum, polygon, optimism"
                ),
            )

        # Calculate portfolio
        portfolio = await portfolio_service.get_portfolio_by_address(
            wallet_address,
            target_chain,
            save_snapshot=save_snapshot,
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate portfolio. Check the address and chain.",
            )

        return PortfolioResponse(
            wallet_address=portfolio.wallet_address,
            chain=portfolio.chain,
            total_usd=portfolio.total_usd,
            native_balance=portfolio.native_balance,
            native_usd_value=portfolio.native_usd_value,
            native_symbol=portfolio.native_symbol,
            tokens=[
                TokenHoldingResponse(
                    token_address=t.get("token_address"),
                    symbol=t["symbol"],
                    name=t["name"],
                    decimals=t["decimals"],
                    amount=t["amount"],
                    usd_value=t.get("usd_value"),
                    usd_price=t.get("usd_price"),
                    percentage=t.get("percentage", 0.0),
                )
                for t in portfolio.tokens
            ],
            captured_at=portfolio.captured_at,
            has_value=portfolio.has_value,
        )

    # ============================================================
    # Risk Analysis Endpoints (existing)
    # ============================================================

    @router.get(
        "/risk",
        status_code=status.HTTP_200_OK,
        response_model=PortfolioRiskResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_portfolio_risk(
        current_user: FromDishka[CurrentUserService],
        risk_analysis: FromDishka[PortfolioRiskAnalysis],
    ) -> PortfolioRiskResponse:
        """
        Get comprehensive risk analysis for user's portfolio.

        Returns:
        - Overall risk score (weighted by exposure)
        - Risk distribution by level
        - Protocols at elevated risk
        - Dependency risks
        - Systemic risk score
        - Concentration risk
        - Chain-specific risks
        - Actionable recommendations
        """
        user = await current_user.get_current_user()

        # TODO: Get actual portfolio from repository
        # For now, create mock portfolio for demonstration
        portfolio = UserPortfolio(user_id=UUID(str(user.id_.value)))

        # In production, would load from:
        # portfolio = await portfolio_repo.get_by_user_id(user.id_)

        if not portfolio.protocols:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio found. Add protocols to your portfolio first.",
            )

        # Get risk analysis
        risk_summary = await risk_analysis.get_portfolio_risk(portfolio)

        return PortfolioRiskResponse(
            user_id=str(risk_summary.user_id),
            overall_risk_score=risk_summary.overall_risk_score,
            risk_distribution=risk_summary.risk_distribution,
            protocols_at_risk=[
                {
                    "protocol_id": str(p.protocol_id),
                    "protocol_name": p.protocol_name,
                    "exposure_usd": float(p.exposure_usd),
                    "exposure_percentage": p.exposure_percentage,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "risk_trend": p.risk_trend,
                    "contributing_factors": p.contributing_factors,
                    "value_at_risk_usd": float(p.value_at_risk_usd),
                }
                for p in risk_summary.protocols_at_risk
            ],
            dependency_risks=[
                {
                    "dependency_protocol_id": str(d.dependency_protocol_id),
                    "dependency_protocol_name": d.dependency_protocol_name,
                    "dependent_protocols": d.dependent_protocols,
                    "impact_if_failure": d.impact_if_failure,
                    "total_exposure_usd": float(d.total_exposure_usd),
                    "risk_score": d.risk_score,
                }
                for d in risk_summary.dependency_risks
            ],
            systemic_risk_score=risk_summary.systemic_risk_score,
            concentration_risk=risk_summary.concentration_risk,
            chain_risk_distribution=risk_summary.chain_risk_distribution,
            recommendations=risk_summary.recommendations,
            total_value_at_risk_usd=float(risk_summary.total_value_at_risk_usd),
            last_updated=risk_summary.last_updated.isoformat(),
        )

    @router.post(
        "/risk/simulate-cascade",
        status_code=status.HTTP_200_OK,
        response_model=CascadeSimulationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def simulate_cascade(
        request: CascadeSimulationRequest,
        current_user: FromDishka[CurrentUserService],
        risk_analysis: FromDishka[PortfolioRiskAnalysis],
    ) -> CascadeSimulationResponse:
        """
        Simulate cascade failure impact on portfolio.

        Simulates what would happen if a specific protocol in the
        portfolio fails, showing direct and indirect impacts via
        network contagion.

        Args:
            origin_protocol_id: Protocol that fails

        Returns:
        - Cascade impacts (direct/indirect)
        - Worst case loss (USD and %)
        - Protocols to exit immediately
        - Protocols to reduce exposure
        - Safe protocols (unaffected)
        """
        user = await current_user.get_current_user()

        # TODO: Get actual portfolio
        portfolio = UserPortfolio(user_id=UUID(str(user.id_.value)))

        if not portfolio.protocols:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio found",
            )

        # Check if protocol is in portfolio
        origin_id = UUID(request.origin_protocol_id)
        if not portfolio.get_exposure(origin_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Protocol not in your portfolio",
            )

        # Run simulation
        cascade_result = await risk_analysis.simulate_portfolio_cascade(
            portfolio, origin_id
        )

        return CascadeSimulationResponse(
            user_id=str(cascade_result.user_id),
            cascade_impacts=[
                {
                    "origin_protocol_id": str(c.origin_protocol_id),
                    "origin_protocol_name": c.origin_protocol_name,
                    "directly_affected": c.directly_affected,
                    "indirectly_affected": c.indirectly_affected,
                    "total_exposure_at_risk_usd": float(c.total_exposure_at_risk_usd),
                    "cascade_probability": c.cascade_probability,
                    "time_to_impact": c.time_to_impact,
                }
                for c in cascade_result.cascade_impacts
            ],
            worst_case_loss_usd=float(cascade_result.worst_case_loss_usd),
            worst_case_loss_percentage=cascade_result.worst_case_loss_percentage,
            protocols_to_exit=cascade_result.protocols_to_exit,
            protocols_to_reduce=cascade_result.protocols_to_reduce,
            safe_protocols=cascade_result.safe_protocols,
        )

    return router
