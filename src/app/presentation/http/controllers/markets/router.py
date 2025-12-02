"""
Markets API router.

Endpoints for advanced market data, token prices, and protocol yields.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Security
from dishka.integrations.fastapi import FromDishka

from app.application.markets.advanced_markets_service import AdvancedMarketsService
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme


def create_markets_router() -> APIRouter:
    """Create and configure markets router."""
    router = APIRouter(prefix="/markets", tags=["markets"])

    @router.get("/overview")
    async def get_market_overview(
        authorization: str = Security(bearer_scheme),
        markets_service: AdvancedMarketsService = FromDishka(),
        chains: Optional[str] = None,
        risk_filter: Optional[str] = None,
    ):
        """
        Get comprehensive market overview.
        
        Returns:
        - Top tokens by market cap with ML risk scores
        - Trending protocols
        - Market trend analysis
        - Personalized recommendations (if authenticated)
        """
        chain_list = chains.split(",") if chains else None
        risk_list = risk_filter.split(",") if risk_filter else None
        
        # TODO: Extract user_id from authorization token
        user_id = None
        
        overview = await markets_service.get_market_overview(
            user_id=user_id,
            chains=chain_list,
            risk_filter=risk_list,
        )
        return overview

    @router.get("/yields")
    async def get_protocol_yields(
        authorization: str = Security(bearer_scheme),
        markets_service: AdvancedMarketsService = FromDishka(),
        chains: Optional[str] = None,
        categories: Optional[str] = None,
        min_apy: Optional[float] = None,
        max_risk: Optional[float] = None,
    ):
        """
        Get aggregated protocol yields across chains.
        
        Query Parameters:
        - chains: Comma-separated chain names
        - categories: Comma-separated categories (lending, staking, farming)
        - min_apy: Minimum APY threshold
        - max_risk: Maximum risk score threshold
        
        Returns list of protocol yields with risk-adjusted metrics.
        """
        chain_list = chains.split(",") if chains else None
        category_list = categories.split(",") if categories else None
        
        yields = await markets_service.get_protocol_yields(
            chains=chain_list,
            categories=category_list,
            min_apy=min_apy,
            max_risk=max_risk,
        )
        return {"yields": yields}

    @router.get("/tokens/{token_symbol}")
    async def get_token_details(
        token_symbol: str,
        authorization: str = Security(bearer_scheme),
        markets_service: AdvancedMarketsService = FromDishka(),
    ):
        """
        Get detailed market data for specific token.
        
        Path Parameters:
        - token_symbol: Token symbol (e.g., ETH, BTC, USDC)
        
        Returns detailed token data with ML risk analysis.
        """
        token_data = await markets_service.get_token_details(token_symbol.upper())
        
        if not token_data:
            return {"error": "Token not found"}, 404
        
        return token_data

    @router.get("/tokens/{token_symbol}/history")
    async def get_token_history(
        token_symbol: str,
        timeframe: str = "7d",
        authorization: str = Security(bearer_scheme),
        markets_service: AdvancedMarketsService = FromDishka(),
    ):
        """
        Get historical price data for token.
        
        Path Parameters:
        - token_symbol: Token symbol
        
        Query Parameters:
        - timeframe: Time range (1h, 24h, 7d, 30d)
        
        Returns historical price points.
        """
        history = await markets_service.get_historical_prices(
            token_symbol.upper(),
            timeframe=timeframe,
        )
        return {"history": history}

    return router
