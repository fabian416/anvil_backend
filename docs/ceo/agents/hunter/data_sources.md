# Hunter AI Data Sources

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Documented

---

## Overview

Hunter AI aggregates data from multiple sources to provide comprehensive market intelligence:

| Source | Status | Type | Cost |
|--------|--------|------|------|
| CoinGecko | ✅ REAL | Prices & Market Data | Free |
| Hyperliquid | ✅ REAL | Swap Quotes | Free |
| RSS News | ✅ REAL | News Sentiment | Free |
| Reddit | ⚠️ Fallback | Social Sentiment | OAuth2 Required |
| Twitter | 🟡 Simulated | Social Sentiment | $100/month |
| Discord | 🟡 Simulated | Social Sentiment | Bot Token (Free) |

---

## Real Data Sources

### 1. CoinGecko (Price Data)

**Status**: ✅ Fully Integrated

**Location**: `src/app/infrastructure/adapters/external/coingecko_client.py`

**Features**:
- Real-time prices for 10,000+ cryptocurrencies
- Historical OHLCV data (up to 365 days)
- Market cap and volume data
- 24h price changes
- 7-day high/low

**Methods**:

```python
# Single token price
price = await client.get_price("ethereum")
# Returns: TokenPrice(usd=2988.55, usd_24h_change=-0.83, market_cap=360750000000, volume_24h=21950000000)

# Bulk prices (more efficient)
prices = await client.get_prices_bulk(["bitcoin", "ethereum", "solana"])
# Returns: dict[str, TokenPrice]

# Historical data
chart = await client.get_market_chart("ethereum", days=7)
# Returns: MarketChart(prices=[[timestamp, price], ...], volumes=[[...], ...])
```

**Rate Limits**: 
- Free tier: 10-50 calls/minute
- Pro tier: Higher limits available

**API Documentation**: https://www.coingecko.com/en/api/documentation

---

### 2. Hyperliquid (Swap Quotes)

**Status**: ✅ Fully Integrated

**Location**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Features**:
- Real-time spot swap quotes
- Order book data (L2)
- Zero gas fees
- High-speed execution

**Methods**:

```python
quote = await client.get_spot_quote(
    from_token="ETH",
    to_token="USDC",
    amount=1.0,
)
# Returns: SpotQuote(
#     from_token="ETH",
#     to_token="USDC",
#     from_amount=1.0,
#     to_amount=2988.55,
#     price=2988.55,
#     mid_price=2988.60,
#     spread_bps=0.05,
# )
```

**Rate Limits**: Unlimited

**Supported Pairs**:
- All major tokens against USDC
- Meme tokens (PEPE, TRUMP, PURR, etc.)

---

### 3. RSS News Feeds

**Status**: ✅ Fully Integrated

**Location**: `src/app/infrastructure/adapters/external/rss_news_client.py`

**Supported Sources**:

| Source | Feed URL |
|--------|----------|
| CoinDesk | `coindesk.com/arc/outboundfeeds/rss/` |
| CoinTelegraph | `cointelegraph.com/rss` |
| Decrypt | `decrypt.co/feed` |
| The Block | `theblock.co/rss.xml` |
| Bitcoin Magazine | `bitcoinmagazine.com/feed` |

**Methods**:

```python
articles = await client.get_token_news("ETH", "Ethereum", limit=10)
# Returns: list[NewsArticle]

for article in articles:
    print(f"[{article.source}] {article.title}")
    print(f"  Published: {article.published_at}")
    print(f"  Link: {article.url}")
```

**Features**:
- No authentication required
- Automatic XML/Atom parsing
- HTML tag stripping
- Publication date parsing

---

## Fallback/Simulated Sources

### 4. Reddit (Social Sentiment)

**Status**: ⚠️ Fallback Mode

Reddit blocks server requests without OAuth2 authentication (since 2023).

**Current Behavior**:
1. Attempts real API call
2. Falls back to simulated data if blocked (403 error)

**Monitored Subreddits**:
- r/cryptocurrency
- r/ethereum
- r/bitcoin
- r/ethtrader
- r/defi
- r/cryptomarkets

**To Enable Real Reddit Data**:

1. Create Reddit App: https://www.reddit.com/prefs/apps
2. Add to `config/local/.secrets.toml`:

```toml
[reddit]
client_id = "your_client_id"
client_secret = "your_client_secret"
```

---

### 5. Twitter (Social Sentiment)

**Status**: 🟡 Simulated

Twitter API requires paid access ($100/month minimum for Basic tier).

**Current Behavior**:
- Uses simulated sentiment data
- Realistic scores based on market conditions

**To Enable Real Twitter Data**:

1. Apply for Twitter Developer Account: https://developer.twitter.com/
2. Subscribe to Basic or Pro tier ($100-$5000/month)
3. Add to `config/local/.secrets.toml`:

```toml
[twitter]
bearer_token = "your_bearer_token"
api_key = "your_api_key"
api_secret = "your_api_secret"
```

---

### 6. Discord (Social Sentiment)

**Status**: 🟡 Simulated

Discord requires a bot token and the bot must be invited to relevant crypto servers.

**Current Behavior**:
- Uses simulated sentiment data
- Realistic scores based on community activity patterns

**To Enable Real Discord Data**:

1. Create Discord Application: https://discord.com/developers/applications
2. Create Bot and get token
3. Invite bot to crypto Discord servers
4. Add to `config/local/.secrets.toml`:

```toml
[discord]
bot_token = "your_bot_token"
guild_ids = ["server_id_1", "server_id_2"]
```

---

## Sentiment Aggregation

Hunter AI aggregates sentiment from all sources with configurable weights:

### Signal Configuration

```python
@dataclass
class SignalConfig:
    sentiment_weight: float = 0.40   # 40% of final score
    prediction_weight: float = 0.35  # 35% of final score
    risk_weight: float = 0.25        # 25% of final score
```

### Source Weights (within sentiment)

| Source | Weight | Status |
|--------|--------|--------|
| Twitter | 30% | 🟡 Simulated |
| Reddit | 25% | ⚠️ Fallback |
| Discord | 20% | 🟡 Simulated |
| News | 25% | ✅ Real |

---

## API Clients Location

All external API clients are located in:

```
src/app/infrastructure/adapters/external/
├── coingecko_client.py     # CoinGecko price data
├── hyperliquid_client.py   # Hyperliquid swap quotes
├── reddit_client.py        # Reddit posts (with fallback)
├── rss_news_client.py      # RSS news aggregation
├── oneinch_client.py       # 1inch DEX aggregator
├── defillama_client.py     # DeFiLlama TVL data
├── morpho_client.py        # Morpho lending
├── aave_client.py          # Aave money market
└── etherscan_client.py     # Etherscan API
```

---

## Hunter AI Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    TradingSignalGenerator                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ SentimentAggr.  │  │ LSTMPredictor   │  │ RiskAnalyzer│ │
│  │ (4 sources)     │  │ (CoinGecko)     │  │ (on-chain)  │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           ▼                    ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │      Weighted Composite Score: 68/100                   ││
│  │  (sentiment×0.4) + (prediction×0.35) + (risk×0.25)     ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Signal: BUY | Confidence: 57%                          ││
│  │  Entry: $1,964 | Stop: $1,851 | Take Profit: $2,191    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Example Response

```json
{
  "intent": "hunter_sentiment",
  "enrichment": {
    "overall_score": 66.97,
    "classification": "bullish",
    "hunter_tool": "sentiment_aggregator",
    "sources": {
      "twitter": 63,
      "reddit": 72,
      "discord": 92,
      "news": 52
    }
  },
  "agent_message": {
    "content": "📊 **Sentiment Analysis for ETH**\n\n**Overall:** Bullish (67.0/100)\n**Confidence:** 43%\n\n**By Source:**\n- Twitter: 🟢 63/100\n- Reddit: 🟢 72/100\n- Discord: 🟢 92/100\n- News: 🟡 52/100"
  }
}
```

---

## Rate Limits Summary

| API | Free Tier | Notes |
|-----|-----------|-------|
| CoinGecko | 10-50/min | Use bulk endpoints |
| Hyperliquid | Unlimited | No restrictions |
| RSS Feeds | Unlimited | No rate limiting |
| Reddit | 60/min | OAuth2 required |
| Twitter | Varies | Paid plans only |
| Discord | Varies | Bot token required |

---

## Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| Token Prices | 60s | Redis |
| Market Charts | 5min | Redis |
| Swap Quotes | 0s (real-time) | None |
| News Articles | 15min | Redis |
| Sentiment | 5min | Redis |

---

## Future Enhancements

1. **LunarCrush Integration** - Social metrics aggregator (free tier available)
2. **Santiment Integration** - On-chain + social analytics
3. **CryptoPanic API** - News aggregation with sentiment
4. **The Graph** - On-chain data for whale tracking
5. **Glassnode** - Advanced on-chain metrics

---

## Related Documentation

- **Main Data Sources Doc**: `/docs/HUNTER_AI_DATA_SOURCES.md`
- **CoinGecko API Docs**: https://www.coingecko.com/en/api/documentation
- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/hyperliquid-docs/
