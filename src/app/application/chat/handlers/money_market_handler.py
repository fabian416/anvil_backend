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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID, uuid4

from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.compound_gateway import CompoundGateway
from app.domain.ports.money_market.money_market_cache_gateway import (
    MoneyMarketCacheGateway,
)
from app.domain.ports.money_market.money_market_comparison_gateway import (
    MoneyMarketComparisonGateway,
)
from app.domain.entities.money_market.protocol_data import (
    MoneyMarketProtocolData,
)
from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)

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
    language: str = "en"
    handler: str = "money_market_handler"
    pending_action: str | None = None  # For multi-turn flows


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
        cache_gateway: Optional[MoneyMarketCacheGateway] = None,
        comparison_gateway: Optional[MoneyMarketComparisonGateway] = None,
    ):
        """
        Initialize money market handler with caching support.

        Args:
            aave_gateway: Gateway for Aave V3 data
            compound_gateway: Gateway for Compound V3 data
            cache_gateway: Gateway for 60s TTL rate caching (NEW)
            comparison_gateway: Gateway for comparison analytics (NEW)
        """
        self._aave = aave_gateway
        self._compound = compound_gateway
        self._cache = cache_gateway
        self._comparison = comparison_gateway
        self._cache_hits = 0
        self._cache_misses = 0

    async def compare_rates(
        self,
        asset: str = "USDC",
        chain: str = "base",
        language: str = "en",
        user_id: Optional[UUID] = None,
    ) -> MoneyMarketHandlerResult:
        """
        Compare lending rates across Aave and Compound with caching.

        Args:
            asset: Asset to compare rates for
            chain: Blockchain (ethereum, base, polygon, etc.)
            language: Response language
            user_id: User ID for comparison logging (optional)

        Returns:
            MoneyMarketHandlerResult with comparison data
        """
        start_time = time.time()

        rates = []
        self._cache_hits = 0
        self._cache_misses = 0

        # Get Aave V3 rates (with caching)
        aave_rate = await self._get_protocol_rate(
            protocol="aave_v3",
            asset=asset,
            chain=chain,
            fetch_func=self._fetch_aave_rate,
        )
        if aave_rate:
            rates.append(aave_rate)

        # Get Compound V3 rates (with caching)
        compound_rate = await self._get_protocol_rate(
            protocol="compound_v3",
            asset=asset,
            chain=chain,
            fetch_func=self._fetch_compound_rate,
        )
        if compound_rate:
            rates.append(compound_rate)

        # Find best rates
        supply_rates = [r for r in rates if r.get("supply_apy")]
        borrow_rates = [r for r in rates if r.get("borrow_apy")]

        best_supply = (
            max(supply_rates, key=lambda r: r["supply_apy"]) if supply_rates else None
        )
        best_borrow = (
            min(borrow_rates, key=lambda r: r["borrow_apy"]) if borrow_rates else None
        )

        # Format response with i18n
        content = self._format_comparison_response(
            rates=rates,
            best_supply=best_supply,
            best_borrow=best_borrow,
            asset=asset,
            chain=chain,
            language=language,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Set pending_action if no rates found
        pending_action = None
        if not rates:
            pending_action = "money_market_no_rates"

        # Log comparison for analytics (if gateway available)
        if self._comparison and user_id:
            try:
                await self._log_comparison(
                    user_id=user_id,
                    asset=asset,
                    chain=chain,
                    rates=rates,
                    best_supply=best_supply,
                    best_borrow=best_borrow,
                    latency_ms=latency_ms,
                    language=language,
                )
            except Exception as e:
                logger.warning(f"Failed to log comparison: {e}")

        # Log cache performance
        logger.info(
            f"Money market comparison complete: "
            f"cache_hits={self._cache_hits}, cache_misses={self._cache_misses}, "
            f"latency={latency_ms}ms"
        )

        return MoneyMarketHandlerResult(
            content=content,
            rates=rates,
            best_supply_protocol=best_supply["protocol"] if best_supply else "N/A",
            best_supply_apy=best_supply["supply_apy"] if best_supply else 0.0,
            best_borrow_protocol=best_borrow["protocol"] if best_borrow else "N/A",
            best_borrow_apy=best_borrow["borrow_apy"] if best_borrow else 0.0,
            asset=asset,
            latency_ms=latency_ms,
            language=language,
            pending_action=pending_action,
        )

    async def _get_protocol_rate(
        self,
        protocol: str,
        asset: str,
        chain: str,
        fetch_func,
    ) -> Optional[dict]:
        """
        Get protocol rate with 60s caching.

        Cache-first strategy:
        1. Check cache (60s TTL)
        2. On miss, fetch from protocol
        3. Store in cache with 60s TTL

        Args:
            protocol: Protocol ID ('aave_v3', 'compound_v3')
            asset: Asset symbol
            chain: Blockchain network
            fetch_func: Async function to fetch data on cache miss

        Returns:
            Rate dict or None if unavailable
        """
        # 1. Try cache first (if gateway available)
        if self._cache:
            try:
                cached_data = await self._cache.get_cached_rate(
                    protocol=protocol,
                    asset=asset,
                    chain=chain,
                )

                if cached_data:
                    self._cache_hits += 1
                    logger.info(
                        f"Cache HIT for {protocol}/{asset}/{chain} "
                        f"(expires in {cached_data.seconds_until_expiry}s)"
                    )
                    return self._protocol_data_to_dict(cached_data)
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}, falling back to fetch")

        # 2. Cache miss - fetch from protocol
        self._cache_misses += 1
        logger.info(f"Cache MISS for {protocol}/{asset}/{chain}, fetching...")

        rate_data = await fetch_func(asset, chain)
        if not rate_data:
            return None

        # 3. Store in cache (if gateway available)
        if self._cache:
            try:
                await self._cache_rate(
                    protocol=protocol,
                    asset=asset,
                    chain=chain,
                    rate_data=rate_data,
                )
                logger.info(f"Cached {protocol}/{asset}/{chain} (TTL: 60s)")
            except Exception as e:
                logger.warning(f"Failed to cache rate: {e}")

        return rate_data

    async def _cache_rate(
        self,
        protocol: str,
        asset: str,
        chain: str,
        rate_data: dict,
    ) -> None:
        """Store protocol rate in cache with 60s TTL."""
        now = datetime.now(timezone.utc)

        protocol_data = MoneyMarketProtocolData(
            id=uuid4(),
            protocol_id=protocol,
            asset=asset,
            chain=chain,
            supply_apy=Decimal(str(rate_data.get("supply_apy", 0))),
            borrow_apy_variable=Decimal(str(rate_data.get("borrow_apy", 0))),
            borrow_apy_stable=None,  # Not all protocols support stable rates
            total_supplied_usd=Decimal(str(rate_data.get("tvl_usd", 0))),
            total_borrowed_usd=Decimal("0"),  # Not available in rate_data
            utilization_rate=Decimal(str(rate_data.get("utilization", 0))),
            liquidity_available=Decimal("0"),  # Not available in rate_data
            data_source=rate_data.get("source", "api"),
            valid_until=now + timedelta(seconds=60),  # 60s TTL
            created_at=now,
        )

        await self._cache.cache_rate(protocol_data)

    def _protocol_data_to_dict(self, data: MoneyMarketProtocolData) -> dict:
        """Convert domain entity to handler dict format."""
        return {
            "protocol": "Aave V3" if data.protocol_id == "aave_v3" else "Compound V3",
            "type": "lending_pool",
            "supply_apy": float(data.supply_apy),
            "borrow_apy": float(data.borrow_apy_variable),
            "chain": data.chain,
            "tvl_usd": float(data.total_supplied_usd),
            "utilization": float(data.utilization_rate),
            "source": data.data_source,
            "is_cached": True,
        }

    async def _fetch_aave_rate(self, asset: str, chain: str) -> Optional[dict]:
        """Fetch Aave rate from gateway."""
        if not self._aave:
            return self._get_aave_fallback(asset, chain)

        try:
            supported_chains = [
                "ethereum",
                "polygon",
                "arbitrum",
                "optimism",
                "base",
                "avalanche",
            ]
            target_chain = chain if chain.lower() in supported_chains else "ethereum"

            aave_market = await self._aave.get_market_details(
                asset=asset,
                chain=target_chain,
            )
            if aave_market:
                return {
                    "protocol": "Aave V3",
                    "type": "lending_pool",
                    "supply_apy": float(aave_market.supply_apy) * 100,
                    "borrow_apy": float(aave_market.borrow_apy_variable) * 100,
                    "chain": target_chain,
                    "tvl_usd": float(aave_market.total_supplied_usd)
                    if hasattr(aave_market, "total_supplied_usd")
                    else None,
                    "utilization": float(aave_market.utilization_rate)
                    if hasattr(aave_market, "utilization_rate")
                    else None,
                    "source": "on_chain",
                }
            return self._get_aave_fallback(asset, chain)
        except Exception as e:
            logger.warning(f"Error fetching Aave rates: {e}")
            return self._get_aave_fallback(asset, chain)

    async def _fetch_compound_rate(self, asset: str, chain: str) -> Optional[dict]:
        """Fetch Compound rate from gateway."""
        if not self._compound:
            return self._get_compound_fallback(asset, chain)

        try:
            compound_market = await self._compound.get_market_details(
                asset=asset,
                chain=chain,
            )
            if compound_market:
                return {
                    "protocol": "Compound V3",
                    "type": "lending_pool",
                    "supply_apy": compound_market.supply_apy,
                    "borrow_apy": compound_market.borrow_apy,
                    "chain": compound_market.chain,
                    "tvl_usd": compound_market.total_supply_usd,
                    "utilization": compound_market.utilization,
                    "source": "on_chain",
                }
            return self._get_compound_fallback(asset, chain)
        except Exception as e:
            logger.warning(f"Error fetching Compound rates: {e}")
            return self._get_compound_fallback(asset, chain)

    async def _log_comparison(
        self,
        user_id: UUID,
        asset: str,
        chain: str,
        rates: list[dict],
        best_supply: Optional[dict],
        best_borrow: Optional[dict],
        latency_ms: int,
        language: str,
    ) -> None:
        """Log comparison for analytics."""
        comparison = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=user_id,
            guest_session_id=None,
            asset=asset,
            chain=chain,
            protocols_compared=rates,
            best_supply_protocol=best_supply["protocol"] if best_supply else "N/A",
            best_supply_apy=str(best_supply["supply_apy"]) if best_supply else "0",
            best_borrow_protocol=best_borrow["protocol"] if best_borrow else "N/A",
            best_borrow_apy=str(best_borrow["borrow_apy"]) if best_borrow else "0",
            latency_ms=latency_ms,
            language=language,
            created_at=datetime.now(timezone.utc),
        )

        await self._comparison.log_comparison(comparison)
        logger.info(f"Logged comparison for user {user_id}: {asset}/{chain}")

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
        language: str = "en",
    ) -> str:
        """Format comparison data as chat response with i18n support."""
        from app.application.chat.i18n import t

        if not rates:
            # Localized "no rates found" message with improved formatting
            no_rates_msgs = {
                "en": {
                    "title": f"Money Market Rates - {asset}",
                    "message": f"I couldn't find lending rates for {asset} on {chain.upper()}.",
                    "header": "What would you like to try?",
                    "options": [
                        ("💎", "Try a different asset", "USDC, USDT, DAI, ETH, WETH"),
                        (
                            "🌐",
                            "Try a different chain",
                            "Ethereum, Base, Arbitrum, Polygon",
                        ),
                        ("💡", "Check back later", "Rates may be available soon"),
                    ],
                },
                "es": {
                    "title": f"Tasas de Mercado Monetario - {asset}",
                    "message": f"No pude encontrar tasas de préstamo para {asset} en {chain.upper()}.",
                    "header": "¿Qué te gustaría intentar?",
                    "options": [
                        ("💎", "Probar otro activo", "USDC, USDT, DAI, ETH, WETH"),
                        (
                            "🌐",
                            "Probar otra cadena",
                            "Ethereum, Base, Arbitrum, Polygon",
                        ),
                        (
                            "💡",
                            "Verificar más tarde",
                            "Las tasas pueden estar disponibles pronto",
                        ),
                    ],
                },
                "pt": {
                    "title": f"Taxas de Mercado Monetário - {asset}",
                    "message": f"Não consegui encontrar taxas de empréstimo para {asset} em {chain.upper()}.",
                    "header": "O que você gostaria de tentar?",
                    "options": [
                        ("💎", "Tentar outro ativo", "USDC, USDT, DAI, ETH, WETH"),
                        (
                            "🌐",
                            "Tentar outra rede",
                            "Ethereum, Base, Arbitrum, Polygon",
                        ),
                        (
                            "💡",
                            "Verificar mais tarde",
                            "As taxas podem estar disponíveis em breve",
                        ),
                    ],
                },
                "zh": {
                    "title": f"货币市场利率 - {asset}",
                    "message": f"在 {chain.upper()} 上找不到 {asset} 的借贷利率。",
                    "header": "您想尝试什么？",
                    "options": [
                        ("💎", "尝试其他资产", "USDC, USDT, DAI, ETH, WETH"),
                        ("🌐", "尝试其他链", "Ethereum, Base, Arbitrum, Polygon"),
                        ("💡", "稍后查看", "利率可能很快可用"),
                    ],
                },
            }

            msgs = no_rates_msgs.get(language, no_rates_msgs["en"])
            options_text = "\n".join([
                f"**{i}.** {emoji} **{title}**\n   {details}"
                for i, (emoji, title, details) in enumerate(msgs["options"], 1)
            ])

            return f"""📊 **{msgs["title"]}**

{msgs["message"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""

        # Sort by supply APY
        sorted_rates = sorted(
            [r for r in rates if r.get("supply_apy")],
            key=lambda r: r["supply_apy"],
            reverse=True,
        )

        # Localized header with improved formatting
        response = f"""📊 **{t("money_market", "title", language, asset=asset)}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{t("money_market", "comparing", language, chain=chain.upper())}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| {t("money_market", "protocol", language)} | {t("money_market", "supply_apy", language)} | {t("money_market", "borrow_apy", language)} | |
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
        real_time = t("money_market", "real_time", language)
        estimated = t("money_market", "estimated", language)
        response += f"\n*🟢 {real_time} | 🟡 {estimated}*\n"

        # Best rate recommendations
        if best_supply:
            best_supply_label = t("money_market", "best_supply", language)
            response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 {best_supply_label}:** {best_supply["protocol"]} ({best_supply["supply_apy"]:.2f}% APY)
"""

        if best_borrow:
            best_borrow_label = t("money_market", "best_borrow", language)
            response += f"""**🎯 {best_borrow_label}:** {best_borrow["protocol"]} ({best_borrow["borrow_apy"]:.2f}% APY)
"""

        response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *{t("money_market", "tip_morpho", language)}*
"""
        return response

    async def handle(
        self,
        content: str,
        user_id: Optional[str] = None,
        wallet_address: Optional[str] = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Handle money market comparison request from chat.

        Parses messages like:
        - "compare Aave vs Compound"
        - "money market rates for USDC"
        - "best borrow rates"

        Args:
            content: User message content
            user_id: User ID (optional, for guest mode)
            wallet_address: Wallet address (optional, for guest mode)
            language: Response language (en, es, pt, zh)

        Returns:
            dict with 'content', 'enrichment', and 'requires_registration' fields
        """
        # Extract asset and chain from message
        asset, chain = self._extract_params_from_message(content)

        # Convert user_id to UUID if provided
        user_uuid = None
        if user_id:
            try:
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            except (ValueError, TypeError):
                logger.warning(f"Invalid user_id format: {user_id}")

        # Compare rates with caching and logging
        result = await self.compare_rates(
            asset=asset,
            chain=chain,
            language=language,
            user_id=user_uuid,
        )

        return {
            "content": result.content,
            "enrichment": {
                "asset": result.asset,
                "chain": chain,
                "rates": result.rates,
                "best_supply_protocol": result.best_supply_protocol,
                "best_supply_apy": result.best_supply_apy,
                "best_borrow_protocol": result.best_borrow_protocol,
                "best_borrow_apy": result.best_borrow_apy,
                "latency_ms": result.latency_ms,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "handler": "money_market_handler",
            },
            "requires_registration": False,  # View-only, no registration needed
        }

    def _extract_params_from_message(self, message: str) -> tuple[str, str]:
        """
        Extract asset and chain from user message.

        Examples:
        - "compare Aave vs Compound" -> ("USDC", "ethereum")
        - "money market rates for USDC" -> ("USDC", "ethereum")
        - "compare Aave vs Compound on Base" -> ("USDC", "base")
        - "best borrow rates for ETH" -> ("ETH", "ethereum")

        Returns:
            Tuple of (asset, chain)
        """
        message_lower = message.lower()

        # Detect chain
        if "base" in message_lower:
            chain = "base"
        elif "arbitrum" in message_lower or "arb" in message_lower:
            chain = "arbitrum"
        elif "polygon" in message_lower or "matic" in message_lower:
            chain = "polygon"
        elif "optimism" in message_lower or "op" in message_lower:
            chain = "optimism"
        elif "avalanche" in message_lower or "avax" in message_lower:
            chain = "avalanche"
        elif "ethereum" in message_lower or "mainnet" in message_lower:
            chain = "ethereum"
        else:
            chain = "ethereum"  # Default to Ethereum

        # Detect asset
        asset_patterns = {
            "USDC": ["usdc"],
            "USDT": ["usdt", "tether"],
            "DAI": ["dai"],
            "ETH": ["eth", "ethereum", "ether"],
            "WETH": ["weth", "wrapped eth", "wrapped ether"],
            "WBTC": ["wbtc", "wrapped btc", "wrapped bitcoin"],
        }

        for asset_symbol, patterns in asset_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return asset_symbol, chain

        # Default to USDC if no asset detected
        return "USDC", chain
