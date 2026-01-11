# Guest Chat User Guide

**Welcome to Anvil's Guest Chat!** 🚀

Experience the power of AI-driven DeFi intelligence without creating an account. This guide will help you get the most out of your guest chat experience.

## Table of Contents

1. [What is Guest Chat?](#what-is-guest-chat)
2. [Getting Started](#getting-started)
3. [Available Features](#available-features)
4. [DeFi Shortcuts](#defi-shortcuts)
5. [Hunter AI Features](#hunter-ai-features)
6. [GraphRAG Protocol Intelligence](#graphrag-protocol-intelligence)
7. [Multi-Language Support](#multi-language-support)
8. [Rate Limits](#rate-limits)
9. [Upgrading to Full Access](#upgrading-to-full-access)
10. [Example Queries](#example-queries)

---

## What is Guest Chat?

Guest Chat lets you explore Anvil's AI-powered DeFi assistant without signing up. You'll get:

- ✅ **Real-time market data** from CoinGecko, Aave, Morpho, and more
- ✅ **Hunter AI insights** including sentiment analysis, price predictions, and risk signals
- ✅ **Protocol intelligence** powered by GraphRAG for smart protocol discovery
- ✅ **Multi-language support** in English, Spanish, Portuguese, and Chinese
- ✅ **Conversational UX** with emojis, formatting, and actionable insights

**What's the catch?** As a guest, you can **view and explore** all features, but you'll need to sign up to **execute transactions** like swaps, lending, or purchases.

---

## Getting Started

### Making Your First Query

Simply send a message to the guest chat endpoint:

```bash
POST /api/v1/guest/chat
{
  "content": "What's the sentiment for BTC?",
  "language": "en"
}
```

**No API key required!** Just start chatting.

### Understanding Responses

Every response includes:

1. **Agent Message**: The conversational response with rich formatting
2. **Enrichment Data**: Structured data (prices, APY, scores, etc.)
3. **Registration Info**: Whether you need to sign up for the action

Example response:

```json
{
  "agent_message": {
    "content": "📊 **BTC Sentiment Analysis**\n\n✅ **Overall**: Bullish (0.72)\n\n..."
  },
  "enrichment": {
    "token": "BTC",
    "overall_score": 0.72,
    "classification": "bullish",
    "sources": {...}
  },
  "registration_required": {
    "required": false
  }
}
```

---

## Available Features

### 🎯 DeFi Shortcuts

Quick actions for common DeFi operations:

| Feature | Description | Example Query |
|---------|-------------|---------------|
| **SWAP** | Get real-time swap quotes from 1inch | "Swap 100 USDC to ETH" |
| **BUY** | View crypto prices from CoinGecko | "Buy $500 of BTC" |
| **LENDING** | Compare Morpho vault APY rates | "Lend 1000 USDC" |
| **MONEY_MARKET** | Compare Aave/Compound/Morpho rates | "Best rates for USDC" |
| **BALANCE** | Learn about wallet balances | "Show my balance" |
| **PORTFOLIO** | Preview portfolio features (demo) | "Show my portfolio" |
| **ACTIVITY** | Preview transaction history (demo) | "Recent activity" |
| **SEND** | Learn how to send crypto | "Send ETH to a friend" |
| **RECEIVE** | Learn how to receive crypto | "How do I receive USDC?" |

**Note:** All features show **real data** from live protocols. Portfolio and Activity show demo data for preview since guests don't have wallets yet.

### 🔍 Hunter AI Features

Advanced AI-powered market intelligence:

| Feature | Description | Example Query |
|---------|-------------|---------------|
| **SENTIMENT** | Analyze social sentiment from Twitter/Reddit/Discord/News | "ETH sentiment analysis" |
| **PRICE_PREDICTION** | LSTM-based price forecasting for multiple timeframes | "BTC price prediction" |
| **RISK_SIGNALS** | Market risk warnings and indicators | "Risk signals for SOL" |
| **TRADING_SIGNALS** | Buy/sell signal recommendations with technical analysis | "Trading signals for ETH" |
| **PATTERNS** | Chart pattern detection and analysis | "BTC chart patterns" |
| **PORTFOLIO_OPTIMIZATION** | Portfolio allocation and diversification suggestions | "Optimize my crypto portfolio" |

**Data Sources:** Real-time data from CoinGecko, RSS news feeds (CoinDesk, CoinTelegraph), and market APIs.

### 🕸️ GraphRAG Protocol Intelligence

Smart protocol discovery powered by knowledge graphs:

| Feature | Description | Example Query |
|---------|-------------|---------------|
| **PROTOCOL_SEARCH** | Find and compare DeFi protocols | "Find me lending protocols" |
| **RISK_ASSESSMENT** | Protocol security and audit analysis | "Is Aave safe to use?" |
| **SIMILAR_PROTOCOLS** | Discover protocol alternatives | "Protocols like Compound" |

**Knowledge Base:** Real protocol data including TVL, audits, features, and security history.

---

## DeFi Shortcuts

### 💱 SWAP - Token Swapping

**What it does:** Get real-time swap quotes from 1inch aggregator.

**Example queries:**
- "Swap 100 USDC to ETH"
- "How much ETH can I get for 500 USDC?"
- "Best swap rate for USDC to SOL"

**What you'll get:**
- Real-time price from 1inch
- Amount you'll receive after fees
- Exchange rate
- Slippage protection information

**Guest experience:** View quotes and compare rates. Sign up to execute swaps.

---

### 💰 BUY - Purchase Crypto

**What it does:** View real-time crypto prices and purchase quotes.

**Example queries:**
- "Buy $500 of BTC"
- "How much BTC can I buy with $1000?"
- "ETH price now"

**What you'll get:**
- Real-time price from CoinGecko
- Amount of crypto you'll receive
- Total cost breakdown
- Purchase guidance

**Guest experience:** See live prices and quotes. Sign up to complete purchases.

---

### 🏦 LENDING - Earn Yield

**What it does:** Compare top Morpho vault APY rates for lending.

**Example queries:**
- "Lend 1000 USDC"
- "Best lending rates for ETH"
- "What's the APY for DAI?"

**What you'll get:**
- Real-time APY from top Morpho vaults
- Projected earnings
- Vault details and safety information
- Deposit instructions

**Guest experience:** View real APY rates. Sign up to deposit and earn.

---

### 📊 MONEY_MARKET - Compare Rates

**What it does:** Compare lending/borrowing rates across Aave, Compound, and Morpho.

**Example queries:**
- "Best rates for USDC"
- "Compare lending rates"
- "Where can I get the best APY?"

**What you'll get:**
- Side-by-side comparison of protocols
- Best supply and borrow rates
- Protocol recommendations
- Real-time APY data

**Guest experience:** Compare all rates. Sign up to use protocols.

---

### 📈 PORTFOLIO - View Holdings

**What it does:** Preview portfolio tracking features with demo data.

**Example queries:**
- "Show my portfolio"
- "What are my holdings?"
- "Portfolio value"

**What you'll get:**
- Demo portfolio with sample holdings
- Total value calculation
- Asset breakdown
- Feature preview

**Guest experience:** See how portfolio tracking works with demo data. Sign up to track your real portfolio.

---

### 🧾 ACTIVITY - Transaction History

**What it does:** Preview transaction history features with demo data.

**Example queries:**
- "Recent activity"
- "Show my transactions"
- "Transaction history"

**What you'll get:**
- Demo transactions showing the feature
- Transaction types (swap, send, receive)
- Timestamp and amount information
- Feature preview

**Guest experience:** See how transaction tracking works. Sign up to view your real transactions.

---

### 📤 SEND - Transfer Crypto

**What it does:** Learn how to send cryptocurrency.

**Example queries:**
- "Send ETH to a friend"
- "How do I transfer USDC?"
- "Send crypto"

**What you'll get:**
- Step-by-step sending guide
- Gas fee information
- Security best practices
- Wallet address format

**Guest experience:** Educational guide for sending. Sign up to send crypto.

---

### 📥 RECEIVE - Get Crypto Address

**What it does:** Learn how to receive cryptocurrency.

**Example queries:**
- "How do I receive USDC?"
- "Receive crypto"
- "What's my wallet address?"

**What you'll get:**
- Step-by-step receiving guide
- Address format information
- QR code usage
- Safety tips

**Guest experience:** Educational guide for receiving. Sign up to get your wallet address.

---

## Hunter AI Features

### 📊 SENTIMENT - Social Sentiment Analysis

**What it does:** Analyze crypto sentiment from Twitter, Reddit, Discord, and News.

**Example queries:**
- "ETH sentiment analysis"
- "What's the sentiment for BTC?"
- "Is SOL bullish or bearish?"

**What you'll get:**
- Overall sentiment score (-1 to 1)
- Classification (bullish/bearish/neutral/mixed)
- Source breakdown (Twitter, Reddit, News)
- Social volume and engagement metrics
- Key talking points

**Data sources:** Real-time data from social media and news RSS feeds.

---

### 🔮 PRICE_PREDICTION - AI Price Forecasting

**What it does:** LSTM-based price predictions for multiple timeframes.

**Example queries:**
- "BTC price prediction"
- "Where will ETH be in 30 days?"
- "SOL price forecast"

**What you'll get:**
- 24h, 7d, 30d price predictions
- Confidence levels
- Historical accuracy metrics
- Price range (low/mid/high)
- Model performance data

**Data sources:** CoinGecko historical OHLCV data for LSTM training.

**Disclaimer:** Predictions are AI estimates, not financial advice. DYOR!

---

### ⚠️ RISK_SIGNALS - Market Risk Warnings

**What it does:** Identify market risks and warning signals.

**Example queries:**
- "Risk signals for BTC"
- "Is SOL risky right now?"
- "Market risk analysis for ETH"

**What you'll get:**
- Risk level (low/medium/high/critical)
- Multiple risk indicators (volatility, liquidation, correlation)
- Market conditions analysis
- Actionable recommendations
- Risk mitigation strategies

**Data sources:** Real-time market data, volatility metrics, and liquidation data.

---

### 📈 TRADING_SIGNALS - Buy/Sell Recommendations

**What it does:** Generate buy/sell signals based on technical analysis.

**Example queries:**
- "Trading signals for BTC"
- "Should I buy ETH now?"
- "BTC buy sell signals"

**What you'll get:**
- Signal type (buy/sell/hold/neutral)
- Signal strength (strong/moderate/weak)
- Technical indicators (RSI, MACD, moving averages)
- Entry and exit points
- Stop-loss recommendations

**Data sources:** Real price and volume data from exchanges.

**Disclaimer:** Signals are AI-generated, not financial advice. Trade at your own risk!

---

### 📐 PATTERNS - Chart Pattern Detection

**What it does:** Detect and analyze chart patterns using AI.

**Example queries:**
- "BTC chart patterns"
- "What patterns do you see in ETH?"
- "SOL pattern analysis"

**What you'll get:**
- Detected patterns (head & shoulders, triangles, flags, etc.)
- Pattern confidence scores
- Timeframe analysis (1h, 4h, 1d)
- Bullish/bearish implications
- Price target projections

**Data sources:** Real chart data from exchanges.

---

### 💼 PORTFOLIO_OPTIMIZATION - Smart Allocation

**What it does:** Suggest optimal portfolio allocations and diversification.

**Example queries:**
- "Optimize my crypto portfolio"
- "Portfolio allocation strategy"
- "How should I diversify?"

**What you'll get:**
- Recommended asset allocation
- Risk tolerance assessment (conservative/moderate/aggressive)
- Diversification strategies
- Expected returns and risk metrics
- Rebalancing recommendations

**Data sources:** Real market data and volatility metrics.

---

## GraphRAG Protocol Intelligence

### 🔍 PROTOCOL_SEARCH - Find DeFi Protocols

**What it does:** Search and compare DeFi protocols using knowledge graphs.

**Example queries:**
- "Find me lending protocols"
- "Top DeFi protocols"
- "Protocols on Ethereum"
- "Compare Aave and Compound"

**What you'll get:**
- List of matching protocols
- TVL and market data
- Key features and categories
- Chain support
- Protocol comparisons

**Knowledge base:** Real protocol data from DeFi ecosystem.

---

### 🛡️ RISK_ASSESSMENT - Protocol Security

**What it does:** Analyze protocol security, audits, and risks.

**Example queries:**
- "Is Aave safe to use?"
- "Risk assessment for Compound"
- "Has Morpho been audited?"

**What you'll get:**
- Overall risk score
- Audit history and auditors
- Exploit/incident history
- Smart contract risks
- Centralization risks
- Risk mitigation recommendations

**Knowledge base:** Audit reports, security incidents, and protocol analysis.

---

### 🔄 SIMILAR_PROTOCOLS - Find Alternatives

**What it does:** Discover similar protocols and alternatives.

**Example queries:**
- "Protocols like Aave"
- "Alternatives to Compound"
- "What's similar to Uniswap?"

**What you'll get:**
- Similar protocol rankings
- Similarity scores
- Feature comparisons
- Key differences highlighted
- Use case guidance (when to use which)

**Knowledge base:** Protocol features, categories, and relationship graphs.

---

## Multi-Language Support

Guest Chat supports **4 languages**:

- 🇬🇧 **English** (`language: "en"`)
- 🇪🇸 **Spanish** (`language: "es"`)
- 🇧🇷 **Portuguese** (`language: "pt"`)
- 🇨🇳 **Chinese** (`language: "zh"`)

**Example in Spanish:**

```json
{
  "content": "sentimiento de ETH",
  "language": "es"
}
```

**Response:**

```
📊 **Análisis de Sentimiento para ETH**

✅ **General**: Alcista (0.68)
...
```

---

## Rate Limits

To ensure fair access, guest chat has the following limits:

- **20 messages per hour** per IP address
- **100 messages per day** per IP address

**What happens when you hit the limit?**

You'll receive a friendly message:

```json
{
  "error": "Rate limit exceeded",
  "message": "You've reached the hourly limit of 20 messages. Please try again in 45 minutes, or sign up for unlimited access!",
  "retry_after": 2700
}
```

**Want unlimited access?** Sign up for a free account!

---

## Upgrading to Full Access

### Why Sign Up?

Guest chat gives you a great preview, but with an account you unlock:

- ✅ **Execute transactions** - Actually swap, buy, lend, and earn
- ✅ **Real portfolio tracking** - Track your actual holdings
- ✅ **Transaction history** - View your real on-chain activity
- ✅ **Unlimited messages** - No rate limits
- ✅ **Personalized insights** - AI tailored to your portfolio
- ✅ **Advanced features** - Flash loans, arbitrage, MEV protection
- ✅ **Multi-wallet support** - Connect multiple wallets

### How to Sign Up

When you're ready, you'll see prompts like:

```
🔐 Want to execute this swap? Sign up to get started!

👉 Create your free account: https://anvil.app/signup
```

**Registration is free and takes less than 2 minutes!**

---

## Example Queries

### Quick Start Examples

**Market Data:**
- "What's the price of BTC?"
- "ETH sentiment analysis"
- "BTC price prediction"

**DeFi Operations:**
- "Swap 100 USDC to ETH"
- "Best lending rates for USDC"
- "Compare Aave and Compound"

**Risk Analysis:**
- "Risk signals for SOL"
- "Is Aave safe to use?"
- "BTC trading signals"

**Protocol Discovery:**
- "Find me yield farming protocols"
- "Protocols like Uniswap"
- "Top lending protocols on Ethereum"

**Portfolio Help:**
- "How should I diversify my portfolio?"
- "Optimize my crypto allocation"
- "What patterns do you see in ETH chart?"

### Advanced Examples

**Multi-step Queries:**
- "I want to buy $1000 of ETH and lend it on Morpho"
- "Compare sentiment, price prediction, and risk signals for BTC"
- "Find the safest lending protocol with highest APY"

**Comparative Analysis:**
- "Which has better risk profile: Aave or Compound?"
- "Compare BTC and ETH sentiment"
- "Best swap rates: 1inch vs direct DEX"

**Educational Queries:**
- "How does Morpho work?"
- "What are the risks of lending crypto?"
- "Explain head and shoulders pattern"

---

## Tips for Best Results

### 🎯 Be Specific

**Good:** "Swap 100 USDC to ETH on Polygon"
**Better than:** "Swap"

### 💬 Use Natural Language

**Good:** "What's the sentiment for BTC right now?"
**Also works:** "BTC sentiment"

### 🔄 Follow Up

Guest chat maintains context for multi-turn conversations:

```
You: "ETH sentiment"
AI: [Provides sentiment analysis]
You: "What about the price prediction?"
AI: [Provides ETH price prediction]
```

### 🌐 Use Your Language

If you're more comfortable in Spanish, use Spanish! The AI will respond in your language.

---

## Frequently Asked Questions

### Is guest chat really free?

Yes! No API keys, no credit card, no signup required to explore features.

### What data is guest chat using?

All **real data** from live sources: CoinGecko, Aave, Morpho, 1inch, news feeds, and social media. Portfolio and Activity show demo data for preview.

### Can I execute transactions as a guest?

You can **view quotes and data**, but you'll need to sign up to **execute transactions**.

### Are the AI predictions accurate?

Hunter AI uses advanced models trained on real data, but **predictions are not financial advice**. Always DYOR (Do Your Own Research)!

### How is my privacy protected?

Guest chat uses **IP-based rate limiting** only. No personal data is collected unless you sign up.

### Can I use guest chat in my app?

Yes! The guest chat API is available for integration. Contact us for API access.

---

## Getting Help

**Questions or feedback?**

- 📧 Email: support@anvilcrypto.com
- 💬 Discord: [discord.gg/anvil](https://discord.gg/anvil)
- 🐦 Twitter: [@AnvilCrypto](https://twitter.com/AnvilCrypto)

**Ready to unlock full features?**

👉 **[Sign up for free](https://anvil.app/signup)** and start executing DeFi transactions today!

---

*Last updated: 2026-01-11*
