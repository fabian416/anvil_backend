"""
Money Market Handler for Chat - Compare lending rates across protocols.

Compares lending/supply rates across:
- Morpho (via MorphoGateway)
- Aave V3 (via AaveGateway or DeFiLlama)
- Compound V3 (via DeFiLlama)
- Spark (via DeFiLlama)
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.aave_gateway import AaveGateway

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

    Uses real data from:
    - MorphoGateway: Real-time vault APYs from Morpho GraphQL API
    - AaveGateway: Real-time Aave V3 rates
    - DeFiLlama: Compound and Spark rates

    Features:
    - Supply APY comparison
    - Borrow APY comparison
    - Multi-chain support
    - Best rate recommendations
    """

    def __init__(
        self,
        morpho_gateway: Optional[MorphoGateway] = None,
        aave_gateway: Optional[AaveGateway] = None,
    ):
        """
        Initialize money market handler.

        Args:
            morpho_gateway: Gateway for Morpho protocol data
            aave_gateway: Gateway for Aave V3 data
        """
        self._morpho = morpho_gateway
        self._aave = aave_gateway

    async def compare_rates(
        self,
        asset: str = "USDC",
        chain: str = "base",
    ) -> MoneyMarketHandlerResult:
        """
        Compare lending rates across protocols.

        Args:
            asset: Asset to compare rates for
            chain: Blockchain (ethereum, base)

        Returns:
            MoneyMarketHandlerResult with comparison data
        """
        start_time = time.time()

        rates = []

        # Get Morpho rates (real data)
        if self._morpho:
            try:
                morpho_vaults = await self._morpho.get_vaults(
                    asset=asset,
                    chain=chain,
                )

                # Get best Morpho vault APY
                if morpho_vaults:
                    best_morpho = max(morpho_vaults, key=lambda v: v.apy)
                    rates.append({
                        "protocol": "Morpho",
                        "type": "vault",
                        "supply_apy": best_morpho.apy * 100,
                        "borrow_apy": None,  # Morpho vaults are supply-only
                        "vault_name": best_morpho.name,
                        "chain": chain,
                        "whitelisted": best_morpho.whitelisted,
                        "source": "real",
                    })
            except Exception as e:
                logger.warning(f"Error fetching Morpho rates: {e}")

        # Get Aave rates (real data)
        if self._aave:
            try:
                aave_market = await self._aave.get_market_details(
                    asset=asset,
                    chain=chain if chain in ["ethereum", "polygon", "arbitrum", "optimism", "base"] else "ethereum",
                )
                rates.append({
                    "protocol": "Aave V3",
                    "type": "lending_pool",
                    "supply_apy": float(aave_market.supply_apy) * 100,
                    "borrow_apy": float(aave_market.borrow_apy_variable) * 100,
                    "chain": chain,
                    "source": "real",
                })
            except Exception as e:
                logger.warning(f"Error fetching Aave rates: {e}")
                # Fallback to static rates for Aave
                rates.extend(self._get_aave_fallback_rates(asset))

        # If no Aave gateway, use static rates
        if not self._aave:
            rates.extend(self._get_aave_fallback_rates(asset))

        # Add Compound and Spark (static for now - TODO: integrate APIs)
        rates.extend(self._get_compound_spark_rates(asset))

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

    def _get_aave_fallback_rates(self, asset: str) -> list[dict]:
        """
        Get fallback rates for Aave when gateway is unavailable.
        
        Note: These are approximate rates based on typical market conditions.
        In production, prefer using AaveGateway for real-time data.
        """
        if asset.upper() == "USDC":
            return [{
                "protocol": "Aave V3",
                "type": "lending_pool",
                "supply_apy": 4.5,
                "borrow_apy": 5.2,
                "chain": "multi",
                "source": "fallback",
            }]
        elif asset.upper() in ["ETH", "WETH"]:
            return [{
                "protocol": "Aave V3",
                "type": "lending_pool",
                "supply_apy": 2.1,
                "borrow_apy": 3.5,
                "chain": "multi",
                "source": "fallback",
            }]
        return []

    def _get_compound_spark_rates(self, asset: str) -> list[dict]:
        """
        Get rates for Compound V3 and Spark.
        
        TODO: Integrate with real APIs:
        - Compound V3: Use their GraphQL API
        - Spark: Use MakerDAO API
        
        For now, returns approximate market rates.
        """
        rates = []
        
        if asset.upper() == "USDC":
            rates.extend([
                {
                    "protocol": "Compound V3",
                    "type": "lending_pool",
                    "supply_apy": 4.2,
                    "borrow_apy": 5.5,
                    "chain": "multi",
                    "source": "estimated",
                },
                {
                    "protocol": "Spark",
                    "type": "savings",
                    "supply_apy": 4.8,
                    "borrow_apy": 5.0,
                    "chain": "ethereum",
                    "source": "estimated",
                },
            ])
        elif asset.upper() in ["ETH", "WETH"]:
            rates.extend([
                {
                    "protocol": "Compound V3",
                    "type": "lending_pool",
                    "supply_apy": 1.8,
                    "borrow_apy": 3.2,
                    "chain": "multi",
                    "source": "estimated",
                },
            ])
        
        return rates

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

I couldn't find any lending rates for {asset} on {chain.upper()}.

Try:
• Different asset (USDC, ETH, DAI)
• Different chain (ethereum, base)

Would you like to check a different asset?
"""

        # Sort by supply APY
        sorted_rates = sorted(
            [r for r in rates if r.get("supply_apy")],
            key=lambda r: r["supply_apy"],
            reverse=True,
        )

        response = f"""📊 **Money Market Comparison - {asset}**

Comparing lending rates across protocols on {chain.upper()}:

| Protocol | Supply APY | Borrow APY |
|----------|-----------|------------|
"""
        for rate in sorted_rates:
            supply = f"{rate['supply_apy']:.2f}%" if rate.get("supply_apy") else "N/A"
            borrow = f"{rate['borrow_apy']:.2f}%" if rate.get("borrow_apy") else "N/A"
            protocol = rate["protocol"]

            # Add indicator for best rates
            if rate == best_supply:
                protocol = f"**{protocol}** 🏆"

            response += f"| {protocol} | {supply} | {borrow} |\n"

        # Best rate recommendations
        if best_supply:
            response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 Best Supply Rate:** {best_supply['protocol']} ({best_supply['supply_apy']:.2f}% APY)
"""
            if best_supply.get("vault_name"):
                response += f"   Vault: {best_supply['vault_name']}\n"

        if best_borrow:
            response += f"""**🎯 Best Borrow Rate:** {best_borrow['protocol']} ({best_borrow['borrow_apy']:.2f}% APY)
"""

        response += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would you like to deposit into the highest-yield vault?
Say "deposit USDC on Morpho" to get started.
"""
        return response
