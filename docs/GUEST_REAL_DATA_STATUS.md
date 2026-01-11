# Guest Handler Real Data Status

**Last Updated:** 2026-01-11
**Directive:** Guests should always see **real data**, not demo/mock data

## Current Status Summary

### ✅ Handlers Using Real Data

| Intent | Handler | Data Source | Status |
|--------|---------|-------------|--------|
| `SWAP` | SwapHandler + Multi-step | 1inch API (real quotes) | ✅ Real |
| `MONEY_MARKET` | MoneyMarketHandler | Aave/Compound APIs (real APY) | ✅ Real |
| `SWAP_MOONPAY` | MoonPaySwapMultiStepHandler | MoonPaySwapHandler (real prices) | ✅ Real |
| `HUNTER_SENTIMENT` | Hunter AI | Real Twitter/Reddit/Discord/News | ✅ Real |
| `HUNTER_PRICE_PREDICTION` | LSTM Predictor | CoinGecko historical data | ✅ Real |
| `HUNTER_RISK_SIGNALS` | Risk Analyzer | Real market data | ✅ Real |
| `HUNTER_TRADING_SIGNALS` | Trading Signals | Real price/volume data | ✅ Real |
| `HUNTER_PATTERNS` | Pattern Detection | Real chart data | ✅ Real |
| `HUNTER_PORTFOLIO` | Portfolio Optimizer | Real holdings data | ✅ Real |
| `ULTRA_ARBITRAGE` | Arbitrage Finder | Real DEX prices | ✅ Real |
| `ULTRA_FLASH_LOANS` | Flash Loan Handler | Real protocol data | ✅ Real |
| `ULTRA_MEV_PROTECTION` | MEV Protector | Real mempool data | ✅ Real |
| `PROTOCOL_SEARCH` | GraphRAG | Real protocol data | ✅ Real |

### ⚠️ Handlers Using Demo Data (Needs Update)

| Intent | Handler | Current Data | Should Use | Priority |
|--------|---------|--------------|------------|----------|
| `BUY` | BuyMultiStepHandler | Demo prices (hardcoded) | CoinGeckoClient API | **HIGH** |
| `LENDING` | LendingMultiStepHandler | Demo APY (hardcoded) | MorphoGateway API | **HIGH** |
| `PORTFOLIO` | PortfolioMultiStepHandler | Demo holdings | N/A (see note) | **LOW** |
| `ACTIVITY` | ActivityMultiStepHandler | Demo transactions | N/A (see note) | **LOW** |

### 📝 Special Cases

**PORTFOLIO & ACTIVITY:**
- These show demo data for **preview/educational purposes**
- Guests don't have wallets, so there's no "real" portfolio to show
- Current approach: Show demo data with clear "Sign up to see YOUR portfolio" messaging
- **Recommendation:** Keep demo data for these intents as it's educational

**SEND, BALANCE, RECEIVE:**
- These are informational/instructional for guests
- Show guidance on how to use features (no real data needed)
- **Status:** Appropriate for guests

## Required Updates

### 1. BuyMultiStepHandler (`buy_multistep.py`)

**Current Implementation:**
```python
# Line 254-259
demo_prices = {
    "BTC": 45000, "ETH": 1950, "SOL": 32.5,
    "USDC": 1.0, "USDT": 1.0, "MATIC": 0.65
}
price_per_unit = demo_prices.get(crypto, 100)
```

**Required Change:**
```python
# Add to imports
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient

# Add to __init__
def __init__(self):
    self._coingecko = CoinGeckoClient()

# Replace demo_prices with real prices
async def _get_crypto_price(self, symbol: str) -> float:
    """Get real-time crypto price from CoinGecko."""
    coin_id_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "USDC": "usd-coin",
        "USDT": "tether",
        "MATIC": "matic-network"
    }
    coin_id = coin_id_map.get(symbol)
    if not coin_id:
        return 100.0  # Fallback

    try:
        price_data = await self._coingecko.get_price(coin_id)
        return price_data.usd
    except Exception as e:
        logger.warning(f"Failed to fetch price for {symbol}: {e}")
        return 100.0  # Fallback

# In _show_quote method
price_per_unit = await self._get_crypto_price(crypto)
```

### 2. LendingMultiStepHandler (`lending_multistep.py`)

**Current Implementation:**
```python
# Line 31-37
DEMO_APYS = {
    "USDC": 8.5,
    "USDT": 7.8,
    "DAI": 9.2,
    "ETH": 5.4,
    "WBTC": 4.2,
}
```

**Required Change:**
```python
# Add to imports
from app.application.chat.handlers.lending_handler import LendingHandler
from app.infrastructure.adapters.defi.morpho_gateway import MorphoGateway

# Add to __init__
def __init__(self, morpho_gateway: MorphoGateway | None = None):
    self._morpho_gateway = morpho_gateway or MorphoGateway()
    self._lending_handler = LendingHandler(self._morpho_gateway)

# Replace DEMO_APYS with real APY
async def _get_best_apy(self, asset: str, chain: str = "ethereum") -> float:
    """Get real APY from Morpho vaults."""
    try:
        result = await self._lending_handler.handle(
            asset=asset,
            chain=chain,
            language="en"
        )
        return result.best_apy
    except Exception as e:
        logger.warning(f"Failed to fetch APY for {asset}: {e}")
        return 5.0  # Fallback

# In _show_quote method
apy = await self._get_best_apy(asset, chain="ethereum")
```

## Implementation Priority

1. **HIGH:** Update `BuyMultiStepHandler` to use CoinGeckoClient
2. **HIGH:** Update `LendingMultiStepHandler` to use MorphoGateway
3. **LOW:** Review Portfolio/Activity handlers (likely keep demo for preview)

## Testing Requirements

After updates, verify:
- ✅ Real prices are fetched from CoinGecko
- ✅ Real APY rates are fetched from Morpho
- ✅ Fallback values work if APIs fail
- ✅ Guest experience shows "real" data with signup CTAs
- ✅ No transaction execution for guests (read-only)

## Notes

- All multi-step handlers maintain conversational UX while using real data
- Guests get read-only access to real protocol data
- Signup CTAs are shown for transaction execution
- Error handling includes fallback to approximate values if APIs fail
