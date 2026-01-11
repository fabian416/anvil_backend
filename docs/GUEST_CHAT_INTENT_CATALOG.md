# Guest Chat Intent Catalog

**Version:** 1.0
**Last Updated:** 2026-01-11

Complete reference of all supported intents in the Guest Chat system, with example queries, responses, and enrichment data structures.

---

## Table of Contents

### DeFi Shortcuts
1. [SWAP - Token Swapping](#1-swap---token-swapping)
2. [BUY - Purchase Crypto](#2-buy---purchase-crypto)
3. [LENDING - Yield Earning](#3-lending---yield-earning)
4. [MONEY_MARKET - Rate Comparison](#4-money_market---rate-comparison)
5. [PORTFOLIO - Holdings Tracking](#5-portfolio---holdings-tracking)
6. [ACTIVITY - Transaction History](#6-activity---transaction-history)
7. [SEND - Transfer Crypto](#7-send---transfer-crypto)
8. [RECEIVE - Get Wallet Address](#8-receive---get-wallet-address)
9. [BALANCE - Check Balance](#9-balance---check-balance)

### Hunter AI
10. [HUNTER_SENTIMENT - Sentiment Analysis](#10-hunter_sentiment---sentiment-analysis)
11. [HUNTER_PRICE_PREDICTION - Price Forecasting](#11-hunter_price_prediction---price-forecasting)
12. [HUNTER_RISK_SIGNALS - Risk Warnings](#12-hunter_risk_signals---risk-warnings)
13. [HUNTER_TRADING_SIGNALS - Buy/Sell Signals](#13-hunter_trading_signals---buysell-signals)
14. [HUNTER_PATTERNS - Chart Patterns](#14-hunter_patterns---chart-patterns)
15. [HUNTER_PORTFOLIO - Portfolio Optimization](#15-hunter_portfolio---portfolio-optimization)

### GraphRAG
16. [PROTOCOL_SEARCH - Find Protocols](#16-protocol_search---find-protocols)
17. [RISK_ASSESSMENT - Protocol Security](#17-risk_assessment---protocol-security)
18. [SIMILAR_PROTOCOLS - Find Alternatives](#18-similar_protocols---find-alternatives)

### Utility
19. [HELP - Assistant Capabilities](#19-help---assistant-capabilities)
20. [UNKNOWN - Fallback Intent](#20-unknown---fallback-intent)

---

## DeFi Shortcuts

### 1. SWAP - Token Swapping

**Description:** Get real-time token swap quotes from 1inch aggregator.

**Trigger Keywords:** swap, exchange, trade, convert

**Example Queries:**
- "Swap 100 USDC to ETH"
- "How much ETH can I get for 500 USDC?"
- "Exchange 1 ETH for USDC"
- "Trade USDC to SOL"
- "Convert 200 USDC to MATIC"

**Detection Patterns:**
```
swap [amount] [token] to [token]
exchange [amount] [token] for [token]
trade [token] to [token]
convert [amount] [token] to [token]
```

**Example Response:**

```markdown
💱 **Swap Quote: 100 USDC → ETH**

**You'll Receive:** ~0.0512 ETH

📊 **Details:**
- Exchange Rate: 1 ETH = 1,952.34 USDC
- Price Impact: 0.12%
- Gas Fee: ~$3.45 USD

**Route:** 1inch Aggregator (Best Rate)

🔐 **Sign up to execute this swap!**

*Quote valid for 60 seconds*
```

**Enrichment Schema:**

```json
{
  "from_token": "USDC",
  "to_token": "ETH",
  "from_amount": 100.0,
  "to_amount": 0.0512,
  "exchange_rate": 1952.34,
  "price_impact": 0.12,
  "gas_estimate_usd": 3.45,
  "route": "1inch",
  "slippage": 0.5,
  "quote_timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** Yes (for execution)

**Real Data:** ✅ Yes (1inch API)

---

### 2. BUY - Purchase Crypto

**Description:** View real-time crypto prices and purchase quotes.

**Trigger Keywords:** buy, purchase, get, acquire

**Example Queries:**
- "Buy $500 of BTC"
- "Purchase 1 ETH"
- "How much is BTC?"
- "Get some SOL"
- "I want to buy crypto"

**Detection Patterns:**
```
buy [amount] [token]
purchase [amount] of [token]
how much is [token]
[token] price
```

**Example Response:**

```markdown
💰 **Buy Quote: $500 → BTC**

**You'll Receive:** ~0.0108 BTC

📊 **Breakdown:**
- BTC Price: $46,200 USD
- Amount: 0.0108 BTC
- Total Cost: $500.00 USD

**Payment Methods:**
✅ Credit/Debit Card
✅ Bank Transfer
✅ Apple Pay

🔐 **Sign up to complete your purchase!**

*Price updated 30 seconds ago from CoinGecko*
```

**Enrichment Schema:**

```json
{
  "crypto": "BTC",
  "amount_usd": 500,
  "crypto_amount": 0.0108,
  "price_per_unit": 46200,
  "total_cost": 500,
  "payment_methods": ["card", "bank_transfer", "apple_pay"],
  "data_source": "coingecko",
  "price_timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** Yes (for execution)

**Real Data:** ✅ Yes (CoinGecko API)

---

### 3. LENDING - Yield Earning

**Description:** Compare top Morpho vault APY rates for lending.

**Trigger Keywords:** lend, earn, deposit, yield, interest

**Example Queries:**
- "Lend 1000 USDC"
- "Earn interest on my ETH"
- "Best yield for USDC"
- "Deposit DAI to earn"
- "What APY can I get?"

**Detection Patterns:**
```
lend [amount] [token]
earn [interest|yield] on [token]
deposit [token]
best [yield|apy] for [token]
```

**Example Response:**

```markdown
🏦 **Lending Quote: 1,000 USDC**

**Real-Time APY:** 8.5% 📈

**Projected Earnings:**
- Daily: $0.23 USDC
- Monthly: $7.08 USDC
- Yearly: $85.00 USDC

**Best Vault:** Morpho Aave USDC Optimizer
- Safety: Well-audited ✅
- Liquidity: $120M TVL
- Withdrawals: Instant

🔐 **Sign up to start earning!**

*APY updated 2 minutes ago from Morpho*
```

**Enrichment Schema:**

```json
{
  "asset": "USDC",
  "amount": 1000,
  "apy": 8.5,
  "protocol": "Morpho",
  "vault_name": "Morpho Aave USDC Optimizer",
  "vault_address": "0x...",
  "tvl": 120000000,
  "projected_earnings": {
    "daily": 0.23,
    "monthly": 7.08,
    "yearly": 85
  },
  "data_source": "morpho",
  "apy_timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** Yes (for execution)

**Real Data:** ✅ Yes (Morpho Gateway API)

---

### 4. MONEY_MARKET - Rate Comparison

**Description:** Compare lending/borrowing rates across Aave, Compound, and Morpho.

**Trigger Keywords:** rates, compare, best apy, money market

**Example Queries:**
- "Best rates for USDC"
- "Compare lending rates"
- "USDC money market rates"
- "Where can I get the best APY?"
- "Compare Aave and Compound"

**Detection Patterns:**
```
[best|compare] rates for [token]
money market [token]
[token] apy comparison
```

**Example Response:**

```markdown
📊 **Money Market Rates: USDC (Ethereum)**

**Supply Rates:**
1. 🥇 Morpho: **8.5% APY** ⭐ Best
2. 🥈 Aave: **5.2% APY**
3. 🥉 Compound: **4.8% APY**

**Borrow Rates:**
1. 🥇 Morpho: **7.5% APY** ⭐ Best
2. 🥈 Aave: **7.8% APY**
3. 🥉 Compound: **8.1% APY**

**Recommendation:** Morpho offers the best rates for both supply and borrow!

🔐 **Sign up to access these rates!**

*Updated in real-time from Aave, Compound, and Morpho APIs*
```

**Enrichment Schema:**

```json
{
  "asset": "USDC",
  "chain": "ethereum",
  "rates": {
    "aave": {
      "supply_apy": 5.2,
      "borrow_apy": 7.8,
      "utilization": 0.68
    },
    "compound": {
      "supply_apy": 4.8,
      "borrow_apy": 8.1,
      "utilization": 0.72
    },
    "morpho": {
      "supply_apy": 8.5,
      "borrow_apy": 7.5,
      "utilization": 0.75
    }
  },
  "best_supply_protocol": "morpho",
  "best_supply_apy": 8.5,
  "best_borrow_protocol": "morpho",
  "best_borrow_apy": 7.5,
  "latency_ms": 245,
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** Yes (for execution)

**Real Data:** ✅ Yes (Aave, Compound, Morpho APIs)

---

### 5. PORTFOLIO - Holdings Tracking

**Description:** Preview portfolio tracking features with demo data.

**Trigger Keywords:** portfolio, holdings, assets, my crypto

**Example Queries:**
- "Show my portfolio"
- "What are my holdings?"
- "Portfolio value"
- "My crypto assets"
- "How much crypto do I have?"

**Detection Patterns:**
```
[show|display] [my] portfolio
my [holdings|assets]
portfolio value
```

**Example Response:**

```markdown
💼 **Portfolio Overview** (Demo Preview)

**Total Value:** $12,450 USD

📊 **Holdings:**
1. BTC: 0.25 ($11,550 | 92.8%)
2. ETH: 0.5 ($976 | 7.8%)
3. USDC: 100 ($100 | 0.8%)

**24h Change:** +$325 (+2.68%) 📈

**Best Performer:** BTC (+3.2%)

💡 **This is a demo portfolio!**

🔐 **Sign up to track YOUR real portfolio!**
```

**Enrichment Schema:**

```json
{
  "total_value_usd": 12450,
  "holdings": [
    {
      "token": "BTC",
      "amount": 0.25,
      "value_usd": 11550,
      "percentage": 92.8,
      "change_24h": 3.2
    },
    {
      "token": "ETH",
      "amount": 0.5,
      "value_usd": 976,
      "percentage": 7.8,
      "change_24h": 1.5
    },
    {
      "token": "USDC",
      "amount": 100,
      "value_usd": 100,
      "percentage": 0.8,
      "change_24h": 0.0
    }
  ],
  "change_24h_usd": 325,
  "change_24h_percent": 2.68,
  "is_demo": true
}
```

**Registration Required:** Yes (to view real portfolio)

**Real Data:** ❌ No (Demo data for preview)

---

### 6. ACTIVITY - Transaction History

**Description:** Preview transaction history features with demo data.

**Trigger Keywords:** activity, transactions, history, recent

**Example Queries:**
- "Recent activity"
- "Show my transactions"
- "Transaction history"
- "What did I do recently?"
- "My recent trades"

**Detection Patterns:**
```
[recent|my] [activity|transactions]
transaction history
show [my] [trades|swaps|transfers]
```

**Example Response:**

```markdown
🧾 **Recent Activity** (Demo Preview)

**Today:**
1. 💱 Swapped 100 USDC → 0.051 ETH
   - 2 hours ago
   - Status: Completed ✅

2. 📤 Sent 0.02 BTC
   - 5 hours ago
   - To: 0x1234...5678
   - Status: Confirmed ✅

**Yesterday:**
3. 🏦 Deposited 500 USDC to Morpho
   - Earning 8.5% APY
   - Status: Active ✅

💡 **This is demo activity!**

🔐 **Sign up to view YOUR real transactions!**
```

**Enrichment Schema:**

```json
{
  "transactions": [
    {
      "type": "swap",
      "from_token": "USDC",
      "from_amount": 100,
      "to_token": "ETH",
      "to_amount": 0.051,
      "timestamp": "2026-01-11T10:00:00Z",
      "status": "completed",
      "tx_hash": "0xabc..."
    },
    {
      "type": "send",
      "token": "BTC",
      "amount": 0.02,
      "to_address": "0x1234...5678",
      "timestamp": "2026-01-11T07:00:00Z",
      "status": "confirmed",
      "tx_hash": "0xdef..."
    },
    {
      "type": "deposit",
      "token": "USDC",
      "amount": 500,
      "protocol": "Morpho",
      "apy": 8.5,
      "timestamp": "2026-01-10T15:00:00Z",
      "status": "active"
    }
  ],
  "is_demo": true
}
```

**Registration Required:** Yes (to view real transactions)

**Real Data:** ❌ No (Demo data for preview)

---

### 7. SEND - Transfer Crypto

**Description:** Learn how to send cryptocurrency.

**Trigger Keywords:** send, transfer, pay

**Example Queries:**
- "Send ETH"
- "How do I transfer USDC?"
- "Pay someone in crypto"
- "Send Bitcoin to a friend"
- "Transfer tokens"

**Detection Patterns:**
```
send [token]
transfer [token]
pay [in] [token]
how [to] send [token]
```

**Example Response:**

```markdown
📤 **How to Send Crypto**

**Step-by-Step Guide:**

1️⃣ **Get the Recipient's Address**
   - Ask for their wallet address
   - Verify it's correct (double-check!)

2️⃣ **Enter Amount**
   - Decide how much to send
   - Keep some for gas fees

3️⃣ **Review Details**
   - Recipient address
   - Amount
   - Network fee (gas)

4️⃣ **Confirm & Send**
   - Transactions are irreversible!
   - Takes 1-15 minutes

**Gas Fees:**
- Ethereum: ~$2-10 (varies)
- Polygon: ~$0.01-0.10
- Arbitrum: ~$0.10-0.50

⚠️ **Important:** Always send a small test amount first!

🔐 **Sign up to send crypto!**
```

**Enrichment Schema:**

```json
{
  "action": "send",
  "guide_steps": [
    "Get recipient address",
    "Enter amount",
    "Review details",
    "Confirm transaction"
  ],
  "gas_estimates": {
    "ethereum": {"min": 2, "max": 10},
    "polygon": {"min": 0.01, "max": 0.10},
    "arbitrum": {"min": 0.10, "max": 0.50}
  },
  "safety_tips": [
    "Verify recipient address",
    "Send test amount first",
    "Check network/chain",
    "Transactions are irreversible"
  ]
}
```

**Registration Required:** Yes (for execution)

**Real Data:** N/A (Educational content)

---

### 8. RECEIVE - Get Wallet Address

**Description:** Learn how to receive cryptocurrency.

**Trigger Keywords:** receive, get, deposit, wallet address

**Example Queries:**
- "How do I receive USDC?"
- "Receive crypto"
- "What's my wallet address?"
- "Get Bitcoin"
- "Deposit ETH"

**Detection Patterns:**
```
receive [token]
get [token]
my wallet address
how to receive [token]
```

**Example Response:**

```markdown
📥 **How to Receive Crypto**

**Step-by-Step Guide:**

1️⃣ **Get Your Wallet Address**
   - Your unique crypto address
   - Starts with 0x... (Ethereum)
   - Each network has its own address

2️⃣ **Share with Sender**
   - Copy your address (or use QR code)
   - Tell them which network (Ethereum, Polygon, etc.)

3️⃣ **Wait for Confirmation**
   - Transactions take 1-15 minutes
   - Check your wallet to confirm

4️⃣ **Funds Received!**
   - Now you can use, swap, or lend

**Address Format Examples:**
- Ethereum: 0x742d35Cc6634C0532925a3b8...
- Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv...
- Solana: 7EqQdEUa...

⚠️ **Important:** Always verify the network matches!

🔐 **Sign up to get YOUR wallet address!**
```

**Enrichment Schema:**

```json
{
  "action": "receive",
  "guide_steps": [
    "Get your wallet address",
    "Share with sender",
    "Wait for confirmation",
    "Funds received"
  ],
  "address_formats": {
    "ethereum": "0x...",
    "bitcoin": "1...",
    "solana": "..."
  },
  "confirmation_times": {
    "ethereum": "1-15 minutes",
    "bitcoin": "10-60 minutes",
    "polygon": "1-5 minutes"
  },
  "safety_tips": [
    "Verify network matches",
    "Use QR codes when possible",
    "Save address securely",
    "Check transaction status"
  ]
}
```

**Registration Required:** Yes (to get wallet address)

**Real Data:** N/A (Educational content)

---

### 9. BALANCE - Check Balance

**Description:** Learn about wallet balances.

**Trigger Keywords:** balance, check, how much

**Example Queries:**
- "Check my balance"
- "How much crypto do I have?"
- "Show balance"
- "What's in my wallet?"
- "Account balance"

**Detection Patterns:**
```
[check|show] [my] balance
how much [crypto|token] [do I have]
wallet balance
```

**Example Response:**

```markdown
💰 **About Wallet Balances**

**What is a Balance?**
Your wallet balance shows how much crypto you own across all supported tokens and networks.

**How Balances Work:**
- Real-time updates
- Shown in crypto and USD
- Separate for each network

**Example Balance View:**

**Ethereum:**
- ETH: 0.5 ($976)
- USDC: 100 ($100)

**Polygon:**
- MATIC: 200 ($130)
- USDC: 50 ($50)

**Total: $1,256 USD**

**Refresh Rate:** Balances update every 30 seconds

🔐 **Sign up to check YOUR real balance!**
```

**Enrichment Schema:**

```json
{
  "action": "balance",
  "guide_content": "How wallet balances work",
  "features": [
    "Real-time updates",
    "Multi-token support",
    "USD conversion",
    "Multi-network support"
  ],
  "refresh_rate": "30 seconds"
}
```

**Registration Required:** Yes (to view real balance)

**Real Data:** N/A (Educational content)

---

## Hunter AI

### 10. HUNTER_SENTIMENT - Sentiment Analysis

**Description:** Analyze crypto sentiment from Twitter, Reddit, Discord, and News.

**Trigger Keywords:** sentiment, feeling, mood, social, bullish, bearish

**Example Queries:**
- "ETH sentiment analysis"
- "What's the sentiment for BTC?"
- "Is SOL bullish or bearish?"
- "Market mood for crypto"
- "Social sentiment BTC"

**Detection Patterns:**
```
[token] sentiment
sentiment [analysis|for] [token]
is [token] [bullish|bearish]
market mood
```

**Example Response:**

```markdown
📊 **ETH Sentiment Analysis**

✅ **Overall: Bullish** (Score: 0.68)

**Source Breakdown:**
- 🐦 **Twitter:** Bullish (0.65)
  - 9,800 mentions in 24h
  - Trending topics: #Ethereum #ETH2.0

- 🗣️ **Reddit:** Bullish (0.72)
  - 620 discussions
  - Top subreddits: r/ethereum, r/ethtrader

- 📰 **News:** Neutral (0.60)
  - 32 articles today
  - Focus: Network upgrades, adoption

**Key Talking Points:**
✅ Upcoming network upgrades
✅ Institutional adoption increasing
✅ DeFi TVL growth
⚠️ Regulatory concerns

**Sentiment Trend:** ↗️ Improving (7-day)

*Data refreshed 5 minutes ago*
```

**Enrichment Schema:**

```json
{
  "token": "ETH",
  "overall_score": 0.68,
  "classification": "bullish",
  "sources": {
    "twitter": {
      "score": 0.65,
      "classification": "bullish",
      "volume": 9800,
      "trending_topics": ["#Ethereum", "#ETH2.0"]
    },
    "reddit": {
      "score": 0.72,
      "classification": "bullish",
      "volume": 620,
      "top_subreddits": ["r/ethereum", "r/ethtrader"]
    },
    "news": {
      "score": 0.60,
      "classification": "neutral",
      "volume": 32,
      "focus_areas": ["upgrades", "adoption"]
    }
  },
  "key_points": [
    "Upcoming network upgrades",
    "Institutional adoption increasing",
    "DeFi TVL growth"
  ],
  "trend_7d": "improving",
  "hunter_tool": "sentiment_aggregator",
  "timestamp": "2026-01-11T12:05:00Z"
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Twitter/Reddit/RSS News feeds)

---

### 11. HUNTER_PRICE_PREDICTION - Price Forecasting

**Description:** LSTM-based price predictions for multiple timeframes.

**Trigger Keywords:** prediction, forecast, price target, future price

**Example Queries:**
- "BTC price prediction"
- "Where will ETH be in 30 days?"
- "SOL price forecast"
- "Predict BTC price"
- "Future price for crypto"

**Detection Patterns:**
```
[token] price [prediction|forecast]
where will [token] be
predict [token] price
future price [for] [token]
```

**Example Response:**

```markdown
🔮 **BTC Price Prediction (LSTM Model)**

**Current Price:** $46,200

**Forecasts:**

📈 **24 Hours**
- Predicted: $46,800
- Range: $46,200 - $47,400
- Confidence: 82%

📅 **7 Days**
- Predicted: $48,500
- Range: $46,500 - $50,500
- Confidence: 71%

📆 **30 Days**
- Predicted: $52,000
- Range: $48,000 - $56,000
- Confidence: 58%

**Model Performance:**
- Historical Accuracy: 76%
- Training Data: 2 years OHLCV
- Last Updated: 1 hour ago

⚠️ **Disclaimer:** AI predictions, not financial advice. DYOR!

*Powered by LSTM deep learning model trained on CoinGecko historical data*
```

**Enrichment Schema:**

```json
{
  "token": "BTC",
  "current_price": 46200,
  "predictions": {
    "24h": {
      "price": 46800,
      "low": 46200,
      "high": 47400,
      "confidence": 0.82
    },
    "7d": {
      "price": 48500,
      "low": 46500,
      "high": 50500,
      "confidence": 0.71
    },
    "30d": {
      "price": 52000,
      "low": 48000,
      "high": 56000,
      "confidence": 0.58
    }
  },
  "model": {
    "type": "LSTM",
    "historical_accuracy": 0.76,
    "training_period": "2_years",
    "last_trained": "2026-01-11T11:00:00Z"
  },
  "hunter_tool": "lstm_price_predictor",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (CoinGecko historical OHLCV data)

---

### 12. HUNTER_RISK_SIGNALS - Risk Warnings

**Description:** Identify market risks and warning signals.

**Trigger Keywords:** risk, warning, danger, safe, risky

**Example Queries:**
- "Risk signals for BTC"
- "Is SOL risky right now?"
- "Market risk analysis for ETH"
- "Safety warnings for crypto"
- "Danger signals BTC"

**Detection Patterns:**
```
risk [signals|analysis] [for] [token]
is [token] [risky|safe]
[market] risk [for] [token]
[warning|danger] signals
```

**Example Response:**

```markdown
⚠️ **BTC Risk Signals Analysis**

**Overall Risk Level: MEDIUM** 🟡

**Active Signals:**

1. **Volatility Risk** 🟡 Medium
   - 30-day volatility: 42% (above normal)
   - Large price swings expected
   - Recommended: Reduce leverage

2. **Liquidation Risk** 🟢 Low
   - $120M liquidations at $44,000
   - Current price well above danger zone
   - Healthy distance from liquidation levels

3. **Market Correlation** 🟡 Medium
   - High correlation with stock market (0.78)
   - Macro factors impacting price
   - Monitor traditional markets

4. **Volume Risk** 🟢 Low
   - Trading volume: Healthy
   - Liquidity: Excellent
   - No volume concerns

**Recommendations:**
✅ Monitor position sizes
✅ Consider stop losses at $44,000
✅ Watch for volatility spikes
⚠️ Avoid over-leverage in current conditions

**Next Review:** 4 hours

*Real-time risk analysis powered by Hunter AI*
```

**Enrichment Schema:**

```json
{
  "token": "BTC",
  "risk_level": "medium",
  "signals": [
    {
      "type": "volatility",
      "severity": "medium",
      "value": 42,
      "threshold": 30,
      "description": "Higher than average volatility detected"
    },
    {
      "type": "liquidation_risk",
      "severity": "low",
      "liquidation_level": 44000,
      "current_price": 46200,
      "description": "Low liquidation cascade risk"
    },
    {
      "type": "market_correlation",
      "severity": "medium",
      "correlation": 0.78,
      "description": "High correlation with stock market"
    },
    {
      "type": "volume",
      "severity": "low",
      "description": "Healthy trading volume and liquidity"
    }
  ],
  "recommendations": [
    "Monitor position sizes",
    "Consider stop losses at $44,000",
    "Watch for volatility spikes",
    "Avoid over-leverage"
  ],
  "next_update": "4h",
  "hunter_tool": "risk_signal_analyzer",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Real market data, volatility metrics)

---

### 13. HUNTER_TRADING_SIGNALS - Buy/Sell Signals

**Description:** Generate buy/sell signals based on technical analysis.

**Trigger Keywords:** trading signals, buy sell, should I buy, trade

**Example Queries:**
- "Trading signals for BTC"
- "Should I buy ETH now?"
- "BTC buy sell signals"
- "Trade recommendations for SOL"
- "Is it a good time to buy?"

**Detection Patterns:**
```
trading signals [for] [token]
should I [buy|sell] [token]
[token] [buy|sell] signals
trade recommendations [for] [token]
good time to buy [token]
```

**Example Response:**

```markdown
📈 **BTC Trading Signals**

**Signal: BUY** 🟢 (Moderate Strength)

**Confidence:** 68%

**Technical Indicators:**

📊 **RSI:** 42 (Slightly Oversold)
- Below 50, room for upside
- Not extremely oversold

📈 **MACD:** Bullish Crossover ✅
- Signal line crossed above MACD
- Momentum turning positive

📉 **Moving Averages:**
- Price above 50-day MA ✅
- Below 200-day MA ⚠️
- Medium-term bullish signal

**Entry Strategy:**
- **Entry Zone:** $45,500 - $46,500
- **Target 1:** $48,000 (+4.2%)
- **Target 2:** $50,000 (+8.7%)
- **Stop Loss:** $44,000 (-4.3%)

**Risk/Reward:** 1:2.5 (Favorable)

**Timeframe:** 1-2 weeks for targets

⚠️ **Not financial advice!** Always DYOR and manage risk.

*Real-time technical analysis from Hunter AI*
```

**Enrichment Schema:**

```json
{
  "token": "BTC",
  "signal": "buy",
  "strength": "moderate",
  "confidence": 0.68,
  "current_price": 46200,
  "indicators": {
    "rsi": {
      "value": 42,
      "interpretation": "slightly_oversold",
      "signal": "bullish"
    },
    "macd": {
      "value": "bullish_crossover",
      "signal": "bullish"
    },
    "moving_averages": {
      "50_day": "above",
      "200_day": "below",
      "signal": "neutral_bullish"
    }
  },
  "entry_points": {
    "low": 45500,
    "high": 46500
  },
  "targets": [
    {"price": 48000, "gain_percent": 4.2},
    {"price": 50000, "gain_percent": 8.7}
  ],
  "stop_loss": 44000,
  "stop_loss_percent": -4.3,
  "risk_reward_ratio": 2.5,
  "timeframe": "1-2 weeks",
  "hunter_tool": "trading_signal_generator",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Real price and volume data)

---

### 14. HUNTER_PATTERNS - Chart Patterns

**Description:** Detect and analyze chart patterns using AI.

**Trigger Keywords:** pattern, chart, formation, technical analysis

**Example Queries:**
- "BTC chart patterns"
- "What patterns do you see in ETH?"
- "SOL pattern analysis"
- "Technical chart for BTC"
- "Head and shoulders pattern?"

**Detection Patterns:**
```
[token] [chart] patterns
what patterns [in] [token]
[token] pattern analysis
technical [chart|analysis] [for] [token]
[pattern_name] pattern [in] [token]
```

**Example Response:**

```markdown
📐 **BTC Chart Pattern Analysis**

**Detected Patterns:**

1️⃣ **Ascending Triangle** 📈 (4H Timeframe)
   - **Confidence:** 85%
   - **Implication:** Bullish Continuation
   - **Target:** $48,500 (+5.2%)
   - **Breakout Level:** $47,000
   - **Formation:** 85% complete

2️⃣ **Higher Lows Trend** ✅ (1D Timeframe)
   - **Confidence:** 78%
   - **Implication:** Bullish Momentum
   - **Support Zone:** $45,000 - $45,500
   - **Pattern Duration:** 12 days

**Key Levels:**
- **Resistance:** $47,000 (critical breakout)
- **Support:** $45,200 (strong)
- **Pivot:** $46,200 (current)

**Pattern Summary:**
The ascending triangle is a classic bullish continuation pattern. A breakout above $47,000 with volume could target $48,500.

**Trading Plan:**
✅ Watch for breakout above $47,000
✅ Confirm with increased volume
⚠️ Invalidated if breaks below $45,000

*Real-time pattern detection powered by Hunter AI*
```

**Enrichment Schema:**

```json
{
  "token": "BTC",
  "patterns": [
    {
      "type": "ascending_triangle",
      "timeframe": "4h",
      "confidence": 0.85,
      "implication": "bullish_continuation",
      "target_price": 48500,
      "breakout_level": 47000,
      "completion": 0.85
    },
    {
      "type": "higher_lows",
      "timeframe": "1d",
      "confidence": 0.78,
      "implication": "bullish_momentum",
      "support_zone": {"low": 45000, "high": 45500},
      "duration_days": 12
    }
  ],
  "key_levels": {
    "resistance": [47000],
    "support": [45200, 45000],
    "pivot": 46200
  },
  "trading_plan": [
    "Watch for breakout above $47,000",
    "Confirm with increased volume",
    "Invalidated if breaks below $45,000"
  ],
  "hunter_tool": "pattern_detector",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Real chart data from exchanges)

---

### 15. HUNTER_PORTFOLIO - Portfolio Optimization

**Description:** Suggest optimal portfolio allocations and diversification.

**Trigger Keywords:** portfolio optimization, allocation, diversify, rebalance

**Example Queries:**
- "Optimize my crypto portfolio"
- "Portfolio allocation strategy"
- "How should I diversify?"
- "Rebalance my portfolio"
- "Best crypto allocation"

**Detection Patterns:**
```
optimize [my] portfolio
portfolio [allocation|optimization]
how [should I|to] diversify
rebalance portfolio
best [crypto] allocation
```

**Example Response:**

```markdown
💼 **Portfolio Optimization Strategy**

**Risk Profile:** Moderate

**Recommended Allocation:**

1. **BTC - 40%** (Core Holding)
   - Least volatile
   - Store of value
   - Portfolio anchor

2. **ETH - 30%** (Growth)
   - DeFi ecosystem
   - Strong fundamentals
   - Higher growth potential

3. **USDC - 20%** (Stability)
   - Stablecoin buffer
   - Earn yield (8.5% APY)
   - Reduced volatility

4. **SOL - 10%** (Higher Risk/Reward)
   - Layer 1 growth play
   - Higher volatility
   - Diversification

**Expected Performance:**
- **Annual Return:** 18-25%
- **Volatility:** 32%
- **Sharpe Ratio:** 0.68
- **Max Drawdown:** -28%

**Diversification Score:** 7.5/10 ✅

**Rebalancing:**
- Review quarterly
- Rebalance when any asset ±5% from target
- Take profits during run-ups

**Risk Management:**
✅ Never all-in on one asset
✅ Keep stablecoin buffer (15-25%)
✅ Set stop-losses for volatile assets
⚠️ Only invest what you can afford to lose

🔐 **Sign up to implement this strategy!**

*Recommendations based on current market conditions*
```

**Enrichment Schema:**

```json
{
  "risk_profile": "moderate",
  "recommended_allocation": [
    {
      "asset": "BTC",
      "percentage": 40,
      "rationale": "Core holding, least volatile, store of value"
    },
    {
      "asset": "ETH",
      "percentage": 30,
      "rationale": "DeFi ecosystem, strong fundamentals"
    },
    {
      "asset": "USDC",
      "percentage": 20,
      "rationale": "Stability, earn yield, reduced volatility"
    },
    {
      "asset": "SOL",
      "percentage": 10,
      "rationale": "Higher risk/reward, diversification"
    }
  ],
  "expected_performance": {
    "annual_return": {"low": 18, "high": 25},
    "volatility": 32,
    "sharpe_ratio": 0.68,
    "max_drawdown": -28
  },
  "diversification_score": 7.5,
  "rebalancing": {
    "frequency": "quarterly",
    "threshold": 5
  },
  "risk_management": [
    "Never all-in on one asset",
    "Keep 15-25% in stablecoins",
    "Set stop-losses for volatile assets",
    "Only invest what you can afford to lose"
  ],
  "hunter_tool": "portfolio_optimizer",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Registration Required:** Yes (for implementation)

**Real Data:** ✅ Yes (Real market data and volatility metrics)

---

## GraphRAG

### 16. PROTOCOL_SEARCH - Find Protocols

**Description:** Search and compare DeFi protocols using knowledge graphs.

**Trigger Keywords:** find protocol, search, discover, compare protocols

**Example Queries:**
- "Find me lending protocols"
- "Top DeFi protocols"
- "Protocols on Ethereum"
- "Compare Aave and Compound"
- "Best DEX protocols"

**Detection Patterns:**
```
find [me] [category] protocols
[top|best] [defi|category] protocols
protocols on [chain]
compare [protocol] and [protocol]
search [for] protocols
```

**Example Response:**

```markdown
🔍 **Top Lending Protocols**

1. **Aave** - $12.5B TVL 🥇
   - **Chains:** Ethereum, Polygon, Arbitrum, Optimism
   - **Features:** Flash loans, Collateral swap, GHO stablecoin
   - **Safety:** 15+ audits ✅
   - **APY Range:** 3-12% (supply)

2. **Compound** - $8.2B TVL 🥈
   - **Chains:** Ethereum
   - **Features:** Governance (COMP), Proven track record
   - **Safety:** 10+ audits ✅
   - **APY Range:** 2-10% (supply)

3. **Morpho** - $2.1B TVL 🥉
   - **Chains:** Ethereum
   - **Features:** P2P matching, Higher yields, Built on Aave/Compound
   - **Safety:** 5+ audits ✅
   - **APY Range:** 5-15% (supply)

**Quick Comparison:**
- **Best TVL:** Aave
- **Most Chains:** Aave
- **Best Rates:** Morpho
- **Most Established:** Compound

💡 **Want specific rates?** Try: "Compare rates for USDC"

*Data from DeFi protocols via GraphRAG*
```

**Enrichment Schema:**

```json
{
  "query": "lending protocols",
  "protocols": [
    {
      "name": "Aave",
      "category": "lending",
      "tvl": 12500000000,
      "chains": ["ethereum", "polygon", "arbitrum", "optimism"],
      "features": ["flash_loans", "collateral_swap", "gho_stablecoin"],
      "audits": 15,
      "apy_range": {"min": 3, "max": 12},
      "website": "aave.com"
    },
    {
      "name": "Compound",
      "category": "lending",
      "tvl": 8200000000,
      "chains": ["ethereum"],
      "features": ["governance", "proven_track_record"],
      "audits": 10,
      "apy_range": {"min": 2, "max": 10},
      "website": "compound.finance"
    },
    {
      "name": "Morpho",
      "category": "lending",
      "tvl": 2100000000,
      "chains": ["ethereum"],
      "features": ["p2p_matching", "optimized_yields"],
      "audits": 5,
      "apy_range": {"min": 5, "max": 15},
      "website": "morpho.org"
    }
  ],
  "comparison": {
    "best_tvl": "Aave",
    "most_chains": "Aave",
    "best_rates": "Morpho",
    "most_established": "Compound"
  }
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Real protocol data via GraphRAG)

---

### 17. RISK_ASSESSMENT - Protocol Security

**Description:** Analyze protocol security, audits, and risks.

**Trigger Keywords:** safe, security, audit, risk assessment, hack

**Example Queries:**
- "Is Aave safe to use?"
- "Risk assessment for Compound"
- "Has Morpho been audited?"
- "Security analysis for Uniswap"
- "Was Aave hacked?"

**Detection Patterns:**
```
is [protocol] safe
[risk|security] assessment [for] [protocol]
has [protocol] been [audited|hacked]
[security] analysis [for] [protocol]
```

**Example Response:**

```markdown
🛡️ **Aave Security Assessment**

**Overall Risk Score: 2.5/10** 🟢 (Low Risk)

**Security Profile:**

✅ **Audit History:** Excellent
- 15+ comprehensive audits
- Auditors: OpenZeppelin, Trail of Bits, Consensys, ABDK
- Most recent: September 2023
- **Findings:** No critical vulnerabilities

✅ **Track Record:** Strong
- **Launched:** 2020
- **Exploits:** 0 major hacks
- **Uptime:** 99.9%
- **Bug Bounty:** Active ($250K max payout)

✅ **Decentralization:**
- **Governance:** DAO-controlled
- **Multi-sig:** 6 of 10 required
- **Upgrade Control:** Time-locked

⚠️ **Risk Factors:**
- Smart contract complexity (high)
- Oracle dependency (Chainlink)
- Liquidation cascades (market risk)

**Recommendations:**
✅ Well-audited and battle-tested
✅ Suitable for most risk tolerances
✅ Consider diversifying across protocols
⚠️ Always understand liquidation risks

**Safety Rating: 9/10** ⭐⭐⭐⭐⭐

*Security assessment powered by GraphRAG knowledge base*
```

**Enrichment Schema:**

```json
{
  "protocol": "Aave",
  "risk_score": 2.5,
  "risk_level": "low",
  "audits": [
    {
      "auditor": "OpenZeppelin",
      "date": "2023-09-15",
      "findings": "No critical issues",
      "report_url": "https://..."
    },
    {
      "auditor": "Trail of Bits",
      "date": "2023-06-20",
      "findings": "1 medium, 3 low",
      "report_url": "https://..."
    }
  ],
  "track_record": {
    "launched": "2020-01-01",
    "major_exploits": 0,
    "uptime": 0.999,
    "bug_bounty": {
      "active": true,
      "max_payout": 250000
    }
  },
  "decentralization": {
    "governance": "DAO",
    "multisig": "6_of_10",
    "upgrade_control": "time_locked"
  },
  "risk_factors": [
    {
      "type": "smart_contract_complexity",
      "severity": "medium",
      "description": "Complex codebase increases audit surface"
    },
    {
      "type": "oracle_dependency",
      "severity": "low",
      "description": "Relies on Chainlink oracles"
    },
    {
      "type": "liquidation_cascades",
      "severity": "medium",
      "description": "Market volatility can trigger cascades"
    }
  ],
  "recommendations": [
    "Well-audited and battle-tested",
    "Suitable for most risk tolerances",
    "Consider diversifying across protocols",
    "Understand liquidation risks"
  ],
  "safety_rating": 9
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Audit reports, security data)

---

### 18. SIMILAR_PROTOCOLS - Find Alternatives

**Description:** Discover similar protocols and alternatives.

**Trigger Keywords:** similar, alternative, like, compare to

**Example Queries:**
- "Protocols like Aave"
- "Alternatives to Compound"
- "What's similar to Uniswap?"
- "Compare Morpho to Aave"
- "Other protocols like Curve"

**Detection Patterns:**
```
protocols [like|similar to] [protocol]
alternatives to [protocol]
what's [similar|like] [protocol]
compare [protocol] to [protocol]
other protocols like [protocol]
```

**Example Response:**

```markdown
🔄 **Protocols Similar to Aave**

**Top Alternatives:**

1. **Compound** - Similarity: 92% 🥇
   - **Category:** Lending
   - **TVL:** $8.2B
   - **Similarities:**
     - Over-collateralized lending
     - Algorithmic interest rates
     - Ethereum-native
   - **Differences:**
     - ❌ No flash loans
     - ✅ Simpler codebase
     - ✅ COMP governance token

2. **Morpho** - Similarity: 85% 🥈
   - **Category:** Lending
   - **TVL:** $2.1B
   - **Similarities:**
     - Builds on Aave/Compound
     - Over-collateralized lending
     - Ethereum-native
   - **Differences:**
     - ✅ P2P matching layer
     - ✅ Higher yields
     - ⚠️ Newer protocol (less battle-tested)

3. **Euler** - Similarity: 78% 🥉
   - **Category:** Lending
   - **TVL:** $1.5B
   - **Similarities:**
     - Permissionless lending
     - Flash loans supported
   - **Differences:**
     - ✅ Any ERC-20 can be listed
     - ⚠️ More complex risk model
     - ⚠️ Less audited

**When to Use Each:**

- **Aave:** Multi-chain support, flash loans, most features
- **Compound:** Simplicity, proven track record, governance
- **Morpho:** Best rates, efficiency-focused
- **Euler:** Niche tokens, permissionless listings

*Protocol comparison powered by GraphRAG knowledge graph*
```

**Enrichment Schema:**

```json
{
  "base_protocol": "Aave",
  "similar_protocols": [
    {
      "name": "Compound",
      "similarity_score": 0.92,
      "category": "lending",
      "tvl": 8200000000,
      "similarities": [
        "Over-collateralized lending",
        "Algorithmic interest rates",
        "Ethereum-native"
      ],
      "differences": [
        {"feature": "flash_loans", "aave": true, "compound": false},
        {"feature": "complexity", "aave": "high", "compound": "medium"},
        {"feature": "governance", "aave": "AAVE", "compound": "COMP"}
      ]
    },
    {
      "name": "Morpho",
      "similarity_score": 0.85,
      "category": "lending",
      "tvl": 2100000000,
      "similarities": [
        "Builds on Aave/Compound",
        "Over-collateralized lending",
        "Ethereum-native"
      ],
      "differences": [
        {"feature": "matching_layer", "aave": false, "morpho": true},
        {"feature": "yields", "aave": "standard", "morpho": "optimized"},
        {"feature": "maturity", "aave": "battle-tested", "morpho": "newer"}
      ]
    },
    {
      "name": "Euler",
      "similarity_score": 0.78,
      "category": "lending",
      "tvl": 1500000000,
      "similarities": [
        "Permissionless lending",
        "Flash loans supported"
      ],
      "differences": [
        {"feature": "listings", "aave": "curated", "euler": "permissionless"},
        {"feature": "risk_model", "aave": "standard", "euler": "advanced"},
        {"feature": "audits", "aave": "15+", "euler": "5+"}
      ]
    }
  ],
  "use_cases": {
    "aave": "Multi-chain support, flash loans, most features",
    "compound": "Simplicity, proven track record, governance",
    "morpho": "Best rates, efficiency-focused",
    "euler": "Niche tokens, permissionless listings"
  }
}
```

**Registration Required:** No (viewing only)

**Real Data:** ✅ Yes (Protocol data via GraphRAG)

---

## Utility

### 19. HELP - Assistant Capabilities

**Description:** Show what the assistant can do.

**Trigger Keywords:** help, what can you do, capabilities, features

**Example Queries:**
- "What can you do?"
- "Help me"
- "Show features"
- "What are your capabilities?"
- "How can you help?"

**Detection Patterns:**
```
what can you do
help [me]
[show|list] [features|capabilities]
how can you help
```

**Example Response:**

```markdown
👋 **Welcome to Anvil Guest Chat!**

I'm your AI-powered DeFi assistant. Here's what I can do:

**💱 DeFi Operations:**
- Get swap quotes (1inch)
- View crypto prices (CoinGecko)
- Compare lending rates (Aave, Compound, Morpho)
- Learn about sending/receiving crypto

**🔍 Hunter AI Intelligence:**
- Sentiment analysis (Twitter, Reddit, News)
- Price predictions (LSTM AI model)
- Risk signals and warnings
- Trading signals (buy/sell recommendations)
- Chart pattern detection
- Portfolio optimization advice

**🕸️ Protocol Discovery:**
- Search DeFi protocols
- Security assessments
- Find protocol alternatives
- Compare features and risks

**🌐 Multi-Language:**
- English, Spanish, Portuguese, Chinese

**Try These Examples:**
- "What's the sentiment for BTC?"
- "Swap 100 USDC to ETH"
- "Find me lending protocols"
- "BTC price prediction"
- "Compare Aave and Compound"

💬 Just ask me anything about DeFi!

🔐 **Sign up for unlimited access and transaction execution!**
```

**Enrichment Schema:**

```json
{
  "intent": "help",
  "capabilities": {
    "defi_shortcuts": [
      "SWAP", "BUY", "LENDING", "MONEY_MARKET",
      "PORTFOLIO", "ACTIVITY", "SEND", "RECEIVE", "BALANCE"
    ],
    "hunter_ai": [
      "SENTIMENT", "PRICE_PREDICTION", "RISK_SIGNALS",
      "TRADING_SIGNALS", "PATTERNS", "PORTFOLIO_OPTIMIZATION"
    ],
    "graphrag": [
      "PROTOCOL_SEARCH", "RISK_ASSESSMENT", "SIMILAR_PROTOCOLS"
    ],
    "languages": ["en", "es", "pt", "zh"]
  },
  "example_queries": [
    "What's the sentiment for BTC?",
    "Swap 100 USDC to ETH",
    "Find me lending protocols",
    "BTC price prediction",
    "Compare Aave and Compound"
  ]
}
```

**Registration Required:** No

**Real Data:** N/A (Informational)

---

### 20. UNKNOWN - Fallback Intent

**Description:** Handles unrecognized queries gracefully.

**Trigger Keywords:** N/A (catches all unrecognized queries)

**Example Queries:**
- "Hello"
- "Tell me a joke"
- Random unrelated content

**Detection Patterns:**
```
Any query that doesn't match known intents
```

**Example Response:**

```markdown
👋 **Hi there!**

I didn't quite understand that. I'm specialized in DeFi and crypto!

**I can help you with:**

💱 **DeFi Operations**
- "Swap 100 USDC to ETH"
- "Best lending rates for USDC"

🔍 **Market Intelligence**
- "BTC sentiment analysis"
- "ETH price prediction"

🕸️ **Protocol Discovery**
- "Find me lending protocols"
- "Is Aave safe?"

**Try one of these, or just ask me anything crypto-related!**

Need help? Type "What can you do?"
```

**Enrichment Schema:**

```json
{
  "intent": "unknown",
  "confidence": 0.0,
  "suggestions": [
    "Try asking about crypto prices, swaps, or lending",
    "Ask for sentiment analysis or price predictions",
    "Search for DeFi protocols",
    "Type 'help' for full capabilities"
  ]
}
```

**Registration Required:** No

**Real Data:** N/A (Informational)

---

## Appendix

### Intent Detection Confidence Thresholds

| Confidence Range | Interpretation | Action |
|-----------------|----------------|--------|
| 0.9 - 1.0 | Very High | Execute intent directly |
| 0.7 - 0.9 | High | Execute with minor validation |
| 0.5 - 0.7 | Medium | Ask for clarification |
| 0.0 - 0.5 | Low | Show UNKNOWN/HELP response |

### Multi-Language Support

All intents support 4 languages:
- **English** (`en`) - Default
- **Spanish** (`es`) - Full translation
- **Portuguese** (`pt`) - Full translation
- **Chinese** (`zh`) - Full translation

### Rate Limiting by Intent

All intents share the same rate limit pool:
- 20 requests per hour per IP
- 100 requests per day per IP

### Real Data Sources

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| Token Prices | CoinGecko API | 30 seconds |
| Swap Quotes | 1inch API | Real-time (60s validity) |
| Lending APY | Morpho Gateway | 5 minutes |
| Money Market Rates | Aave/Compound/Morpho APIs | 5 minutes |
| Sentiment Data | Twitter/Reddit/RSS News | 5-10 minutes |
| Historical OHLCV | CoinGecko API | Daily |
| Protocol Data | GraphRAG Knowledge Base | Weekly |
| Audit Reports | Manual curation | As released |

---

**Questions or feedback?**

📧 Email: support@anvilcrypto.com
📚 Docs: [docs.anvil.app](https://docs.anvil.app)
💬 Discord: [discord.gg/anvil](https://discord.gg/anvil)

---

*Intent Catalog Version 1.0 - Last Updated: 2026-01-11*
