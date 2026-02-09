# Sentiment Analysis — Chat Agent Response Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Chat Response Enrichment (conversations/messages)  
**Intent**: `HUNTER_SENTIMENT`  
**Related**: Hunter AI Agent, CoinGecko API, Chat Sources Spec

---

## Overview

When a user asks about token sentiment (e.g., "what's the sentiment on BTC?", "is ETH bullish?"), the unified chat router directs to the **Hunter AI Agent** which produces a structured `sentiment_analysis` enrichment block. This spec defines the **response schema** including the **chart_url** field — a server-generated URL to a token price chart image that the frontend renders inline in the chat bubble.

---

## Intent Detection

### Trigger Phrases

```
"sentiment on {token}"
"is {token} bullish/bearish?"
"what's the market feeling on {token}?"
"how is {token} doing?"
"BTC sentiment"
"market sentiment for ETH"
"what do people think about SOL?"
```

### Intent Classification

```python
# IntentDetectorService maps to:
intent = "HUNTER_SENTIMENT"
confidence >= 0.85
entities = [{"type": "cryptocurrency", "value": "BTC", "confidence": 0.98}]
```

---

## Response Schema

### Enrichment Block: `sentiment_analysis`

```python
class SentimentAnalysisEnrichment(BaseModel):
    type: Literal["sentiment_analysis"] = "sentiment_analysis"
    token: str                          # "BTC", "ETH", "SOL"
    token_name: str                     # "Bitcoin", "Ethereum"
    sentiment: Literal["bullish", "bearish", "neutral"]
    score: float                        # -1.0 (max bearish) to 1.0 (max bullish)
    confidence: float                   # 0.0 to 1.0 — how confident in the score
    chart_url: str                      # Server-generated chart image URL
    chart_range: str                    # "7d" default, matches chart_url
    summary: str                        # LLM-generated natural language summary
    price_usd: str                      # Current price at time of analysis
    change_24h: float                   # 24h % change
    volume_24h_usd: str                 # 24h trading volume
    fear_greed_index: int | None        # 0-100, null if unavailable
    fear_greed_label: str | None        # "Extreme Fear" / "Fear" / "Neutral" / "Greed" / "Extreme Greed"
    signals: list[SentimentSignal]      # Individual signal breakdowns
    sources: list[str]                  # ["coingecko", "fear_greed_index", "social_sentiment"]
    analyzed_at: str                    # ISO8601 timestamp

class SentimentSignal(BaseModel):
    source: str                         # "coingecko", "twitter", "reddit", "news", "on_chain"
    signal: Literal["bullish", "bearish", "neutral"]
    weight: float                       # 0.0-1.0 contribution to overall score
    detail: str                         # "Price up 5.2% in 24h with increasing volume"
    data_points: int | None             # Number of data points analyzed
```

### Example Response

```json
{
  "user_message": {
    "content": "what's the sentiment on BTC?",
    "id": "msg-uuid-123"
  },
  "agent_message": {
    "content": "Bitcoin is showing strong bullish momentum right now. The price is up 5.2% over the past 24 hours with increasing volume, and the Fear & Greed Index sits at 72 (Greed). Social sentiment across Twitter and Reddit is predominantly positive, with discussions focused on institutional adoption. On-chain data shows accumulation by large holders. Overall sentiment score: 0.78 (bullish).",
    "agent_type": "hunter_ai"
  },
  "routing": {
    "intent": "HUNTER_SENTIMENT",
    "confidence": 0.95,
    "handler": "hunter_sentiment_analyzer",
    "total_latency_ms": 1200
  },
  "enrichment": {
    "sentiment_analysis": {
      "type": "sentiment_analysis",
      "token": "BTC",
      "token_name": "Bitcoin",
      "sentiment": "bullish",
      "score": 0.78,
      "confidence": 0.85,
      "chart_url": "https://api.anvil.finance/api/v1/charts/BTC?range=7d&theme=dark&w=600&h=300",
      "chart_range": "7d",
      "summary": "Bitcoin showing strong bullish momentum with institutional buying pressure and positive social sentiment.",
      "price_usd": "97,450.00",
      "change_24h": 5.2,
      "volume_24h_usd": "42,500,000,000",
      "fear_greed_index": 72,
      "fear_greed_label": "Greed",
      "signals": [
        {
          "source": "coingecko",
          "signal": "bullish",
          "weight": 0.35,
          "detail": "Price up 5.2% in 24h, 15.3% in 7d. Volume increasing 23% above average.",
          "data_points": 1
        },
        {
          "source": "fear_greed_index",
          "signal": "bullish",
          "weight": 0.20,
          "detail": "Fear & Greed Index at 72 (Greed), up from 58 yesterday.",
          "data_points": 1
        },
        {
          "source": "twitter",
          "signal": "bullish",
          "weight": 0.15,
          "detail": "67% positive mentions in last 24h across 12,450 tweets.",
          "data_points": 12450
        },
        {
          "source": "reddit",
          "signal": "bullish",
          "weight": 0.15,
          "detail": "Bullish sentiment in r/Bitcoin and r/CryptoCurrency with 4.2k upvotes on bullish posts.",
          "data_points": 847
        },
        {
          "source": "on_chain",
          "signal": "bullish",
          "weight": 0.15,
          "detail": "Net exchange outflows of 2,340 BTC in 24h indicating accumulation.",
          "data_points": 1
        }
      ],
      "sources": ["coingecko", "fear_greed_index", "twitter", "reddit", "on_chain"],
      "analyzed_at": "2026-02-09T14:30:00Z"
    }
  },
  "sources": [
    {
      "source_type": "api",
      "source_name": "CoinGecko",
      "url": "https://www.coingecko.com/en/coins/bitcoin",
      "citation_text": "CoinGecko price and market data for BTC",
      "fetched_at": "2026-02-09T14:30:00Z",
      "provider": "CoinGecko API",
      "relevance_score": 1.0
    },
    {
      "source_type": "api",
      "source_name": "Alternative.me Fear & Greed Index",
      "url": "https://alternative.me/crypto/fear-and-greed-index/",
      "citation_text": "Crypto Fear & Greed Index",
      "fetched_at": "2026-02-09T14:30:00Z"
    }
  ]
}
```

---

## Chart URL Generation

### Chart Endpoint

```
GET /api/v1/charts/{token_symbol}
```

**Auth**: Optional (public, rate-limited)  
**Cache**: CDN-cached, 5-minute TTL  
**Response**: PNG image (or SVG)

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| range | string | "7d" | Time range: "1h", "24h", "7d", "30d", "90d", "1y" |
| theme | string | "dark" | "dark" or "light" |
| w | int | 600 | Width in pixels (max 1200) |
| h | int | 300 | Height in pixels (max 600) |
| indicators | string | null | Comma-separated: "sma_20,ema_50,bollinger" |
| sentiment_overlay | bool | false | Overlay sentiment score band on chart |

### Chart URL Construction (Backend)

```python
class ChartURLBuilder:
    """Builds chart URLs for token price charts."""

    BASE_URL = "{API_BASE_URL}/api/v1/charts"

    def build_chart_url(
        self,
        token: str,
        range: str = "7d",
        theme: str = "dark",
        width: int = 600,
        height: int = 300,
        sentiment_overlay: bool = False,
    ) -> str:
        params = {
            "range": range,
            "theme": theme,
            "w": width,
            "h": height,
        }
        if sentiment_overlay:
            params["sentiment_overlay"] = "true"

        query = urlencode(params)
        return f"{self.BASE_URL}/{token.upper()}?{query}"
```

### Chart Generation (Server-Side)

```python
# Implementation options (pick one):

# Option A: CoinGecko Sparkline + Custom Renderer
# - Fetch OHLCV from CoinGecko /coins/{id}/market_chart
# - Render with matplotlib/plotly → PNG
# - Cache rendered image 5 min

# Option B: TradingView Widget URL (client-side)
# - Return TradingView lightweight chart embed URL
# - Frontend renders widget directly
# - No server-side rendering needed

# Option C: Pre-generated SVG (recommended for MVP)
# - Fetch price history from CoinGecko
# - Generate SVG sparkline server-side
# - Return as image/svg+xml
# - Lightweight, fast, cacheable

# Recommended: Option C for MVP, Option A for production
```

### Chart Data Source

```python
async def get_chart_data(self, token: str, range: str) -> list[PricePoint]:
    """Fetch OHLCV data for chart rendering."""
    # CoinGecko endpoint
    coingecko_id = self._resolve_coingecko_id(token)  # BTC → bitcoin
    
    range_to_days = {
        "1h": 0.042, "24h": 1, "7d": 7,
        "30d": 30, "90d": 90, "1y": 365
    }
    days = range_to_days.get(range, 7)
    
    data = await self._coingecko.get(
        f"/coins/{coingecko_id}/market_chart",
        params={"vs_currency": "usd", "days": days}
    )
    
    return [
        PricePoint(timestamp=p[0], price=p[1])
        for p in data["prices"]
    ]
```

---

## Sentiment Score Calculation

### Weighted Algorithm

```python
class SentimentScoreCalculator:
    """Calculates composite sentiment score from multiple signals."""

    WEIGHTS = {
        "coingecko": 0.35,      # Price action + volume
        "fear_greed_index": 0.20,  # Market-wide sentiment
        "twitter": 0.15,        # Social sentiment
        "reddit": 0.15,         # Social sentiment
        "on_chain": 0.15,       # On-chain metrics
    }

    def calculate(self, signals: list[SentimentSignal]) -> tuple[float, str]:
        """
        Returns: (score: -1.0 to 1.0, label: bullish/bearish/neutral)
        """
        total_weight = 0.0
        weighted_score = 0.0

        for signal in signals:
            weight = self.WEIGHTS.get(signal.source, 0.10)
            signal_value = self._signal_to_numeric(signal.signal)
            weighted_score += signal_value * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0, "neutral"

        score = weighted_score / total_weight  # Normalize to -1.0 to 1.0

        if score > 0.25:
            label = "bullish"
        elif score < -0.25:
            label = "bearish"
        else:
            label = "neutral"

        return round(score, 2), label

    def _signal_to_numeric(self, signal: str) -> float:
        return {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}[signal]
```

### Individual Signal Generators

| Source | Data Provider | Signal Logic |
|--------|---------------|--------------|
| **CoinGecko** | CoinGecko API | Price change > 3% = bullish, < -3% = bearish. Volume above 20-day avg = confirms. |
| **Fear & Greed** | alternative.me | Index > 55 = bullish, < 45 = bearish, else neutral |
| **Twitter** | Hunter AI (Perplexity Sonar) | Sentiment classification of recent tweets mentioning token |
| **Reddit** | Hunter AI (Perplexity Sonar) | Sentiment of top posts in crypto subreddits |
| **On-chain** | Alchemy / Dune Analytics | Exchange flows: net outflows = bullish (accumulation), net inflows = bearish (selling) |

---

## Caching Strategy

| Data | Cache Key | TTL | Source |
|------|-----------|-----|--------|
| CoinGecko price | `price:{token}` | 30s | CoinGecko API |
| Fear & Greed Index | `fear_greed` | 5 min | alternative.me |
| Social sentiment | `social:{token}` | 10 min | Perplexity Sonar |
| Chart image | `chart:{token}:{range}:{theme}` | 5 min | Server-rendered |
| Composite score | `sentiment:{token}` | 2 min | Calculated |

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/charts/chart_image.py` | GET /charts/{token} endpoint |
| **Application** | `queries/hunter/sentiment_analysis.py` | SentimentAnalysisHandler |
| **Application** | `services/chart_url_builder.py` | Chart URL construction |
| **Domain** | `entities/sentiment.py` | SentimentResult, SentimentSignal value objects |
| **Domain** | `ports/sentiment_provider.py` | SentimentDataProvider protocol |
| **Domain** | `ports/chart_renderer.py` | ChartRenderer protocol |
| **Infrastructure** | `adapters/external/coingecko_client.py` | CoinGecko price + market data |
| **Infrastructure** | `adapters/external/fear_greed_client.py` | Fear & Greed Index API |
| **Infrastructure** | `adapters/chart/svg_chart_renderer.py` | SVG sparkline generator |
| **Infrastructure** | `adapters/cache/redis_sentiment_cache.py` | Redis caching layer |

---

## Handler Integration

```python
class SentimentAnalysisHandler:
    """Handles HUNTER_SENTIMENT intent."""

    async def handle(self, query: SentimentQuery) -> SentimentResult:
        token = query.token.upper()

        # 1. Parallel data fetching
        price_data, fear_greed, social_data, on_chain = await asyncio.gather(
            self._coingecko.get_price_with_market(token),
            self._fear_greed.get_current(),
            self._hunter_ai.get_social_sentiment(token),
            self._on_chain.get_exchange_flows(token),
            return_exceptions=True,
        )

        # 2. Build individual signals
        signals = []
        if not isinstance(price_data, Exception):
            signals.append(self._build_price_signal(price_data))
        if not isinstance(fear_greed, Exception):
            signals.append(self._build_fear_greed_signal(fear_greed))
        if not isinstance(social_data, Exception):
            signals.extend(self._build_social_signals(social_data))
        if not isinstance(on_chain, Exception):
            signals.append(self._build_on_chain_signal(on_chain))

        # 3. Calculate composite score
        score, sentiment = self._calculator.calculate(signals)

        # 4. Build chart URL
        chart_url = self._chart_builder.build_chart_url(
            token=token, range="7d", sentiment_overlay=True
        )

        # 5. Generate LLM summary
        summary = await self._llm.generate_sentiment_summary(
            token=token, score=score, sentiment=sentiment, signals=signals
        )

        return SentimentResult(
            token=token,
            sentiment=sentiment,
            score=score,
            chart_url=chart_url,
            summary=summary,
            signals=signals,
            price_usd=price_data.current_price,
            change_24h=price_data.change_24h_pct,
            fear_greed_index=fear_greed.value if fear_greed else None,
        )
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Total response time | < 2s |
| Chart URL resolution | < 100ms (URL construction only) |
| Chart image generation | < 500ms (server-side render) |
| CoinGecko API | < 300ms |
| Fear & Greed API | < 200ms |
| Social sentiment (Sonar) | < 1.5s |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Token not found | Return error: "Token {X} not recognized" |
| CoinGecko down | Partial response with available signals, score marked low confidence |
| Fear & Greed unavailable | Omit from signals, adjust weights |
| Social data unavailable | Omit from signals, return price-only analysis |
| Chart generation fails | Fallback to CoinGecko chart URL: `https://www.coingecko.com/en/coins/{id}` |

---

## Frontend Rendering

```
┌─────────────────────────────────────────┐
│  🤖 Bitcoin Sentiment Analysis          │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  📈  BTC  $97,450  ↑ 5.2% (24h)   ││
│  │                                     ││
│  │  ┌─────────────────────────────┐    ││
│  │  │ [7D Price Chart Image]      │    ││
│  │  │ (loaded from chart_url)     │    ││
│  │  └─────────────────────────────┘    ││
│  │                                     ││
│  │  Sentiment: 🟢 Bullish (0.78)      ││
│  │  Fear & Greed: 72 — Greed          ││
│  │                                     ││
│  │  Signals:                           ││
│  │  ● CoinGecko    🟢 +5.2% 24h      ││
│  │  ● Fear & Greed 🟢 72/100         ││
│  │  ● Twitter      🟢 67% positive   ││
│  │  ● Reddit       🟢 Bullish posts  ││
│  │  ● On-chain     🟢 Net outflows   ││
│  └─────────────────────────────────────┘│
│                                         │
│  Bitcoin showing strong bullish         │
│  momentum with institutional buying     │
│  pressure and positive social...        │
└─────────────────────────────────────────┘
```

---

## Open Items

- [ ] On-chain data provider selection (Alchemy vs Dune vs Nansen)
- [ ] Twitter/Reddit real API vs Perplexity Sonar approximation
- [ ] Chart rendering: SVG sparkline vs full candlestick
- [ ] Historical sentiment tracking (store scores in TimescaleDB)
- [ ] Sentiment alerts: notify user when score flips direction
- [ ] Multi-token comparison: "compare BTC vs ETH sentiment"
