"""
Money Market Handler for Chat - Compare lending rates across protocols.

Compares lending/supply rates across:
- Morpho (via MorphoGateway)
- Aave V3 (future integration)
- Compound V3 (future integration)
- Spark (future integration)
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.morpho_gateway import MorphoGateway


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

    Uses MorphoGateway and other protocol adapters to compare
    lending/supply rates across DeFi protocols.

    Features:
    - Supply APY comparison
    - Borrow APY comparison (future)
    - Multi-chain support
    - Best rate recommendations
    """

    def __init__(
        self,
        morpho_gateway: Optional[MorphoGateway] = None,
        # Future: aave_gateway, compound_gateway, spark_gateway
    ):
        """
        Initialize money market handler.

        Args:
            morpho_gateway: Gateway for Morpho protocol data
        """
        self._morpho = morpho_gateway

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

        # Get Morpho rates
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
                    })
            except Exception:
                pass  # Morpho not available

        # Add static rates for other protocols (TODO: integrate real APIs)
        # These are placeholder rates - in production, fetch from real APIs
        static_rates = self._get_static_protocol_rates(asset)
        rates.extend(static_rates)

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

    def _get_static_protocol_rates(self, asset: str) -> list[dict]:
        """
        Get static rates for protocols not yet integrated.

        TODO: Replace with real API integrations for Aave, Compound, Spark.
        """
        # These are approximate rates - should be fetched from real APIs
        if asset.upper() == "USDC":
            return [
                {
                    "protocol": "Aave V3",
                    "type": "lending_pool",
                    "supply_apy": 4.5,
                    "borrow_apy": 5.2,
                    "chain": "multi",
                    "note": "Static rate - integrate Aave API",
                },
                {
                    "protocol": "Compound V3",
                    "type": "lending_pool",
                    "supply_apy": 4.2,
                    "borrow_apy": 5.5,
                    "chain": "multi",
                    "note": "Static rate - integrate Compound API",
                },
                {
                    "protocol": "Spark",
                    "type": "savings",
                    "supply_apy": 4.8,
                    "borrow_apy": 5.0,
                    "chain": "ethereum",
                    "note": "Static rate - integrate Spark API",
                },
            ]
        elif asset.upper() == "ETH":
            return [
                {
                    "protocol": "Aave V3",
                    "type": "lending_pool",
                    "supply_apy": 2.1,
                    "borrow_apy": 3.5,
                    "chain": "multi",
                    "note": "Static rate",
                },
                {
                    "protocol": "Compound V3",
                    "type": "lending_pool",
                    "supply_apy": 1.8,
                    "borrow_apy": 3.2,
                    "chain": "multi",
                    "note": "Static rate",
                },
            ]
        else:
            return []

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
