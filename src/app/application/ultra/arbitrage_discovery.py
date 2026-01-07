"""Arbitrage Discovery Engine for ULTRA Arbitrage Bot.

Implements multi-hop arbitrage opportunity discovery:
- 2-hop arbitrage (cross-DEX price differences)
- 3-hop arbitrage (multi-token paths)
- Triangle arbitrage (circular paths on same DEX)

Based on ULTRA Arbitrage Bot's discovery module.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.domain.common.datetime_utils import utc_now


class ArbitrageType(str, Enum):
    """Arbitrage opportunity types."""

    TWO_HOP = "2hop"
    THREE_HOP = "3hop"
    TRIANGLE = "triangle"
    CROSS_DEX = "cross_dex"


class DEX(str, Enum):
    """Supported DEX platforms."""

    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"


@dataclass
class TradingPair:
    """Trading pair on a DEX."""

    dex: DEX
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    price: Decimal
    liquidity: Decimal
    fee_percentage: Decimal = Decimal("0.003")  # 0.3% default

    def __post_init__(self):
        """Calculate price if not provided."""
        if self.price == 0 and self.amount_in > 0:
            self.price = self.amount_out / self.amount_in

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "dex": self.dex.value,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount_in": str(self.amount_in),
            "amount_out": str(self.amount_out),
            "price": str(self.price),
            "liquidity": str(self.liquidity),
            "fee_percentage": float(self.fee_percentage * 100),
        }


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity details."""

    opportunity_id: str
    type: ArbitrageType
    path: list[TradingPair]
    expected_profit_usd: Decimal
    profit_percentage: Decimal
    required_capital: Decimal
    estimated_gas_cost: Decimal
    slippage_tolerance: Decimal
    confidence_score: float
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "opportunity_id": self.opportunity_id,
            "type": self.type.value,
            "path": [p.to_dict() for p in self.path],
            "expected_profit_usd": str(self.expected_profit_usd),
            "profit_percentage": float(self.profit_percentage * 100),
            "required_capital": str(self.required_capital),
            "estimated_gas_cost": str(self.estimated_gas_cost),
            "slippage_tolerance": float(self.slippage_tolerance * 100),
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ArbitrageConfig:
    """Configuration for arbitrage discovery."""

    # Profitability thresholds
    min_profit_usd: Decimal = Decimal("50.0")  # Min $50 profit
    min_profit_percentage: Decimal = Decimal("0.005")  # Min 0.5%
    min_confidence_score: float = 0.7  # Min 70% confidence

    # Risk parameters
    max_capital_per_trade: Decimal = Decimal("100000")  # Max $100K
    max_slippage: Decimal = Decimal("0.01")  # Max 1%
    max_gas_price_gwei: int = 100  # Max 100 gwei

    # Discovery settings
    enabled_dexes: list[DEX] = field(
        default_factory=lambda: [
            DEX.UNISWAP_V2,
            DEX.UNISWAP_V3,
            DEX.SUSHISWAP,
            DEX.CURVE,
            DEX.BALANCER,
        ]
    )
    enabled_tokens: list[str] = field(
        default_factory=lambda: ["WETH", "USDC", "USDT", "DAI", "WBTC"]
    )

    # Performance
    max_concurrent_checks: int = 10  # Max parallel checks
    cache_ttl_seconds: int = 5  # Price cache TTL


@dataclass
class PriceQuote:
    """Price quote from a DEX."""

    dex: DEX
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    price: Decimal
    liquidity: Decimal
    timestamp: datetime


class ArbitrageDiscovery:
    """Arbitrage opportunity discovery engine.

    Discovers arbitrage opportunities across multiple DEXes:
    - 2-hop: Buy low on DEX1, sell high on DEX2
    - 3-hop: Multi-token circular path
    - Triangle: Circular path on same DEX
    """

    def __init__(self, config: ArbitrageConfig = None):
        """Initialize arbitrage discovery.

        Args:
            config: Discovery configuration
        """
        self.config = config or ArbitrageConfig()
        self._opportunity_counter = 0
        self._price_cache: dict[str, PriceQuote] = {}

    def _generate_opportunity_id(self) -> str:
        """Generate unique opportunity ID."""
        self._opportunity_counter += 1
        timestamp = int(utc_now().timestamp())
        return f"ARB-{timestamp}-{self._opportunity_counter:04d}"

    async def _get_price_quote(
        self, dex: DEX, token_in: str, token_out: str, amount: Decimal
    ) -> PriceQuote:
        """Get price quote from DEX.

        Args:
            dex: DEX platform
            token_in: Input token
            token_out: Output token
            amount: Input amount

        Returns:
            Price quote
        """
        # In production, would query actual DEX
        # For now, return mock data with realistic variations

        cache_key = f"{dex.value}:{token_in}:{token_out}:{amount}"

        # Check cache
        if cache_key in self._price_cache:
            cached = self._price_cache[cache_key]
            age = (utc_now() - cached.timestamp).total_seconds()
            if age < self.config.cache_ttl_seconds:
                return cached

        # Mock price data (would be real DEX query in production)
        base_prices = {
            ("WETH", "USDC"): Decimal("2000"),
            ("USDC", "WETH"): Decimal("0.0005"),
            ("WETH", "DAI"): Decimal("2005"),
            ("DAI", "WETH"): Decimal("0.000499"),
            ("USDC", "DAI"): Decimal("1.001"),
            ("DAI", "USDC"): Decimal("0.999"),
            ("WETH", "USDT"): Decimal("1998"),
            ("USDT", "WETH"): Decimal("0.0005005"),
        }

        # DEX-specific price variations (increased for demo opportunities)
        # In production, these would come from real DEX price feeds
        # Larger variations to ensure demo opportunities are found
        dex_variations = {
            DEX.UNISWAP_V2: Decimal("1.0"),
            DEX.UNISWAP_V3: Decimal("0.992"),  # 0.8% better for arbitrage
            DEX.SUSHISWAP: Decimal("1.008"),  # 0.8% worse - creates opportunity
            DEX.CURVE: Decimal("0.994"),  # Best for stables - 0.6% better
            DEX.BALANCER: Decimal("1.006"),  # 0.6% worse - creates opportunity
        }

        base_price = base_prices.get((token_in, token_out), Decimal("1.0"))
        dex_variation = dex_variations.get(dex, Decimal("1.0"))
        price = base_price * dex_variation

        amount_out = amount * price

        # Mock liquidity (would be real in production)
        liquidity = Decimal("1000000")  # $1M liquidity

        quote = PriceQuote(
            dex=dex,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount,
            amount_out=amount_out,
            price=price,
            liquidity=liquidity,
            timestamp=utc_now(),
        )

        # Cache quote
        self._price_cache[cache_key] = quote

        return quote

    async def _calculate_profit(
        self, path: list[TradingPair], initial_capital: Decimal
    ) -> tuple[Decimal, Decimal]:
        """Calculate profit for arbitrage path.

        Args:
            path: Trading path
            initial_capital: Initial capital

        Returns:
            (profit_usd, profit_percentage)
        """
        current_amount = initial_capital

        # Execute path
        for pair in path:
            # Apply fees
            fee = current_amount * pair.fee_percentage
            amount_after_fee = current_amount - fee

            # Calculate output
            current_amount = amount_after_fee * pair.price

        # Calculate profit
        profit_usd = current_amount - initial_capital
        profit_percentage = profit_usd / initial_capital

        return profit_usd, profit_percentage

    async def _estimate_gas_cost(self, num_trades: int) -> Decimal:
        """Estimate gas cost for trades.

        Args:
            num_trades: Number of trades

        Returns:
            Estimated gas cost in USD
        """
        # Simplified gas estimation
        gas_per_trade = 150000  # Gas units
        gas_price_gwei = 30  # Assume 30 gwei
        gas_cost_eth = Decimal(gas_per_trade * num_trades * gas_price_gwei) / Decimal(
            1e9
        )
        gas_cost_usd = gas_cost_eth * Decimal("2000")  # Assume $2000 ETH

        return gas_cost_usd

    async def discover_2hop_arbitrage(
        self, capital: Decimal = Decimal("10000")
    ) -> list[ArbitrageOpportunity]:
        """Discover 2-hop arbitrage opportunities.

        2-hop: Token A → Token B → Token A (different DEXes)
        Example: Buy WETH on Uniswap, sell on Sushiswap

        Args:
            capital: Starting capital

        Returns:
            List of opportunities

        Example:
            >>> discovery = ArbitrageDiscovery()
            >>> opportunities = await discovery.discover_2hop_arbitrage(Decimal("10000"))
            >>> for opp in opportunities:
            ...     print(f"{opp.type}: ${opp.expected_profit_usd}")
        """
        opportunities = []

        # Check each token pair across DEX pairs
        for token_a in self.config.enabled_tokens[:3]:  # Limit for performance
            for token_b in self.config.enabled_tokens[:3]:
                if token_a == token_b:
                    continue

                # Check each DEX pair
                for dex1 in self.config.enabled_dexes[:3]:
                    for dex2 in self.config.enabled_dexes[:3]:
                        if dex1 == dex2:
                            continue

                        # Get quotes
                        quote1 = await self._get_price_quote(
                            dex1, token_a, token_b, capital
                        )
                        quote2 = await self._get_price_quote(
                            dex2, token_b, token_a, quote1.amount_out
                        )

                        # Build path
                        path = [
                            TradingPair(
                                dex=dex1,
                                token_in=token_a,
                                token_out=token_b,
                                amount_in=capital,
                                amount_out=quote1.amount_out,
                                price=quote1.price,
                                liquidity=quote1.liquidity,
                            ),
                            TradingPair(
                                dex=dex2,
                                token_in=token_b,
                                token_out=token_a,
                                amount_in=quote1.amount_out,
                                amount_out=quote2.amount_out,
                                price=quote2.price,
                                liquidity=quote2.liquidity,
                            ),
                        ]

                        # Calculate profit
                        profit_usd, profit_pct = await self._calculate_profit(
                            path, capital
                        )
                        gas_cost = await self._estimate_gas_cost(2)
                        net_profit = profit_usd - gas_cost

                        # Check profitability
                        if (
                            net_profit >= self.config.min_profit_usd
                            and profit_pct >= self.config.min_profit_percentage
                        ):
                            opportunity = ArbitrageOpportunity(
                                opportunity_id=self._generate_opportunity_id(),
                                type=ArbitrageType.TWO_HOP,
                                path=path,
                                expected_profit_usd=net_profit,
                                profit_percentage=profit_pct,
                                required_capital=capital,
                                estimated_gas_cost=gas_cost,
                                slippage_tolerance=self.config.max_slippage,
                                confidence_score=0.85,
                                timestamp=utc_now(),
                                metadata={
                                    "dex1": dex1.value,
                                    "dex2": dex2.value,
                                    "token_a": token_a,
                                    "token_b": token_b,
                                },
                            )
                            opportunities.append(opportunity)

        return opportunities

    async def discover_3hop_arbitrage(
        self, capital: Decimal = Decimal("10000")
    ) -> list[ArbitrageOpportunity]:
        """Discover 3-hop arbitrage opportunities.

        3-hop: Token A → Token B → Token C → Token A
        Example: WETH → USDC → DAI → WETH

        Args:
            capital: Starting capital

        Returns:
            List of opportunities

        Example:
            >>> discovery = ArbitrageDiscovery()
            >>> opportunities = await discovery.discover_3hop_arbitrage(Decimal("10000"))
            >>> for opp in opportunities:
            ...     print(f"Path: {' -> '.join([p.token_out for p in opp.path])}")
        """
        opportunities = []

        # Check 3-token paths
        tokens = self.config.enabled_tokens[:4]  # Limit for performance

        for i, token_a in enumerate(tokens):
            for token_b in tokens:
                if token_b == token_a:
                    continue
                for token_c in tokens:
                    if token_c in (token_a, token_b):
                        continue

                    # Use different DEXes for each hop
                    dexes = self.config.enabled_dexes[:3]

                    # Get quotes
                    quote1 = await self._get_price_quote(
                        dexes[0], token_a, token_b, capital
                    )
                    quote2 = await self._get_price_quote(
                        dexes[1], token_b, token_c, quote1.amount_out
                    )
                    quote3 = await self._get_price_quote(
                        dexes[2], token_c, token_a, quote2.amount_out
                    )

                    # Build path
                    path = [
                        TradingPair(
                            dex=dexes[0],
                            token_in=token_a,
                            token_out=token_b,
                            amount_in=capital,
                            amount_out=quote1.amount_out,
                            price=quote1.price,
                            liquidity=quote1.liquidity,
                        ),
                        TradingPair(
                            dex=dexes[1],
                            token_in=token_b,
                            token_out=token_c,
                            amount_in=quote1.amount_out,
                            amount_out=quote2.amount_out,
                            price=quote2.price,
                            liquidity=quote2.liquidity,
                        ),
                        TradingPair(
                            dex=dexes[2],
                            token_in=token_c,
                            token_out=token_a,
                            amount_in=quote2.amount_out,
                            amount_out=quote3.amount_out,
                            price=quote3.price,
                            liquidity=quote3.liquidity,
                        ),
                    ]

                    # Calculate profit
                    profit_usd, profit_pct = await self._calculate_profit(path, capital)
                    gas_cost = await self._estimate_gas_cost(3)
                    net_profit = profit_usd - gas_cost

                    # Check profitability
                    if (
                        net_profit >= self.config.min_profit_usd
                        and profit_pct >= self.config.min_profit_percentage
                    ):
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=self._generate_opportunity_id(),
                            type=ArbitrageType.THREE_HOP,
                            path=path,
                            expected_profit_usd=net_profit,
                            profit_percentage=profit_pct,
                            required_capital=capital,
                            estimated_gas_cost=gas_cost,
                            slippage_tolerance=self.config.max_slippage,
                            confidence_score=0.75,  # Lower confidence (more hops)
                            timestamp=utc_now(),
                            metadata={
                                "token_a": token_a,
                                "token_b": token_b,
                                "token_c": token_c,
                            },
                        )
                        opportunities.append(opportunity)

        return opportunities

    async def discover_triangle_arbitrage(
        self, dex: DEX = DEX.UNISWAP_V2, capital: Decimal = Decimal("10000")
    ) -> list[ArbitrageOpportunity]:
        """Discover triangle arbitrage on single DEX.

        Triangle: Token A → Token B → Token C → Token A (same DEX)
        Example: ETH → USDC → DAI → ETH on Uniswap

        Args:
            dex: DEX platform
            capital: Starting capital

        Returns:
            List of opportunities

        Example:
            >>> discovery = ArbitrageDiscovery()
            >>> opportunities = await discovery.discover_triangle_arbitrage(DEX.UNISWAP_V2)
            >>> for opp in opportunities:
            ...     print(f"DEX: {opp.metadata['dex']}, Profit: ${opp.expected_profit_usd}")
        """
        opportunities = []

        # Check 3-token triangular paths on same DEX
        tokens = self.config.enabled_tokens[:4]

        for token_a in tokens:
            for token_b in tokens:
                if token_b == token_a:
                    continue
                for token_c in tokens:
                    if token_c in (token_a, token_b):
                        continue

                    # All on same DEX
                    quote1 = await self._get_price_quote(dex, token_a, token_b, capital)
                    quote2 = await self._get_price_quote(
                        dex, token_b, token_c, quote1.amount_out
                    )
                    quote3 = await self._get_price_quote(
                        dex, token_c, token_a, quote2.amount_out
                    )

                    # Build path
                    path = [
                        TradingPair(
                            dex=dex,
                            token_in=token_a,
                            token_out=token_b,
                            amount_in=capital,
                            amount_out=quote1.amount_out,
                            price=quote1.price,
                            liquidity=quote1.liquidity,
                        ),
                        TradingPair(
                            dex=dex,
                            token_in=token_b,
                            token_out=token_c,
                            amount_in=quote1.amount_out,
                            amount_out=quote2.amount_out,
                            price=quote2.price,
                            liquidity=quote2.liquidity,
                        ),
                        TradingPair(
                            dex=dex,
                            token_in=token_c,
                            token_out=token_a,
                            amount_in=quote2.amount_out,
                            amount_out=quote3.amount_out,
                            price=quote3.price,
                            liquidity=quote3.liquidity,
                        ),
                    ]

                    # Calculate profit
                    profit_usd, profit_pct = await self._calculate_profit(path, capital)
                    gas_cost = await self._estimate_gas_cost(3)
                    net_profit = profit_usd - gas_cost

                    # Check profitability
                    if (
                        net_profit >= self.config.min_profit_usd
                        and profit_pct >= self.config.min_profit_percentage
                    ):
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=self._generate_opportunity_id(),
                            type=ArbitrageType.TRIANGLE,
                            path=path,
                            expected_profit_usd=net_profit,
                            profit_percentage=profit_pct,
                            required_capital=capital,
                            estimated_gas_cost=gas_cost,
                            slippage_tolerance=self.config.max_slippage,
                            confidence_score=0.80,
                            timestamp=utc_now(),
                            metadata={
                                "dex": dex.value,
                                "token_a": token_a,
                                "token_b": token_b,
                                "token_c": token_c,
                            },
                        )
                        opportunities.append(opportunity)

        return opportunities

    async def discover_all_opportunities(
        self, capital: Decimal = Decimal("10000")
    ) -> list[ArbitrageOpportunity]:
        """Discover all arbitrage opportunities.

        Args:
            capital: Starting capital

        Returns:
            Combined list of all opportunities

        Example:
            >>> discovery = ArbitrageDiscovery()
            >>> all_opps = await discovery.discover_all_opportunities(Decimal("10000"))
            >>> best = max(all_opps, key=lambda x: x.expected_profit_usd)
            >>> print(f"Best: {best.type}, Profit: ${best.expected_profit_usd}")
        """
        # Run all discovery methods in parallel
        results = await asyncio.gather(
            self.discover_2hop_arbitrage(capital),
            self.discover_3hop_arbitrage(capital),
            self.discover_triangle_arbitrage(DEX.UNISWAP_V2, capital),
        )

        # Flatten results
        all_opportunities = []
        for opportunities in results:
            all_opportunities.extend(opportunities)

        # Sort by profit (descending)
        all_opportunities.sort(key=lambda x: x.expected_profit_usd, reverse=True)

        return all_opportunities

    async def get_opportunity_by_id(
        self, opportunity_id: str, opportunities: list[ArbitrageOpportunity]
    ) -> ArbitrageOpportunity | None:
        """Get opportunity by ID.

        Args:
            opportunity_id: Opportunity ID
            opportunities: List of opportunities

        Returns:
            Opportunity or None
        """
        for opp in opportunities:
            if opp.opportunity_id == opportunity_id:
                return opp
        return None

    async def simulate_opportunity(
        self, opportunity: ArbitrageOpportunity
    ) -> dict:
        """Simulate opportunity execution.

        Args:
            opportunity: Opportunity to simulate

        Returns:
            Simulation result
        """
        # Simulate execution with slippage
        slippage_impact = opportunity.expected_profit_usd * opportunity.slippage_tolerance
        simulated_profit = opportunity.expected_profit_usd - slippage_impact

        return {
            "opportunity_id": opportunity.opportunity_id,
            "type": opportunity.type.value,
            "expected_profit": str(opportunity.expected_profit_usd),
            "simulated_profit": str(simulated_profit),
            "slippage_impact": str(slippage_impact),
            "success_probability": opportunity.confidence_score,
            "recommendation": (
                "Execute" if simulated_profit > self.config.min_profit_usd else "Skip"
            ),
        }

    async def discover_with_real_data(
        self,
        capital: Decimal = Decimal("10000"),
        oneinch_api_key: str | None = None,
        chain: str = "ethereum",
    ) -> list[ArbitrageOpportunity]:
        """Discover arbitrage using real DEX data via 1inch API.

        This method uses the DEXPriceFetcher to get real-time prices
        from 1inch aggregator and other sources.

        Args:
            capital: Starting capital in USD
            oneinch_api_key: 1inch API key (required for real data)
            chain: Blockchain to scan (ethereum, arbitrum, base)

        Returns:
            List of real arbitrage opportunities

        Example:
            >>> discovery = ArbitrageDiscovery()
            >>> opps = await discovery.discover_with_real_data(
            ...     capital=Decimal("10000"),
            ...     oneinch_api_key="your-api-key"
            ... )
            >>> for opp in opps:
            ...     print(f"{opp.type}: ${opp.expected_profit_usd} profit")

        Note:
            Without an API key, falls back to simulated data.
        """
        from app.application.ultra.dex_price_fetcher import DEXPriceFetcher

        fetcher = DEXPriceFetcher(
            oneinch_api_key=oneinch_api_key,
            chain=chain,
        )

        opportunities = []

        try:
            # Token pairs to check
            token_pairs = [
                ("WETH", "USDC"),
                ("WETH", "USDT"),
                ("WETH", "DAI"),
                ("USDC", "USDT"),
                ("USDC", "DAI"),
                ("WBTC", "WETH"),
            ]

            for token_a, token_b in token_pairs:
                # Find arbitrage between token pair
                arb = await fetcher.find_arbitrage_opportunity(
                    token_a=token_a,
                    token_b=token_b,
                    capital=capital,
                )

                if arb and arb["net_profit_usd"] > float(self.config.min_profit_usd):
                    # Convert to ArbitrageOpportunity
                    path = [
                        TradingPair(
                            dex=DEX.UNISWAP_V3,  # Simplified
                            token_in=token_a,
                            token_out=token_b,
                            amount_in=capital,
                            amount_out=Decimal(str(arb["final_amount"])),
                            price=Decimal(str(arb["final_amount"])) / capital,
                            liquidity=Decimal("1000000"),
                        ),
                        TradingPair(
                            dex=DEX.SUSHISWAP,  # Simplified
                            token_in=token_b,
                            token_out=token_a,
                            amount_in=Decimal(str(arb["final_amount"])),
                            amount_out=Decimal(str(arb["final_amount"])),
                            price=Decimal("1"),
                            liquidity=Decimal("1000000"),
                        ),
                    ]

                    opportunity = ArbitrageOpportunity(
                        opportunity_id=self._generate_opportunity_id(),
                        type=ArbitrageType.CROSS_DEX,
                        path=path,
                        expected_profit_usd=Decimal(str(arb["net_profit_usd"])),
                        profit_percentage=Decimal(str(arb["profit_pct"])) / 100,
                        required_capital=capital,
                        estimated_gas_cost=Decimal(str(arb["gas_cost_usd"])),
                        slippage_tolerance=self.config.max_slippage,
                        confidence_score=0.9 if arb["is_real_data"] else 0.6,
                        timestamp=utc_now(),
                        metadata={
                            "buy_dex": arb["buy_dex"],
                            "sell_dex": arb["sell_dex"],
                            "protocols_used": arb["protocols_used"],
                            "is_real_data": arb["is_real_data"],
                            "chain": chain,
                        },
                    )
                    opportunities.append(opportunity)

        finally:
            await fetcher.close()

        # Sort by profit
        opportunities.sort(key=lambda x: x.expected_profit_usd, reverse=True)

        return opportunities
