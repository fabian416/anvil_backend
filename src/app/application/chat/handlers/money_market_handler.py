"""
Money Market Handler for Chat - Compare lending rates across protocols.

Compares lending/supply rates across:
- Aave V3 (via AaveGateway)
- Compound V3 (via CompoundGateway)

Per CEO spec: Money Market = Aave + Compound only
(Morpho is handled separately by LendingHandler for vault deposits)
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.compound_gateway import CompoundGateway

logger = logging.getLogger(__name__)


@dataclass
class MoneyMarketHandlerResult:
    """Result from money market handler."""

    content: str
    rates: list[dict]
    best_supply_protocol: str
    best_supply_apy: float
    best_borrow_protocol: str
    best_borrow_apy: float
    asset: str
    latency_ms: int
    handler: str = "money_market_handler"


class MoneyMarketHandler:
    """
    Handler for money market comparison chat intents.

    Per CEO spec: Aave + Compound only for money market comparison.
    Morpho vaults are handled separately by LendingHandler.

    Uses:
    - AaveGateway: Real-time Aave V3 rates
    - CompoundGateway: Real-time Compound V3 rates

    Features:
    - Supply APY comparison
    - Borrow APY comparison
    - Multi-chain support
    - Best rate recommendations
    """

    def __init__(
        self,
        aave_gateway: Optional[AaveGateway] = None,
        compound_gateway: Optional[CompoundGateway] = None,
    ):
        """
        Initialize money market handler.

        Args:
            aave_gateway: Gateway for Aave V3 data
            compound_gateway: Gateway for Compound V3 data
        """
        self._aave = aave_gateway
        self._compound = compound_gateway

    async def compare_rates(
        self,
        asset: str = "USDC",
        chain: str = "base",
    ) -> MoneyMarketHandlerResult:
        """
        Compare lending rates across Aave and Compound.

        Args:
            asset: Asset to compare rates for
            chain: Blockchain (ethereum, base, polygon, etc.)

        Returns:
            MoneyMarketHandlerResult with comparison data
        """
        start_time = time.time()

        rates = []

        # Get Aave V3 rates (real data)
        if self._aave:
            try:
                supported_chains = ["ethereum", "polygon", "arbitrum", "optimism", "base", "avalanche"]
                target_chain = chain if chain.lower() in supported_chains else "ethereum"
                
                aave_market = await self._aave.get_market_details(
                    asset=asset,
                    chain=target_chain,
                )
                if aave_market:
                    rates.append({
                        "protocol": "Aave V3",
                        "type": "lending_pool",
                        "supply_apy": float(aave_market.supply_apy) * 100,
                        "borrow_apy": float(aave_market.borrow_apy_variable) * 100,
                        "chain": target_chain,
                        "tvl_usd": float(aave_market.total_supplied_usd) if hasattr(aave_market, 'total_supplied_usd') else None,
                        "utilization": float(aave_market.utilization_rate) if hasattr(aave_market, 'utilization_rate') else None,
                        "source": "real",
                    })
                    logger.info(f"Fetched Aave rates for {asset} on {target_chain}")
                else:
                    rates.append(self._get_aave_fallback(asset, chain))
            except Exception as e:
                logger.warning(f"Error fetching Aave rates: {e}")
                rates.append(self._get_aave_fallback(asset, chain))
        else:
            rates.append(self._get_aave_fallback(asset, chain))

        # Get Compound V3 rates (real data)
        if self._compound:
            try:
                compound_market = await self._compound.get_market_details(
                    asset=asset,
                    chain=chain,
                )
                if compound_market:
                    rates.append({
                        "protocol": "Compound V3",
                        "type": "lending_pool",
                        "supply_apy": compound_market.supply_apy,
                        "borrow_apy": compound_market.borrow_apy,
                        "chain": compound_market.chain,
                        "tvl_usd": compound_market.total_supply_usd,
                        "utilization": compound_market.utilization,
                        "source": "real",
                    })
                    logger.info(f"Fetched Compound rates for {asset} on {chain}")
                else:
                    # Asset not supported on this chain
                    fallback = self._get_compound_fallback(asset, chain)
                    if fallback:
                        rates.append(fallback)
            except Exception as e:
                logger.warning(f"Error fetching Compound rates: {e}")
                fallback = self._get_compound_fallback(asset, chain)
                if fallback:
                    rates.append(fallback)
        else:
            # No Compound gateway - use fallback
            fallback = self._get_compound_fallback(asset, chain)
            if fallback:
                rates.append(fallback)

        # Find best rates
        supply_rates = [r for r in rates if r.get("supply_apy")]
        borrow_rates = [r for r in rates if r.get("borrow_apy")]

        best_supply = max(supply_rates, key=lambda r: r["supply_apy"]) if supply_rates else None
        best_borrow = min(borrow_rates, key=lambda r: r["borrow_apy"]) if borrow_rates else None

        # Format response
        content = self._format_comparison_response(
            rates=rates,
            best_supply=best_supply,
            best_borrow=best_borrow,
            asset=asset,
            chain=chain,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return MoneyMarketHandlerResult(
            content=content,
            rates=rates,
            best_supply_protocol=best_supply["protocol"] if best_supply else "N/A",
            best_supply_apy=best_supply["supply_apy"] if best_supply else 0.0,
            best_borrow_protocol=best_borrow["protocol"] if best_borrow else "N/A",
            best_borrow_apy=best_borrow["borrow_apy"] if best_borrow else 0.0,
            asset=asset,
            latency_ms=latency_ms,
        )

    def _get_aave_fallback(self, asset: str, chain: str) -> dict:
        """Get fallback Aave rates when gateway unavailable."""
        rates_map = {
            "USDC": {"supply": 4.5, "borrow": 5.2},
            "USDT": {"supply": 4.3, "borrow": 5.0},
            "DAI": {"supply": 4.8, "borrow": 5.5},
            "ETH": {"supply": 2.1, "borrow": 3.5},
            "WETH": {"supply": 2.1, "borrow": 3.5},
            "WBTC": {"supply": 0.5, "borrow": 2.0},
        }
        
        asset_rates = rates_map.get(asset.upper(), {"supply": 3.0, "borrow": 4.0})
        
        return {
            "protocol": "Aave V3",
            "type": "lending_pool",
            "supply_apy": asset_rates["supply"],
            "borrow_apy": asset_rates["borrow"],
            "chain": chain,
            "source": "estimated",
        }

    def _get_compound_fallback(self, asset: str, chain: str) -> Optional[dict]:
        """
        Get fallback Compound V3 rates when gateway unavailable.
        
        Compound V3 (Comet) is available on:
        - Ethereum: USDC, WETH markets
        - Base: USDC, WETH markets
        - Arbitrum: USDC, WETH markets
        - Polygon: USDC markets
        """
        # Compound V3 only supports certain assets
        supported_assets = ["USDC", "WETH", "ETH"]
        if asset.upper() not in supported_assets:
            return None
            
        rates_map = {
            "USDC": {"supply": 4.2, "borrow": 5.5},
            "WETH": {"supply": 1.8, "borrow": 3.2},
            "ETH": {"supply": 1.8, "borrow": 3.2},
        }
        
        asset_rates = rates_map.get(asset.upper(), {"supply": 3.0, "borrow": 4.0})
        
        return {
            "protocol": "Compound V3",
            "type": "lending_pool",
            "supply_apy": asset_rates["supply"],
            "borrow_apy": asset_rates["borrow"],
            "chain": chain,
            "source": "estimated",
        }

    def _format_comparison_response(
        self,
        rates: list[dict],
        best_supply: Optional[dict],
        best_borrow: Optional[dict],
        asset: str,
        chain: str,
    ) -> str:
        """Format comparison data as chat response."""
        if not rates:
            return f"""📊 **No Rates Found for {asset}**

I couldn't find lending rates for {asset} on {chain.upper()}.

Try:
• Different asset (USDC, ETH, DAI)
• Different chain (ethereum, base, arbitrum)
"""

        # Sort by supply APY
        sorted_rates = sorted(
            [r for r in rates if r.get("supply_apy")],
            key=lambda r: r["supply_apy"],
            reverse=True,
        )

        response = f"""📊 **Money Market Comparison - {asset}**

Comparing Aave & Compound rates on {chain.upper()}:

| Protocol | Supply APY | Borrow APY | Source |
|----------|-----------|------------|--------|
"""
        for rate in sorted_rates:
            supply = f"{rate['supply_apy']:.2f}%"
            borrow = f"{rate['borrow_apy']:.2f}%" if rate.get("borrow_apy") else "N/A"
            protocol = rate["protocol"]
            source = "🟢" if rate.get("source") == "real" else "🟡"

            # Mark best supply rate
            if rate == best_supply:
                protocol = f"**{protocol}** 🏆"

            response += f"| {protocol} | {supply} | {borrow} | {source} |\n"

        # Legend
        response += "\n*🟢 Real-time | 🟡 Estimated*\n"

        # Best rate recommendations
        if best_supply:
            response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 Best Supply Rate:** {best_supply['protocol']} ({best_supply['supply_apy']:.2f}% APY)
"""

        if best_borrow:
            response += f"""**🎯 Best Borrow Rate:** {best_borrow['protocol']} ({best_borrow['borrow_apy']:.2f}% APY)
"""

        response += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *For higher yields on stablecoins, try: "deposit USDC on Morpho"*
"""
        return response
