"""
Instrumented External API Clients.

Provides API clients with full telemetry instrumentation:
- Request/response timing
- Error tracking and categorization
- Rate limit detection
- Distributed tracing
- Prometheus metrics export

Usage:
    from app.infrastructure.adapters.external.instrumented import (
        InstrumentedCoinGeckoClient,
        InstrumentedDefiLlamaClient,
        InstrumentedOneInchClient,
        InstrumentedUniswapClient,
        InstrumentedAaveClient,
        InstrumentedCurveClient,
        InstrumentedHyperliquidClient,
        InstrumentedGasOracleClient,
    )

    # Create client with telemetry
    client = InstrumentedCoinGeckoClient(api_key="...", telemetry=telemetry)

    # All calls automatically instrumented
    price = await client.get_price("ethereum")

    # View metrics
    metrics = telemetry.get_metrics("coingecko")
"""

from app.infrastructure.adapters.external.instrumented.instrumented_coingecko_client import (
    InstrumentedCoinGeckoClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_defillama_client import (
    InstrumentedDefiLlamaClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_oneinch_client import (
    InstrumentedOneInchClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_thegraph_client import (
    InstrumentedTheGraphClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_uniswap_client import (
    InstrumentedUniswapClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_aave_client import (
    InstrumentedAaveClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_curve_client import (
    InstrumentedCurveClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_hyperliquid_client import (
    InstrumentedHyperliquidClient,
)
from app.infrastructure.adapters.external.instrumented.instrumented_gas_oracle_client import (
    InstrumentedGasOracleClient,
)

__all__ = [
    # Market Data
    "InstrumentedCoinGeckoClient",
    "InstrumentedDefiLlamaClient",
    # DEX
    "InstrumentedOneInchClient",
    "InstrumentedUniswapClient",
    "InstrumentedCurveClient",
    # Lending
    "InstrumentedAaveClient",
    # Perpetuals
    "InstrumentedHyperliquidClient",
    # Infrastructure
    "InstrumentedTheGraphClient",
    "InstrumentedGasOracleClient",
]
