# Unified Chat Endpoint - Input/Output Examples

Complete reference guide showing input messages and expected outputs for all 16 intent types supported by the unified chat routing system.

**Endpoint**: `POST /api/v1/user/chat/conversations/{conversation_id}/messages`

**Authentication**: Required (Bearer token)

---

## Table of Contents

1. [GraphRAG Intents](#1-graphrag-intents)
   - [Protocol Search](#11-protocol-search)
   - [Risk Assessment](#12-risk-assessment)
   - [Similar Protocols](#13-similar-protocols)
2. [Hunter AI Intents](#2-hunter-ai-intents)
   - [Sentiment Analysis](#21-sentiment-analysis)
   - [Price Prediction](#22-price-prediction)
   - [Risk Signals](#23-risk-signals)
   - [Trading Signals](#24-trading-signals)
   - [Pattern Detection](#25-pattern-detection)
   - [Portfolio Optimization](#26-portfolio-optimization)
3. [ULTRA Intents](#3-ultra-intents)
   - [Arbitrage Discovery](#31-arbitrage-discovery)
   - [Flash Loan Selection](#32-flash-loan-selection)
   - [MEV Protection](#33-mev-protection)
   - [Auto Executor Control](#34-auto-executor-control)
4. [Agent Squad & Chat Intents](#4-agent-squad--chat-intents)
   - [Specialist Task](#41-specialist-task)
   - [Complex Workflow](#42-complex-workflow)
   - [General Conversation](#43-general-conversation)

---

## 1. GraphRAG Intents

### 1.1. Protocol Search

**Intent**: Find DeFi protocols based on criteria (category, chain, TVL, risk, etc.)

**Input**:
```json
{
  "content": "Show me high-yield staking protocols on Ethereum with low risk"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Show me high-yield staking protocols on Ethereum with low risk",
    "created_at": "2025-12-26T10:30:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "🔍 **Protocol Search Results**\n\nFound 5 protocols matching your criteria:\n\n**1. Lido Finance**\n- Category: Liquid Staking\n- Chain: Ethereum\n- TVL: $23.4B\n- APY: 3.8%\n- Risk Score: 2.1/10 (Low)\n- Security: Audited by multiple firms\n\n**2. Rocket Pool**\n- Category: Decentralized Staking\n- Chain: Ethereum\n- TVL: $2.1B\n- APY: 3.5%\n- Risk Score: 2.3/10 (Low)\n- Security: Non-custodial, audited\n\n...",
    "agent_type": "graphrag_search",
    "created_at": "2025-12-26T10:30:02Z"
  },
  "routing": {
    "intent": "protocol_search",
    "confidence": 0.95,
    "handler": "graphrag_search",
    "reasoning": "User query contains protocol discovery keywords with risk and yield filters",
    "total_latency_ms": 1245
  },
  "enrichment": {
    "protocols": [
      {
        "protocol_id": "lido",
        "protocol_name": "Lido Finance",
        "tvl": 23400000000,
        "apy": 3.8,
        "risk_score": 2.1,
        "category": "Liquid Staking"
      }
    ],
    "search_context": "Filtered for low-risk staking protocols on Ethereum with high yields",
    "recommendations": [
      "Lido Finance offers the highest TVL and institutional trust",
      "Rocket Pool provides decentralized node operation"
    ]
  }
}
```

**Other Example Queries**:
- "Find lending protocols with TVL > $1B"
- "Show me all DEXes on Arbitrum"
- "What are the safest yield farming protocols?"

---

### 1.2. Risk Assessment

**Intent**: Analyze the safety and risk factors of a specific protocol

**Input**:
```json
{
  "content": "Is Aave safe to use? What are the risks?"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Is Aave safe to use? What are the risks?",
    "created_at": "2025-12-26T10:31:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440003",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "⚠️ **Risk Analysis: Aave**\n\n**Overall Risk Score**: 2.8/10 (Low Risk)\n\n**Risk Factors**:\n\n✅ **Smart Contract Risk** (Low)\n- Multiple audits by Trail of Bits, OpenZeppelin, Consensys\n- Bug bounty program active ($250k rewards)\n- 5+ years of operation without major exploits\n\n✅ **Liquidity Risk** (Very Low)\n- TVL: $8.2B across all markets\n- Deep liquidity pools\n- Diverse collateral types\n\n⚠️ **Oracle Risk** (Medium-Low)\n- Depends on Chainlink oracles\n- Mitigated by redundant price feeds\n\n💼 **Governance Risk** (Low)\n- Decentralized governance via AAVE token\n- Time-locked upgrades\n- Multi-sig controls\n\n**Safer Alternatives**:\n1. Compound (Risk: 2.5/10) - Simpler design, established track record\n2. MakerDAO (Risk: 2.3/10) - More conservative, over-collateralized\n\n**Recommendation**: Aave is considered safe for amounts up to $100k per position. Consider diversifying across multiple protocols for larger amounts.",
    "agent_type": "graphrag_risk",
    "created_at": "2025-12-26T10:31:03Z"
  },
  "routing": {
    "intent": "risk_assessment",
    "confidence": 0.93,
    "handler": "graphrag_risk",
    "reasoning": "User asking about protocol safety and risk factors",
    "total_latency_ms": 1850
  },
  "enrichment": {
    "risk_analysis": {
      "protocol_name": "Aave",
      "overall_risk_score": 2.8,
      "risk_level": "low",
      "smart_contract_risk": 2.5,
      "liquidity_risk": 1.8,
      "oracle_risk": 3.5,
      "governance_risk": 2.0
    },
    "alternatives_count": 2
  }
}
```

**Other Example Queries**:
- "How risky is Curve Finance?"
- "Assess the security of Uniswap V3"
- "What are the dangers of using Yearn Finance?"

---

### 1.3. Similar Protocols

**Intent**: Find protocols similar to a given protocol

**Input**:
```json
{
  "content": "What protocols are similar to Uniswap?"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "What protocols are similar to Uniswap?",
    "created_at": "2025-12-26T10:32:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440005",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "🔄 **Protocols Similar to Uniswap**\n\n**Base Protocol**: Uniswap V3\n- Category: DEX (Automated Market Maker)\n- TVL: $4.2B\n- Risk Score: 2.5/10\n\n**Similar Protocols**:\n\n**1. SushiSwap** (Similarity: 92%)\n- TVL: $1.1B\n- Risk: 3.2/10\n- Why Similar: Fork of Uniswap V2, same AMM model\n- Key Difference: Additional features (lending, staking rewards)\n\n**2. PancakeSwap** (Similarity: 88%)\n- TVL: $2.8B\n- Risk: 3.5/10\n- Why Similar: Uniswap clone on BNB Chain\n- Key Difference: Lower fees, different chain\n\n**3. Curve Finance** (Similarity: 75%)\n- TVL: $3.5B\n- Risk: 2.8/10\n- Why Similar: Automated market maker\n- Key Difference: Optimized for stablecoin swaps\n\n**4. Balancer** (Similarity: 72%)\n- TVL: $1.2B\n- Risk: 3.0/10\n- Why Similar: AMM with programmable pools\n- Key Difference: Multi-asset pools, custom weights",
    "agent_type": "graphrag_similar",
    "created_at": "2025-12-26T10:32:02Z"
  },
  "routing": {
    "intent": "similar_protocols",
    "confidence": 0.96,
    "handler": "graphrag_similar",
    "reasoning": "User searching for protocol alternatives/comparisons",
    "total_latency_ms": 1420
  },
  "enrichment": {
    "base_protocol": {
      "protocol_id": "uniswap-v3",
      "protocol_name": "Uniswap V3",
      "tvl": 4200000000,
      "category": "DEX"
    },
    "similar_protocols": [
      {
        "protocol_id": "sushiswap",
        "protocol_name": "SushiSwap",
        "similarity_score": 0.92,
        "tvl": 1100000000,
        "why_similar": "Fork of Uniswap V2 with same AMM model"
      }
    ]
  }
}
```

**Other Example Queries**:
- "Find alternatives to Compound"
- "What's like MakerDAO but simpler?"
- "Show me Aave competitors"

---

## 2. Hunter AI Intents

### 2.1. Sentiment Analysis

**Intent**: Aggregate social media and news sentiment for a token

**Input**:
```json
{
  "content": "What's the ETH sentiment on Twitter and Reddit?"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440006",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "What's the ETH sentiment on Twitter and Reddit?",
    "created_at": "2025-12-26T10:33:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440007",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "📊 **Sentiment Analysis for ETH**\n\n**Overall Sentiment:** Bullish (72/100)\n**Confidence:** 85%\n\n**Source Breakdown:**\n\n🐦 **Twitter** (68/100 - Bullish)\n- Volume: 45,230 mentions (24h)\n- Positive: 58%\n- Neutral: 32%\n- Negative: 10%\n- Top Topics: \"ETH 2.0 upgrade\", \"DeFi growth\", \"institutional adoption\"\n\n📱 **Reddit** (75/100 - Bullish)\n- Subreddits: r/ethereum, r/ethtrader, r/cryptocurrency\n- Volume: 8,420 posts/comments\n- Positive: 65%\n- Neutral: 28%\n- Negative: 7%\n- Trending: Staking yields, Layer 2 solutions\n\n💬 **Discord** (70/100 - Bullish)\n- Channels monitored: 15 major crypto communities\n- Sentiment: Cautiously optimistic\n- Topics: Gas fees improvement, NFT activity\n\n📰 **News** (76/100 - Bullish)\n- Articles: 127 (past 24h)\n- Positive coverage: 68%\n- Key headlines: \"ETH breaks resistance\", \"Institutional inflows continue\"\n\n**Sentiment Divergence Alert:**\n⚠️ Twitter sentiment (68) is 7 points lower than Reddit (75). This may indicate retail optimism vs institutional caution.\n\n**Historical Context:**\n- 7-day average: 65/100\n- Trend: ↗️ Improving (+7 points)\n\n**Recommendation:** Overall bullish sentiment with strong fundamentals. Watch for sentiment shifts if price breaks key levels.",
    "agent_type": "hunter_sentiment",
    "created_at": "2025-12-26T10:33:04Z"
  },
  "routing": {
    "intent": "hunter_sentiment",
    "confidence": 0.94,
    "handler": "hunter_sentiment",
    "agent_used": "hunter_ai",
    "reasoning": "User requesting sentiment analysis from social media sources",
    "total_latency_ms": 2340
  },
  "enrichment": {
    "token_symbol": "ETH",
    "time_horizon": "24h",
    "sources": ["twitter", "reddit", "discord", "news"],
    "hunter_tool": "sentiment_analysis"
  }
}
```

**Other Example Queries**:
- "BTC sentiment last 7 days"
- "How does crypto Twitter feel about SOL?"
- "Show me Polygon sentiment from all sources"

---

### 2.2. Price Prediction

**Intent**: Forecast token price using ML models (LSTM)

**Input**:
```json
{
  "content": "Predict BTC price for next 7 days"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440008",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Predict BTC price for next 7 days",
    "created_at": "2025-12-26T10:34:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440009",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "📈 **BTC Price Prediction (7-Day Forecast)**\n\n**Current Price:** $42,350\n**Model:** LSTM Neural Network (90-day training window)\n**Confidence:** 78%\n\n**Predicted Prices:**\n\n📅 Day 1 (Dec 27): $42,800 (+1.1%) - Confidence: 82%\n📅 Day 2 (Dec 28): $43,200 (+2.0%) - Confidence: 79%\n📅 Day 3 (Dec 29): $43,650 (+3.1%) - Confidence: 76%\n📅 Day 4 (Dec 30): $43,400 (+2.5%) - Confidence: 74%\n📅 Day 5 (Dec 31): $44,100 (+4.1%) - Confidence: 71%\n📅 Day 6 (Jan 1): $44,500 (+5.1%) - Confidence: 68%\n📅 Day 7 (Jan 2): $44,800 (+5.8%) - Confidence: 65%\n\n**Expected Range:** $41,500 - $46,200\n**Average Predicted Price:** $43,779 (+3.4%)\n\n**Technical Indicators:**\n- Trend: ↗️ Bullish\n- Support: $41,200\n- Resistance: $45,000\n- RSI: 62 (Neutral-Bullish)\n- MACD: Bullish crossover\n\n**Risk Factors:**\n⚠️ High volatility expected around Dec 31 (end of year trading)\n⚠️ Confidence decreases beyond day 3\n⚠️ Major news events can invalidate predictions\n\n**Disclaimer:** This is a statistical prediction based on historical patterns. Not financial advice. Actual prices may vary significantly.",
    "agent_type": "hunter_price_prediction",
    "created_at": "2025-12-26T10:34:05Z"
  },
  "routing": {
    "intent": "hunter_price_prediction",
    "confidence": 0.96,
    "handler": "hunter_price_prediction",
    "agent_used": "hunter_ai",
    "reasoning": "User requesting price forecast using time-series prediction",
    "total_latency_ms": 3120
  },
  "enrichment": {
    "token_symbol": "BTC",
    "time_horizon": "7d",
    "hunter_tool": "price_prediction"
  }
}
```

**Other Example Queries**:
- "What will ETH cost tomorrow?"
- "30-day price forecast for SOL"
- "Predict LINK price next week"

---

### 2.3. Risk Signals

**Intent**: Detect market risk warnings and anomalies

**Input**:
```json
{
  "content": "Show risk signals for ETH"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Show risk signals for ETH",
    "created_at": "2025-12-26T10:35:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440011",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "⚠️ **Risk Signals for ETH**\n\n**Overall Risk Level:** MEDIUM (6/10)\n\n**Active Warnings:**\n\n🔴 **High Risk** (2 signals)\n\n1. **Funding Rate Extreme** (Risk: 8/10)\n   - Perpetual funding rate: 0.12% (8-hour)\n   - Annualized: 131% APR\n   - Signal: Overleveraged longs, potential for long squeeze\n   - Recommendation: Reduce leverage or close long positions\n\n2. **Large Whale Transfer** (Risk: 7/10)\n   - Amount: 50,000 ETH ($95M) moved to exchange\n   - Time: 2 hours ago\n   - Signal: Possible sell pressure incoming\n   - Historical accuracy: 72%\n\n🟡 **Medium Risk** (3 signals)\n\n3. **Volume Anomaly** (Risk: 6/10)\n   - 24h volume: 180% above 7-day average\n   - Signal: Unusual activity, possible manipulation\n   - Could indicate: Pump before dump or genuine breakout\n\n4. **Exchange Inflows** (Risk: 5/10)\n   - Net exchange inflow: +32,000 ETH (24h)\n   - Signal: Selling pressure building\n   - Trend: Increasing for past 3 days\n\n5. **Social Sentiment Divergence** (Risk: 5/10)\n   - Price: +3.2% (24h)\n   - Sentiment: -5% (declining)\n   - Signal: Price-sentiment disconnect\n   - Historical pattern: Often precedes corrections\n\n🟢 **Low Risk** (1 signal)\n\n6. **Network Health** (Risk: 2/10)\n   - Gas usage: Normal\n   - Active addresses: Growing\n   - DeFi TVL: Stable\n   - Signal: Fundamentals remain strong\n\n**Risk Score Breakdown:**\n- Market Manipulation Risk: 7/10\n- Liquidity Risk: 5/10\n- Volatility Risk: 6/10\n- Fundamental Risk: 2/10\n\n**Recommended Actions:**\n1. ⚠️ Reduce leverage if trading on margin\n2. 📊 Monitor exchange flows in next 12-24 hours\n3. 💰 Consider taking partial profits above $2,000\n4. 🎯 Set stop-loss below $1,850 support\n\n**Update Frequency:** Risk signals recalculated every 15 minutes",
    "agent_type": "hunter_risk_signals",
    "created_at": "2025-12-26T10:35:06Z"
  },
  "routing": {
    "intent": "hunter_risk_signals",
    "confidence": 0.92,
    "handler": "hunter_risk_signals",
    "agent_used": "hunter_ai",
    "reasoning": "User requesting market risk warnings and anomaly detection",
    "total_latency_ms": 2890
  },
  "enrichment": {
    "token_symbol": "ETH",
    "hunter_tool": "risk_signals"
  }
}
```

**Other Example Queries**:
- "Any red flags for BTC?"
- "Check market risks for SOL"
- "What's risky about LINK right now?"

---

### 2.4. Trading Signals

**Intent**: Generate buy/sell signals with entry/exit prices

**Input**:
```json
{
  "content": "Should I buy SOL now? Give me trading signals"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440012",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Should I buy SOL now? Give me trading signals",
    "created_at": "2025-12-26T10:36:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440013",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "📊 **Trading Signals for SOL**\n\n**Current Price:** $98.45\n**Timeframe:** 4-Hour\n**Signal Strength:** STRONG BUY (82/100)\n\n---\n\n**🟢 PRIMARY SIGNAL: BUY**\n\n**Entry Points:**\n- 🎯 Primary Entry: $98.00 - $99.50 (Current zone)\n- 🎯 Secondary Entry: $95.50 - $96.50 (If pullback)\n\n**Take Profit Levels:**\n- 🥇 TP1: $104.00 (+5.6%) - Probability: 75%\n- 🥈 TP2: $108.50 (+10.2%) - Probability: 55%\n- 🥉 TP3: $115.00 (+16.8%) - Probability: 35%\n\n**Stop Loss:**\n- 🛑 Stop: $93.50 (-5.0%)\n- Max Risk: -$4.95 per SOL\n\n**Position Sizing:**\n- Conservative: 2-3% of portfolio\n- Moderate: 5-7% of portfolio\n- Aggressive: 8-10% of portfolio\n\n---\n\n**Signal Indicators:**\n\n✅ **Bullish Factors** (8/10):\n1. RSI (14): 58 - Neutral with upside room\n2. MACD: Bullish crossover (2 hours ago)\n3. Moving Averages: Price above 50 & 200 EMA\n4. Volume: +45% above average\n5. Market Structure: Higher highs, higher lows\n6. Support Level: Strong buy wall at $96\n\n⚠️ **Risk Factors** (3/10):\n1. Overbought on 1H timeframe (RSI 72)\n2. Resistance at $102 (previous high)\n3. Bitcoin correlation: 0.85 (BTC pullback = SOL pullback)\n\n---\n\n**Trade Plan:**\n\n**Scenario 1: Immediate Entry** (Recommended)\n- Buy: $98.00 - $99.50\n- Sell 30% at TP1 ($104)\n- Sell 40% at TP2 ($108.50)\n- Hold 30% for TP3 ($115) or trail stop\n\n**Scenario 2: Wait for Pullback** (Conservative)\n- Wait for dip to $95.50 - $96.50\n- If price reaches, buy with same TPs\n- If no pullback and price breaks $100, enter at market\n\n---\n\n**Risk/Reward Analysis:**\n- Risk: 5.0% (-$4.95)\n- Potential Reward: 10.2% (+$10.05)\n- R:R Ratio: 1:2.0 (Favorable)\n\n**Confidence Breakdown:**\n- Technical Analysis: 85%\n- Sentiment Analysis: 78%\n- Volume Profile: 82%\n- Overall Signal: 82%\n\n**Timeframe Expectations:**\n- TP1: 2-4 days\n- TP2: 5-7 days\n- TP3: 10-14 days\n\n---\n\n⚠️ **Important Notes:**\n- Monitor Bitcoin price action (strong correlation)\n- Exit all positions if BTC breaks $41,000\n- Consider DCA if entry missed\n- Not financial advice - DYOR\n\n**Last Updated:** 2025-12-26 10:36:00 UTC",
    "agent_type": "hunter_trading_signals",
    "created_at": "2025-12-26T10:36:08Z"
  },
  "routing": {
    "intent": "hunter_trading_signals",
    "confidence": 0.97,
    "handler": "hunter_trading_signals",
    "agent_used": "hunter_ai",
    "reasoning": "User requesting buy/sell signals with entry and exit prices",
    "total_latency_ms": 3450
  },
  "enrichment": {
    "token_symbol": "SOL",
    "hunter_tool": "trading_signals"
  }
}
```

**Other Example Queries**:
- "Give me BTC trading signals"
- "When should I sell ETH?"
- "Entry and exit points for AVAX"

---

### 2.5. Pattern Detection

**Intent**: Identify chart patterns and technical formations

**Input**:
```json
{
  "content": "What chart patterns do you see for BTC?"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440014",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "What chart patterns do you see for BTC?",
    "created_at": "2025-12-26T10:37:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440015",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "📈 **Chart Pattern Analysis for BTC**\n\n**Detected Patterns: 5**\n**Timeframe Analysis:** 4H, 1D, 1W\n\n---\n\n**🔺 ACTIVE PATTERNS**\n\n**1. Ascending Triangle** (4H Chart)\n- Status: ✅ Forming (85% complete)\n- Timeframe: 4-Hour\n- Pattern Type: Bullish Continuation\n- Breakout Direction: UP (Probability: 75%)\n- Entry: Breakout above $43,500\n- Target: $46,800 (+7.6%)\n- Stop Loss: $41,200\n- Formation Start: Dec 20\n- Expected Breakout: Within 2-3 days\n- Confidence: 82%\n\n**2. Bull Flag** (1H Chart)\n- Status: ✅ Confirmed\n- Timeframe: 1-Hour\n- Pattern Type: Bullish Continuation\n- Pole: $40,500 → $43,200 (+6.7%)\n- Flag: $42,800 → $42,200 (consolidation)\n- Breakout Level: $43,000\n- Target: $45,700 (+6.2%)\n- Confidence: 78%\n\n**3. Higher Lows Pattern** (1D Chart)\n- Status: ✅ Active\n- Timeframe: Daily\n- Swing Lows: $38,500 → $40,200 → $41,800\n- Trend: Bullish\n- Next Support: $42,000\n- Indicates: Accumulation phase\n- Confidence: 88%\n\n---\n\n**📊 CANDLESTICK PATTERNS**\n\n**4. Morning Star** (Recent)\n- Date: Dec 24-26\n- Timeframe: Daily\n- Type: Bullish Reversal\n- Formation:\n  - Day 1: Long red candle ($44,200 → $41,500)\n  - Day 2: Small doji/spinning top\n  - Day 3: Long green candle ($41,800 → $43,200)\n- Signal Strength: Strong\n- Confirmation: ✅ Volume increased\n- Confidence: 85%\n\n**5. Three White Soldiers** (Recent)\n- Dates: Dec 22-24\n- Timeframe: Daily\n- Type: Bullish Continuation\n- Pattern: Three consecutive green candles\n- Each close higher than previous\n- Signal: Strong buying momentum\n- Confidence: 80%\n\n---\n\n**🎯 KEY LEVELS**\n\n**Support Zones:**\n- 🛡️ Strong: $41,200 (Tested 3x, held)\n- 🛡️ Moderate: $40,500 (Previous resistance, now support)\n- 🛡️ Major: $38,800 (200 EMA on daily)\n\n**Resistance Zones:**\n- ⚔️ Immediate: $43,500 (Triangle top)\n- ⚔️ Strong: $45,000 (Psychological level)\n- ⚔️ Major: $47,500 (Previous all-time high)\n\n---\n\n**📐 FIBONACCI LEVELS**\n\n**Retracement (from $47,500 → $38,500):**\n- 0.236: $40,625 ✅ Broken\n- 0.382: $41,938 ✅ Broken\n- 0.500: $43,000 🎯 Current battle\n- 0.618: $44,063 (Next target)\n- 0.786: $45,569 (Major resistance)\n\n**Extension Targets (if breakout):**\n- 1.272: $46,234\n- 1.414: $47,018\n- 1.618: $48,362\n\n---\n\n**💡 TRADING IMPLICATIONS**\n\n**Bullish Scenario (70% probability):**\n1. Break above $43,500 confirms ascending triangle\n2. Target: $46,800 within 5-7 days\n3. Strong momentum above $45,000 targets $47,500\n\n**Bearish Scenario (30% probability):**\n1. Rejection at $43,500 and close below $42,000\n2. Invalidates bullish patterns\n3. Target: Retest $40,500 support\n4. Break below $40,500 → $38,800 likely\n\n**Recommendation:**\n- Wait for breakout confirmation above $43,500\n- Volume must be 30%+ above average\n- Don't chase - let price consolidate above breakout\n- Set alerts at key levels: $43,500, $45,000, $47,500\n\n---\n\n**Pattern Reliability (Historical):**\n- Ascending Triangle: 72% success rate\n- Bull Flag: 68% success rate\n- Morning Star: 75% success rate\n- Three White Soldiers: 65% success rate\n\n**Last Updated:** 2025-12-26 10:37:00 UTC",
    "agent_type": "hunter_patterns",
    "created_at": "2025-12-26T10:37:10Z"
  },
  "routing": {
    "intent": "hunter_patterns",
    "confidence": 0.93,
    "handler": "hunter_patterns",
    "agent_used": "hunter_ai",
    "reasoning": "User asking for chart pattern detection and technical analysis",
    "total_latency_ms": 4120
  },
  "enrichment": {
    "token_symbol": "BTC",
    "hunter_tool": "pattern_detection"
  }
}
```

**Other Example Queries**:
- "Find patterns in ETH chart"
- "Head and shoulders on SOL?"
- "Technical patterns for LINK"

---

### 2.6. Portfolio Optimization

**Intent**: Optimize asset allocation using Modern Portfolio Theory (MPT)

**Input**:
```json
{
  "content": "Optimize my portfolio with BTC, ETH, and SOL for moderate risk"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440016",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Optimize my portfolio with BTC, ETH, and SOL for moderate risk",
    "created_at": "2025-12-26T10:38:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440017",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "💼 **Portfolio Optimization (Balanced)**\n\n**Strategy:** Modern Portfolio Theory (MPT)\n**Risk Profile:** Moderate (Risk Tolerance: 0.5)\n**Optimization Goal:** Maximize Sharpe Ratio\n\n---\n\n**📊 OPTIMAL ALLOCATION**\n\n**Recommended Weights:**\n- **BTC**: 45.0% 🟦🟦🟦🟦🟦\n- **ETH**: 35.0% 🟩🟩🟩🟩\n- **SOL**: 20.0% 🟨🟨\n\n**For $10,000 investment:**\n- BTC: $4,500 (≈ 0.106 BTC at $42,350)\n- ETH: $3,500 (≈ 1.84 ETH at $1,900)\n- SOL: $2,000 (≈ 20.3 SOL at $98.50)\n\n---\n\n**📈 PERFORMANCE METRICS**\n\n**Expected Returns:**\n- Annual Return: 45.2%\n- Monthly Return: 3.2%\n- 90-day Return: 9.8%\n\n**Risk Metrics:**\n- Volatility (Risk): 32.8% annualized\n- Sharpe Ratio: 1.28 (Excellent)\n- Sortino Ratio: 1.85\n- Max Drawdown: -28.5% (worst case)\n- Value at Risk (95%): -8.2% (monthly)\n\n**Diversification:**\n- Correlation Score: 0.68 (Well diversified)\n- Portfolio Beta: 0.92 (vs. crypto market)\n- Idiosyncratic Risk: 15%\n\n---\n\n**💡 ALLOCATION RATIONALE**\n\n**BTC (45%)** - Anchor Asset\n- Lowest volatility of the three\n- Highest liquidity and market cap\n- Acts as portfolio stabilizer\n- Historical Sharpe Ratio: 1.12\n\n**ETH (35%)** - Growth + Stability\n- Balanced risk/reward profile\n- Strong fundamentals (ETH 2.0, DeFi)\n- Moderate correlation with BTC (0.72)\n- Historical Sharpe Ratio: 1.08\n\n**SOL (20%)** - High Growth Potential\n- Higher risk, higher reward\n- Lower correlation with BTC (0.58)\n- Provides portfolio upside\n- Historical Sharpe Ratio: 0.95\n- Capped at 20% to limit volatility\n\n---\n\n**📊 EFFICIENT FRONTIER ANALYSIS**\n\n**Your Portfolio Position:**\n- Risk: 32.8% ⭐ (You are here)\n- Return: 45.2%\n- Sharpe: 1.28\n\n**Alternative Allocations:**\n\n**Conservative** (Lower Risk):\n- BTC: 60%, ETH: 30%, SOL: 10%\n- Return: 38.5% | Risk: 28.2% | Sharpe: 1.18\n\n**Balanced** (Recommended):\n- BTC: 45%, ETH: 35%, SOL: 20%\n- Return: 45.2% | Risk: 32.8% | Sharpe: 1.28 ⭐\n\n**Aggressive** (Higher Risk):\n- BTC: 30%, ETH: 35%, SOL: 35%\n- Return: 52.8% | Risk: 42.1% | Sharpe: 1.15\n\n---\n\n**🔄 REBALANCING STRATEGY**\n\n**Frequency:** Quarterly (every 3 months)\n\n**Triggers for Early Rebalancing:**\n1. Any asset drifts >10% from target weight\n2. Portfolio Sharpe ratio drops below 1.0\n3. Correlation between assets changes significantly\n4. Major market regime change\n\n**Example Rebalancing:**\nIf after 3 months your portfolio becomes:\n- BTC: 50% (+5% drift)\n- ETH: 32% (-3% drift)\n- SOL: 18% (-2% drift)\n\nRebalance by:\n- Sell: $500 of BTC\n- Buy: $300 of ETH, $200 of SOL\n\n---\n\n**⚠️ RISK CONSIDERATIONS**\n\n**Market Risks:**\n1. Crypto winter: All assets could drop 50%+\n2. Regulatory changes affecting all tokens\n3. Bitcoin dominance shifts\n\n**Asset-Specific Risks:**\n- BTC: Regulatory crackdowns, mining bans\n- ETH: ETH 2.0 transition issues, gas fees\n- SOL: Network outages, centralization concerns\n\n**Mitigation:**\n- Keep 10-20% in stablecoins for opportunities\n- Use stop-losses if portfolio drops >40%\n- Consider adding uncorrelated assets (gold, USDC)\n\n---\n\n**📅 MONITORING SCHEDULE**\n\n**Daily:**\n- Check for >15% single-day moves\n- Monitor news for major events\n\n**Weekly:**\n- Review portfolio balance\n- Check if rebalancing needed\n\n**Monthly:**\n- Calculate actual vs expected returns\n- Assess Sharpe ratio performance\n- Review allocation vs targets\n\n**Quarterly:**\n- Execute scheduled rebalancing\n- Reassess risk tolerance\n- Update return expectations\n\n---\n\n**🎯 EXPECTED OUTCOMES**\n\n**Best Case (Bull Market):**\n- 12-month return: +85% to +120%\n- Portfolio value: $18,500 - $22,000\n\n**Base Case (Moderate Growth):**\n- 12-month return: +40% to +50%\n- Portfolio value: $14,000 - $15,000\n\n**Worst Case (Bear Market):**\n- 12-month return: -25% to -35%\n- Portfolio value: $6,500 - $7,500\n\n**Recommendation:** This allocation maximizes risk-adjusted returns for your moderate risk profile. Review quarterly and rebalance as needed.\n\n*Allocation based on 90-day historical data. Past performance doesn't guarantee future results.*",
    "agent_type": "hunter_portfolio",
    "created_at": "2025-12-26T10:38:12Z"
  },
  "routing": {
    "intent": "hunter_portfolio",
    "confidence": 0.95,
    "handler": "hunter_portfolio",
    "agent_used": "hunter_ai",
    "reasoning": "User requesting portfolio optimization using Modern Portfolio Theory",
    "total_latency_ms": 4580
  },
  "enrichment": {
    "tokens": ["BTC", "ETH", "SOL"],
    "risk_tolerance": 0.5,
    "hunter_tool": "portfolio_optimization"
  }
}
```

**Other Example Queries**:
- "Optimize BTC, ETH, LINK, AVAX for conservative risk"
- "Best allocation for aggressive growth with 5 coins"
- "How should I split my portfolio between BTC and ETH?"

---

## 3. ULTRA Intents

### 3.1. Arbitrage Discovery

**Intent**: Find profitable arbitrage opportunities across DEXes

**Input**:
```json
{
  "content": "Find arbitrage opportunities with $10,000 capital"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440018",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Find arbitrage opportunities with $10,000 capital",
    "created_at": "2025-12-26T10:39:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440019",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "🔍 **Arbitrage Opportunities** ($10,000.00 capital)\n\n**Found 7 opportunities:**\n\n**1. 2-HOP Arbitrage**\n- Route: Uniswap → SushiSwap\n- Token: USDC → ETH → USDC\n- Expected Profit: $142.50 (1.42%)\n- Gas Cost: $18.30\n- Net Profit: $124.20\n- Opportunity ID: ARB-1735215540-0001\n- Execution Time: ~45 seconds\n- Slippage Risk: Low (0.2%)\n\n**2. 3-HOP Arbitrage**\n- Route: Uniswap → Curve → Balancer\n- Token: DAI → USDC → USDT → DAI\n- Expected Profit: $98.75 (0.99%)\n- Gas Cost: $28.50\n- Net Profit: $70.25\n- Opportunity ID: ARB-1735215540-0002\n- Execution Time: ~90 seconds\n- Slippage Risk: Medium (0.5%)\n\n**3. TRIANGLE Arbitrage**\n- Route: Uniswap (ETH/USDC → ETH/DAI → USDC/DAI)\n- Tokens: ETH → DAI → USDC → ETH\n- Expected Profit: $186.20 (1.86%)\n- Gas Cost: $22.10\n- Net Profit: $164.10\n- Opportunity ID: ARB-1735215540-0003\n- Execution Time: ~60 seconds\n- Slippage Risk: Low (0.3%)\n\n**4. 2-HOP Arbitrage**\n- Route: PancakeSwap → BiSwap\n- Token: BNB → BUSD → BNB\n- Expected Profit: $78.30 (0.78%)\n- Gas Cost: $2.15 (BSC)\n- Net Profit: $76.15\n- Opportunity ID: ARB-1735215540-0004\n- Execution Time: ~30 seconds\n- Slippage Risk: Low (0.15%)\n\n**5. 3-HOP Arbitrage**\n- Route: Uniswap → 1inch → Kyber\n- Token: WETH → USDC → DAI → WETH\n- Expected Profit: $112.90 (1.13%)\n- Gas Cost: $31.20\n- Net Profit: $81.70\n- Opportunity ID: ARB-1735215540-0005\n- Execution Time: ~100 seconds\n- Slippage Risk: High (0.8%)\n\n*+ 2 more opportunities available*\n\n💡 **Next Steps:**\n- Use `/ultra/mev-protection` to execute with Flashbots\n- Check gas prices before execution\n- Monitor liquidity depth for slippage\n\n**Best Opportunity:** #3 Triangle Arbitrage (Net: $164.10)\n**Safest Opportunity:** #4 BSC 2-hop (Low gas, low slippage)\n**Fastest Execution:** #4 BSC 2-hop (30 seconds)\n\n⚠️ **Important:**\n- Opportunities expire quickly (avg 2-3 minutes)\n- Always simulate before executing\n- Consider MEV protection for large amounts\n- Gas prices fluctuate - recalculate before execution",
    "agent_type": "ultra_discovery",
    "created_at": "2025-12-26T10:39:05Z"
  },
  "routing": {
    "intent": "ultra_arbitrage",
    "confidence": 0.93,
    "handler": "ultra_arbitrage",
    "agent_used": "ultra_discovery",
    "reasoning": "User searching for arbitrage opportunities with specified capital",
    "total_latency_ms": 3240
  },
  "enrichment": {
    "capital": 10000.0,
    "arb_type": "all",
    "ultra_tool": "arbitrage_discovery"
  }
}
```

**Other Example Queries**:
- "Find 2-hop arbitrage with $5k"
- "Show me triangular arbitrage opportunities"
- "Any profitable cross-DEX trades available?"

---

### 3.2. Flash Loan Selection

**Intent**: Compare flash loan protocols and select the best one

**Input**:
```json
{
  "content": "Best flash loan protocol for 100k USDC"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440020",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Best flash loan protocol for 100k USDC",
    "created_at": "2025-12-26T10:40:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440021",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "⚡ **Flash Loan Comparison** (USDC)\n\n**Best Protocol:** Balancer\n- Fee: 0.000%\n- Total Cost: $0.00\n\n**All Protocols:**\n- Balancer: $0.00 (0.000%)\n- Aave: $90.00 (0.090%)\n- Uniswap V3: $150.00 (0.150%)\n\n💡 **Use Case:** Borrow $100,000.00 USDC instantly with no collateral\nExecute arbitrage, liquidations, or collateral swaps in a single transaction\n\n**Why Balancer?**\n- ✅ Zero fees (0.000%)\n- ✅ Deep USDC liquidity ($850M available)\n- ✅ Battle-tested smart contracts\n- ✅ Support for complex multi-token flash loans\n\n**Alternative Use Cases:**\n\n**Aave** - Better for:\n- Flash loans during high Balancer congestion\n- Assets not available on Balancer\n- Loans requiring GHO stablecoin\n\n**Uniswap V3** - Better for:\n- Specific token pairs with deep V3 liquidity\n- When combined with V3 concentrated liquidity positions\n\n**How to Execute:**\n1. Deploy flash loan contract\n2. Call `flashLoan()` on Balancer Vault\n3. Execute your strategy (arbitrage, liquidation, etc.)\n4. Repay loan + fees in same transaction\n5. Keep the profit\n\n**Security Notes:**\n⚠️ Transaction must repay loan or it reverts\n⚠️ Test with small amounts first\n⚠️ Consider MEV protection for large loans\n⚠️ Gas costs can be $50-200 depending on complexity",
    "agent_type": "ultra_flash_loan_engine",
    "created_at": "2025-12-26T10:40:03Z"
  },
  "routing": {
    "intent": "ultra_flash_loans",
    "confidence": 0.96,
    "handler": "ultra_flash_loans",
    "agent_used": "ultra_flash_loan_engine",
    "reasoning": "User requesting flash loan protocol comparison and selection",
    "total_latency_ms": 1890
  },
  "enrichment": {
    "token_symbol": "USDC",
    "amount": 100000.0,
    "protocol": null,
    "ultra_tool": "flash_loan_engine"
  }
}
```

**Other Example Queries**:
- "Compare Aave vs Balancer flash loans for ETH"
- "Cheapest flash loan for 1M DAI"
- "Flash loan fees for WBTC"

---

### 3.3. MEV Protection

**Intent**: Execute transactions with Flashbots MEV protection

**Input**:
```json
{
  "content": "Execute ARB-001 with Flashbots protection"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440022",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Execute ARB-001 with Flashbots protection",
    "created_at": "2025-12-26T10:41:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440023",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "🛡️ **MEV-Protected Execution**\n\n**Opportunity:** ARB-001\n\n**Flashbots Bundle Status:**\n- Bundle submitted to Flashbots relay\n- Private transaction (not in public mempool)\n- Protected from frontrunning\n- Priority fee: Dynamic based on block\n\n💡 **MEV Protection Benefits:**\n- No sandwich attacks\n- No frontrunning\n- Failed transactions revert privately\n- Only pay gas if transaction succeeds\n\n**Execution Details:**\n- Bundle ID: 0x7a3d9e... (check status with Flashbots API)\n- Target Block: Next available\n- Max Priority Fee: 2 Gwei\n- Expected Inclusion: 1-3 blocks (~15-45 seconds)\n\n**What Happens Next:**\n1. Flashbots validates your bundle\n2. Miners receive your bundle privately\n3. Your transaction executes if profitable for miner\n4. You receive confirmation or revert notification\n\n**Monitoring:**\n- Track bundle status: https://flashbots.tools/bundle/0x7a3d9e...\n- If not included in 5 blocks, bundle expires\n- Resubmit with higher priority fee if needed\n\n⚠️ **Note:** Even with MEV protection, arbitrage may fail if:\n- Liquidity changes before execution\n- Gas price spikes significantly\n- Another MEV bot executes same opportunity",
    "agent_type": "ultra_mev_engine",
    "created_at": "2025-12-26T10:41:03Z"
  },
  "routing": {
    "intent": "ultra_mev_protection",
    "confidence": 0.91,
    "handler": "ultra_mev_protection",
    "agent_used": "ultra_mev_engine",
    "reasoning": "User requesting MEV-protected execution via Flashbots",
    "total_latency_ms": 1650
  },
  "enrichment": {
    "opportunity_id": "ARB-001",
    "ultra_tool": "mev_protection"
  }
}
```

**Other Example Queries**:
- "Submit transaction with Flashbots"
- "Protect my swap from MEV"
- "Use private relay for this trade"

---

### 3.4. Auto Executor Control

**Intent**: Control automated trading bot (start/stop/pause/status)

**Input**:
```json
{
  "content": "Start trading bot"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440024",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Start trading bot",
    "created_at": "2025-12-26T10:42:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440025",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "🤖 **Trading Bot Started**\n\n✅ Auto-executor is now active\n\n**What it does:**\n- Continuously scans for arbitrage opportunities\n- Automatically executes profitable trades\n- Uses MEV protection for all executions\n- Monitors gas prices for optimal timing\n\n**Current Configuration:**\n- Min Profit Threshold: $50\n- Max Capital Per Trade: $10,000\n- Gas Price Limit: 50 Gwei\n- Execution Strategy: Conservative\n- MEV Protection: Enabled (Flashbots)\n\n**Active Monitoring:**\n- DEXes: Uniswap, SushiSwap, Curve, Balancer\n- Chains: Ethereum, Arbitrum, Polygon\n- Scan Frequency: Every 3 seconds\n- Risk Management: Active\n\n**Safety Features:**\n- ✅ Automatic stop on 3 consecutive losses\n- ✅ Daily loss limit: $500\n- ✅ Cooldown period after failed trades\n- ✅ Real-time monitoring and alerts\n\n💡 Use `pause` or `stop` to control the bot\n\n**Status Dashboard:**\n- State: ACTIVE ✅\n- Uptime: 0.0 hours (just started)\n- Trades Today: 0\n- Total Profit: $0.00\n\n**Commands:**\n- \"bot status\" - Check performance\n- \"pause bot\" - Temporarily suspend\n- \"stop bot\" - Halt all operations",
    "agent_type": "ultra_auto_executor",
    "created_at": "2025-12-26T10:42:02Z"
  },
  "routing": {
    "intent": "ultra_auto_executor",
    "confidence": 0.97,
    "handler": "ultra_auto_executor",
    "agent_used": "ultra_auto_executor",
    "reasoning": "User commanding trading bot to start automated execution",
    "total_latency_ms": 1120
  },
  "enrichment": {
    "action": "start",
    "ultra_tool": "auto_executor"
  }
}
```

**Bot Status Query**:
```json
{
  "content": "Show bot status"
}
```

**Expected Output**:
```json
{
  "agent_message": {
    "content": "🤖 **Trading Bot Status**\n\n**State:** ACTIVE\n**Uptime:** 3.5 hours\n\n**Performance:**\n- Trades Executed: 12\n- Total Profit: $847.30\n- Success Rate: 83.3%\n\n**Current Activity:**\n- Scanning: True\n- Pending Executions: 1\n- Last Trade: 8 minutes ago (+$68.20)\n\n**Today's Breakdown:**\n- Winning Trades: 10 ($1,024.50)\n- Losing Trades: 2 (-$177.20)\n- Net Profit: $847.30\n- Average Profit: $70.61\n- Best Trade: $142.50\n- Worst Trade: -$98.10\n\n**Risk Metrics:**\n- Max Drawdown: -12.3%\n- Win Rate: 83.3%\n- Profit Factor: 5.78\n- Average Hold Time: 45 seconds\n\n💡 **Commands:** `start`, `stop`, `pause`, `resume`"
  }
}
```

**Other Example Queries**:
- "Stop trading bot"
- "Pause auto executor"
- "Resume bot operations"
- "What's my bot performance?"

---

## 4. Agent Squad & Chat Intents

### 4.1. Specialist Task

**Intent**: Route to specialized AI agents (18 agents available)

**Input**:
```json
{
  "content": "Analyze ETH/USDC liquidity depth on Uniswap V3"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440026",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Analyze ETH/USDC liquidity depth on Uniswap V3",
    "created_at": "2025-12-26T10:43:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440027",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "📊 **Uniswap V3 Liquidity Analysis: ETH/USDC**\n\n*Analysis performed by Agent Squad: DeFi Analytics Specialist*\n\n**Pool Overview:**\n- Pool Address: 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640\n- Fee Tier: 0.05%\n- TVL: $285.4M\n- 24h Volume: $142.8M\n- Volume/TVL Ratio: 50% (Highly efficient)\n\n**Liquidity Depth Analysis:**\n\n**Price Impact Estimates:**\n- $10k swap: 0.02% impact\n- $100k swap: 0.15% impact\n- $1M swap: 1.8% impact\n- $10M swap: 12.5% impact\n\n**Concentrated Liquidity Distribution:**\n\n**Current Price:** $1,897 USDC/ETH\n\n**Liquidity Heatmap:**\n```\n$1,850 - $1,875: ████████ $42M (15%)\n$1,875 - $1,900: ████████████ $68M (24%)\n$1,900 - $1,925: ██████████████ $95M (33%) ← Current Range\n$1,925 - $1,950: ██████████ $58M (20%)\n$1,950 - $1,975: ████ $22M (8%)\n```\n\n**Key Observations:**\n1. **High Concentration:** 57% of liquidity within ±2% of current price\n2. **Asymmetric Distribution:** More liquidity above current price (support for upside)\n3. **Efficiency:** Concentrated positions mean lower slippage than V2\n4. **Risk Zones:**\n   - Below $1,850: Liquidity drops 85%\n   - Above $1,975: Liquidity drops 72%\n\n**Active LP Positions:**\n- Total Positions: 2,847\n- Active in Range: 1,234 (43%)\n- Out of Range: 1,613 (57%)\n\n**Top Liquidity Providers:**\n1. 0x742d... - $18.4M (6.4%)\n2. 0x8a9e... - $12.7M (4.5%)\n3. 0x3f2c... - $9.8M (3.4%)\n\n**Fee Distribution (24h):**\n- Total Fees: $71,400\n- Average APR: 9.1% (annualized)\n- Top Position APR: 24.3%\n\n**Recommendations:**\n- ✅ Excellent for swaps <$500k\n- ⚠️ Consider splitting large orders (>$1M)\n- 📊 Best execution time: During high volume (12pm-8pm UTC)\n- 💡 Monitor liquidity shifts near key price levels",
    "agent_type": "agent_squad",
    "created_at": "2025-12-26T10:43:06Z"
  },
  "routing": {
    "intent": "specialist_task",
    "confidence": 0.89,
    "handler": "agent_squad",
    "reasoning": "User requesting specialized DeFi analysis requiring domain expertise",
    "total_latency_ms": 4250
  },
  "enrichment": {
    "tools_used": ["uniswap_v3_api", "the_graph", "liquidity_analyzer"],
    "tokens_consumed": 2840,
    "latency_ms": 4250,
    "intent_classification": "defi_analytics"
  }
}
```

**Other Example Queries**:
- "Calculate impermanent loss for my LP position"
- "Audit this smart contract for vulnerabilities"
- "Explain how flash loans work technically"

---

### 4.2. Complex Workflow

**Intent**: Multi-agent coordination for complex tasks

**Input**:
```json
{
  "content": "Create a complete DeFi investment strategy for $50k with risk analysis and execution plan"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440028",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Create a complete DeFi investment strategy for $50k with risk analysis and execution plan",
    "created_at": "2025-12-26T10:44:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440029",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "💼 **Comprehensive DeFi Investment Strategy**\n\n*Multi-Agent Workflow Completed*\n*Coordinated by: Supervisor Agent*\n*Contributing Agents: 5 specialists*\n\n---\n\n## Executive Summary\n\n**Total Capital:** $50,000\n**Strategy:** Diversified Yield + Growth\n**Risk Profile:** Moderate\n**Expected Annual Return:** 28-42%\n**Time Horizon:** 12 months\n\n---\n\n## Portfolio Allocation\n\n### Core Holdings (60% - $30,000)\n*Agent: Portfolio Optimizer*\n\n**Stable Yield Generation:**\n- **Aave USDC Lending:** $15,000 (30%)\n  - APY: 4.2%\n  - Risk: Low (2.5/10)\n  - Annual Return: $630\n  - Liquidity: Instant\n\n- **Curve 3pool LP:** $10,000 (20%)\n  - APY: 6.8% (base) + 3.2% (CRV rewards)\n  - Risk: Low (3.0/10)\n  - Annual Return: $1,000\n  - Impermanent Loss: Minimal (stablecoins)\n\n- **Yearn USDT Vault:** $5,000 (10%)\n  - APY: 8.5%\n  - Risk: Medium-Low (3.5/10)\n  - Annual Return: $425\n  - Auto-compounding\n\n### Growth Positions (30% - $15,000)\n*Agent: DeFi Strategist*\n\n**Smart Contract Protocols:**\n- **GMX Liquidity (GLP):** $8,000 (16%)\n  - APY: 18-25% (fee sharing)\n  - Risk: Medium (5.0/10)\n  - Expected Return: $1,600\n  - Asset: Blue-chip basket (BTC, ETH, etc.)\n\n- **Uniswap V3 ETH/USDC LP:** $7,000 (14%)\n  - Range: $1,850 - $1,950\n  - APY: 12-18% (concentrated position)\n  - Risk: Medium (4.5/10)\n  - Expected Return: $1,050\n  - IL Risk: Managed with narrow range\n\n### Speculative/High Yield (10% - $5,000)\n*Agent: Yield Farmer*\n\n**Emerging Protocols:**\n- **Pendle PT-ETH:** $3,000 (6%)\n  - Fixed APY: 4.5% + upside exposure\n  - Risk: Medium-High (6.0/10)\n  - Expected Return: $135 + potential\n  - Duration: 6 months\n\n- **Rocket Pool Staking:** $2,000 (4%)\n  - APY: 3.8%\n  - Risk: Low-Medium (3.8/10)\n  - Expected Return: $76\n  - Bonus: rETH price appreciation\n\n---\n\n## Risk Analysis\n\n*Agent: Risk Analyst*\n\n**Portfolio Risk Score: 3.8/10 (Moderate)**\n\n**Risk Breakdown:**\n\n**Smart Contract Risk (4.2/10):**\n- All protocols audited\n- 3+ years operational history (except Pendle)\n- Total Value at Risk: $50,000\n- Mitigation: Insurance through Nexus Mutual ($500/year)\n\n**Liquidity Risk (2.5/10):**\n- 90% can be withdrawn within 24 hours\n- Pendle position locked for 6 months\n- Emergency liquidity: Aave lending ($15k)\n\n**Impermanent Loss Risk (3.5/10):**\n- Curve 3pool: Minimal (stablecoins)\n- Uniswap V3: Managed with ±2.5% range\n- GMX: Diversified basket reduces single-asset IL\n\n**Market Risk (5.0/10):**\n- Crypto market volatility\n- Correlated drawdowns possible\n- Mitigation: 30% stablecoin allocation\n\n**Worst-Case Scenarios:**\n\n*Bear Market (-50% crypto crash):*\n- Aave/Curve/Yearn: Minimal impact ($30k → $29.5k)\n- GMX: -25% ($8k → $6k)\n- Uniswap LP: -15% IL + -20% assets ($7k → $4.9k)\n- Total: $50k → $40.4k (-19.2%)\n\n*Smart Contract Exploit:*\n- Single protocol failure: Max loss $15k (Aave)\n- Nexus Mutual coverage: 80% recovery\n- Net loss: -6% portfolio\n\n*De-peg Event (USDC/USDT):*\n- Affected capital: $30k\n- Historical recovery: 95%+\n- Max temporary loss: $1,500\n\n---\n\n## Execution Plan\n\n*Agent: Execution Specialist*\n\n**Phase 1: Foundation (Week 1)**\n\nDay 1:\n- [ ] Transfer $50k USDC to wallet\n- [ ] Set up hardware wallet (if not already)\n- [ ] Purchase Nexus Mutual insurance ($500)\n\nDay 2-3:\n- [ ] Deploy $15k to Aave USDC lending\n- [ ] Enter $10k to Curve 3pool\n- [ ] Test small amount ($100) on each protocol\n\n**Phase 2: Growth Positions (Week 2)**\n\nDay 8-10:\n- [ ] Analyze Uniswap V3 ETH/USDC liquidity\n- [ ] Set narrow range position ($1,850-$1,950)\n- [ ] Deploy $7k to Uniswap V3\n- [ ] Monitor for 48h, adjust if needed\n\nDay 11-14:\n- [ ] Purchase $8k of GLP tokens\n- [ ] Stake in GMX platform\n- [ ] Verify fee accrual\n\n**Phase 3: Final Allocation (Week 3)**\n\nDay 15-17:\n- [ ] Research current Pendle yields\n- [ ] Enter $3k PT-ETH position\n- [ ] Deploy $5k to Yearn USDT vault\n- [ ] Stake $2k in Rocket Pool\n\n**Phase 4: Monitoring & Rebalancing**\n\n*Weekly:*\n- Check APYs and rebalance if yields change >20%\n- Monitor Uniswap V3 range (reposition if out of range)\n- Track GMX fee accrual\n\n*Monthly:*\n- Harvest rewards and compound\n- Review risk metrics\n- Rebalance to target allocation (±5% tolerance)\n\n*Quarterly:*\n- Full strategy review\n- Consider rotating into better opportunities\n- Tax loss harvesting (if applicable)\n\n---\n\n## Expected Returns\n\n*Agent: Financial Analyst*\n\n**Base Case (Most Likely):**\n- Stable Yield: $2,055/year (6.85%)\n- Growth Positions: $2,650/year (17.67%)\n- Speculative: $211/year (4.22%)\n- **Total: $4,916/year (9.83%)**\n\n**Bull Case (Crypto +50%):**\n- Stable Yield: $2,055 (same)\n- Growth Positions: $4,250 (GMX & UNI benefit)\n- Speculative: $850 (rETH appreciation)\n- **Total: $7,155/year (14.31%)**\n\n**Conservative Case (Sideways Market):**\n- Stable Yield: $1,850 (rates drop)\n- Growth Positions: $1,200 (lower activity)\n- Speculative: $150\n- **Total: $3,200/year (6.40%)**\n\n**12-Month Projections:**\n- Best Case: $50k → $57k (+14%)\n- Expected: $50k → $54.9k (+9.8%)\n- Conservative: $50k → $53.2k (+6.4%)\n\n---\n\n## Tax Considerations\n\n*Note: Consult tax professional*\n\n- Yield: Ordinary income\n- LP rewards: Capital gains when sold\n- Track all transactions for reporting\n- Consider tax-loss harvesting in December\n\n---\n\n## Monitoring Dashboard\n\n**Daily Checks:**\n- [ ] Uniswap V3 range status\n- [ ] Major news/exploits in DeFi\n\n**Weekly:**\n- [ ] APY review across positions\n- [ ] Portfolio value tracking\n\n**Monthly:**\n- [ ] Full performance report\n- [ ] Rebalancing assessment\n\n---\n\n## Emergency Procedures\n\n**If smart contract exploit suspected:**\n1. Withdraw all funds from affected protocol ASAP\n2. File Nexus Mutual claim within 72 hours\n3. Move funds to secure wallet\n\n**If position goes underwater:**\n1. Review loss threshold (exit if >20%)\n2. Consider doubling down if fundamentals strong\n3. Never average down on red flags\n\n**Contact:**\n- Portfolio Manager: [Your contact]\n- Emergency: Withdraw all to hardware wallet\n\n---\n\n**Generated by 5-agent workflow:**\n✅ Portfolio Optimizer\n✅ DeFi Strategist  \n✅ Risk Analyst\n✅ Execution Specialist\n✅ Financial Analyst\n\n*Coordinated by Supervisor Agent*\n*Total Processing Time: 8.4 seconds*",
    "agent_type": "supervisor",
    "created_at": "2025-12-26T10:44:12Z"
  },
  "routing": {
    "intent": "complex_workflow",
    "confidence": 0.91,
    "handler": "supervisor",
    "reasoning": "User requesting complex multi-step strategy requiring coordination of multiple specialized agents",
    "total_latency_ms": 8420
  },
  "enrichment": {
    "workflow_id": "wf-20251226-104400-001",
    "workflow_status": "completed",
    "tasks_count": 5,
    "agents_involved": [
      "portfolio_optimizer",
      "defi_strategist",
      "risk_analyst",
      "execution_specialist",
      "financial_analyst"
    ]
  }
}
```

**Other Example Queries**:
- "Build me a complete NFT trading strategy"
- "Create governance proposal analysis and voting recommendation"
- "Design a MEV bot strategy from scratch"

---

### 4.3. General Conversation

**Intent**: Regular chat, Q&A, general assistance

**Input**:
```json
{
  "content": "Hello! What can you help me with?"
}
```

**Expected Output**:
```json
{
  "user_message": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Hello! What can you help me with?",
    "created_at": "2025-12-26T10:45:00Z"
  },
  "agent_message": {
    "id": "660e8400-e29b-41d4-a716-446655440031",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "Hello! 👋 I'm your AI-powered DeFi assistant with access to specialized tools and real-time data.\n\n**Here's what I can help you with:**\n\n**🔍 Protocol Discovery & Analysis**\n- Find DeFi protocols by category, chain, or criteria\n- Assess protocol safety and risk factors\n- Compare similar protocols and alternatives\n\n**📊 Market Intelligence (Hunter AI)**\n- Social sentiment analysis (Twitter, Reddit, Discord, News)\n- AI-powered price predictions (LSTM models)\n- Market risk signals and warnings\n- Trading signals with entry/exit prices\n- Chart pattern detection\n- Portfolio optimization (Modern Portfolio Theory)\n\n**⚡ DeFi Automation (ULTRA)**\n- Find arbitrage opportunities across DEXes\n- Compare flash loan protocols\n- Execute with MEV protection (Flashbots)\n- Control automated trading bots\n\n**🤖 Specialized Tasks**\n- Smart contract analysis\n- Liquidity pool analytics\n- Gas optimization strategies\n- Yield farming calculations\n- And much more...\n\n**Try asking things like:**\n- \"Find safe lending protocols on Ethereum\"\n- \"What's BTC sentiment on Twitter?\"\n- \"Predict ETH price for next week\"\n- \"Find arbitrage with $10k capital\"\n- \"Should I buy SOL? Give me signals\"\n\nWhat would you like to explore?",
    "agent_type": "chat",
    "created_at": "2025-12-26T10:45:01Z"
  },
  "routing": {
    "intent": "general_conversation",
    "confidence": 0.98,
    "handler": "general_chat",
    "reasoning": "User greeting and general inquiry, not requesting specific analysis or tools",
    "total_latency_ms": 420
  },
  "enrichment": null
}
```

**Other Example Queries**:
- "Explain how DeFi works"
- "What is impermanent loss?"
- "How do I get started with crypto?"

---

## Response Format Reference

All responses follow this unified structure:

```typescript
{
  user_message: {
    id: string (UUID)
    conversation_id: string (UUID)
    role: "user"
    content: string
    created_at: string (ISO 8601)
  }

  agent_message: {
    id: string (UUID)
    conversation_id: string (UUID)
    role: "assistant"
    content: string (Markdown formatted)
    agent_type: string (handler identifier)
    created_at: string (ISO 8601)
  }

  routing: {
    intent: string (one of 16 intent types)
    confidence: number (0.0-1.0)
    handler: string (handler name)
    agent_used?: string (optional)
    reasoning: string (why this intent was chosen)
    total_latency_ms: number
  }

  enrichment?: {
    // Handler-specific structured data
    // See individual examples above for field details
  }
}
```

---

## Testing Tips

**Authentication**:
```bash
# Get token first
curl -X POST http://localhost:8080/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
export TOKEN="your_jwt_token_here"
```

**Send Message**:
```bash
curl -X POST http://localhost:8080/api/v1/user/chat/conversations/{conversation_id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Find arbitrage opportunities with $10k"}'
```

**Create Conversation First**:
```bash
curl -X POST http://localhost:8080/api/v1/user/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Conversation"}'
```

---

## Intent Detection Tips

**Clear Intent Signals**:
- Use specific keywords: "find", "predict", "analyze", "show", "optimize"
- Mention token symbols: BTC, ETH, SOL, USDC
- Include criteria: "with low risk", "for 7 days", "with $10k"
- Be specific about actions: "buy", "sell", "start bot", "execute"

**Examples of Clear vs Ambiguous Queries**:

✅ Clear:
- "Predict BTC price for next 7 days" → hunter_price_prediction
- "Find lending protocols with TVL > $1B" → protocol_search
- "Start trading bot" → ultra_auto_executor

⚠️ Ambiguous (may require clarification):
- "What about ETH?" → Could be sentiment, price, risk, etc.
- "Show me protocols" → Need category/criteria
- "Help with trading" → Need specific task

---

**Last Updated**: December 26, 2025
**API Version**: 1.0
**Supported Intents**: 16
