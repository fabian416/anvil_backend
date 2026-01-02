# Hunter AI Data Sources

This document describes the data sources used by Hunter AI for sentiment analysis, price prediction, and trading signals.

## Overview

Hunter AI aggregates data from multiple sources to provide comprehensive market intelligence:

| Source | Status | Type | Cost |
|--------|--------|------|------|
| CoinGecko | ✅ REAL | Prices & Market Data | Free |
| RSS News | ✅ REAL | News Sentiment | Free |
| Reddit | ⚠️ Fallback | Social Sentiment | OAuth2 Required |
| Twitter | 🟡 Simulated | Social Sentiment | $100/month |
| Discord | 🟡 Simulated | Social Sentiment | Bot Token (Free) |

## Real Data Sources

### 1. CoinGecko (Price Data)

**Status**: ✅ Fully Integrated

**Features**:
- Real-time prices for 10,000+ cryptocurrencies
- Historical OHLCV data (up to 365 days)
- Market cap and volume data
- 24h price changes

**Usage**:
```python
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient

client = CoinGeckoClient()
price = await client.get_price("ethereum")
print(f"ETH: ${price.usd:,.2f} ({price.usd_24h_change:+.2f}%)")

# Historical data for LSTM predictions
chart = await client.get_market_chart("ethereum", days=30)
```

**Rate Limits**: 10-50 calls/minute (free tier)

**API Documentation**: https://www.coingecko.com/en/api/documentation

---

### 2. RSS News Feeds (News Sentiment)

**Status**: ✅ Fully Integrated

**Supported Sources**:
- CoinDesk (`coindesk.com/arc/outboundfeeds/rss/`)
- CoinTelegraph (`cointelegraph.com/rss`)
- Decrypt (`decrypt.co/feed`)
- The Block (`theblock.co/rss.xml`)
- Bitcoin Magazine (`bitcoinmagazine.com/feed`)

**Usage**:
```python
from app.infrastructure.adapters.external.rss_news_client import RSSNewsClient

client = RSSNewsClient()
articles = await client.get_token_news("ETH", "Ethereum", limit=10)
for article in articles:
    print(f"[{article.source}] {article.title}")
```

**Features**:
- No authentication required
- Automatic XML/Atom parsing
- HTML tag stripping
- Publication date parsing

---

### 3. Reddit (Social Sentiment)

**Status**: ⚠️ Fallback Mode

Reddit blocks requests from servers without OAuth2 authentication (since 2023).

**Current Behavior**:
1. Attempts real API call
2. Falls back to realistic simulated data if blocked

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

## Simulated Data Sources

### 4. Twitter (Social Sentiment)

**Status**: 🟡 Simulated

Twitter API requires paid access ($100/month minimum for Basic tier).

**To Enable Real Twitter Data**:

1. Apply for Twitter Developer Account: https://developer.twitter.com/
2. Subscribe to Basic or Pro tier
3. Add to `config/local/.secrets.toml`:
```toml
[twitter]
bearer_token = "your_bearer_token"
api_key = "your_api_key"
api_secret = "your_api_secret"
```

---

### 5. Discord (Social Sentiment)

**Status**: 🟡 Simulated

Discord requires a bot token and the bot must be invited to relevant crypto servers.

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

```python
@dataclass
class SignalConfig:
    sentiment_weight: float = 0.40   # 40% of final score
    prediction_weight: float = 0.35  # 35% of final score
    risk_weight: float = 0.25        # 25% of final score
```

**Source Weights (within sentiment)**:
- Twitter: 30%
- Reddit: 25%
- Discord: 20%
- News: 25%

---

## API Clients Location

All external API clients are located in:
```
src/app/infrastructure/adapters/external/
├── coingecko_client.py     # CoinGecko price data
├── reddit_client.py        # Reddit posts (with fallback)
├── rss_news_client.py      # RSS news aggregation
├── oneinch_client.py       # 1inch DEX aggregator
├── defillama_client.py     # DeFiLlama TVL data
├── morpho_client.py        # Morpho lending
├── aave_client.py          # Aave money market
└── ...
```

---

## Hunter AI Components

The Hunter AI analysis pipeline:

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

## Future Enhancements

1. **LunarCrush Integration** - Social metrics aggregator (free tier available)
2. **Santiment Integration** - On-chain + social analytics
3. **CryptoPanic API** - News aggregation with sentiment
4. **The Graph** - On-chain data for whale tracking
