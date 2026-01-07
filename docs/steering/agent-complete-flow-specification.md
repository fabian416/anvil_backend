# Agent Complete Flow Specification

**Version:** 1.0
**Created:** 2026-01-06
**Methodology:** MIT Systems Thinking + Stanford Design Thinking (CTO Framework)
**Purpose:** Complete end-to-end flow specification for each agent, handler, and execution path.

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [MCP Server Architecture](#2-mcp-server-architecture)
3. [Distillation Engine](#3-distillation-engine)
4. [ULTRA Agents (4 Intents)](#4-ultra-agents-4-intents)
5. [Hunter AI Agents (6 Intents)](#5-hunter-ai-agents-6-intents)
6. [DeFi Shortcuts (7 Intents)](#6-defi-shortcuts-7-intents)
7. [GraphRAG (3 Intents)](#7-graphrag-3-intents)
8. [Agent Squad (18 Agents)](#8-agent-squad-18-agents)
9. [Execute Actions (6 Actions)](#9-execute-actions-6-actions)
10. [Post-Processing Pipeline](#10-post-processing-pipeline)
11. [Test Matrices](#11-test-matrices)

---

## 1. System Overview

### 1.1 Architecture Layers
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE MESSAGE FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │ Message │───▶│ Distillation│───▶│ Orchestrator│───▶│   Handler   │               │
│  │ Receive │    │   Engine    │    │   Router    │    │  Dispatch   │               │
│  └─────────┘    └─────────────┘    └─────────────┘    └─────────────┘               │
│       │               │                   │                   │                      │
│       ▼               ▼                   ▼                   ▼                      │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │  Rate   │    │   Intent    │    │   Agent     │    │    MCP      │               │
│  │  Limit  │    │  Classify   │    │  Selection  │    │  Servers    │               │
│  └─────────┘    └─────────────┘    └─────────────┘    └─────────────┘               │
│                       │                   │                   │                      │
│                       ▼                   ▼                   ▼                      │
│                 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│                 │   Router    │    │   LLM       │    │  External   │               │
│                 │  Decision   │    │  Gateway    │    │   APIs      │               │
│                 └─────────────┘    └─────────────┘    └─────────────┘               │
│                       │                   │                   │                      │
│                       ▼                   ▼                   ▼                      │
│                 ┌──────────────────────────────────────────────────┐                │
│                 │              Post-Processing                      │                │
│                 │  - Source Collection                              │                │
│                 │  - Response Formatting                            │                │
│                 │  - Telemetry Logging                              │                │
│                 └──────────────────────────────────────────────────┘                │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Relationship Matrix

| Component | Depends On | Produces | MCP Used |
|-----------|------------|----------|----------|
| Distillation Engine | LLM Gateway | Route Decision | None |
| Intent Classifier | LLM Gateway | Intent + Entities | None |
| Handler Dispatch | Intent Result | Handler Selection | Multiple |
| ULTRA Tools | DEX APIs | Arbitrage/MEV data | CoinGecko, 1inch |
| Hunter AI | Sentiment APIs | Predictions | CoinGecko, Perplexity |
| DeFi Shortcuts | Protocol APIs | Quotes/Rates | Morpho, Aave, 1inch, LiFi |
| Agent Squad | LLM Gateway | Agent Response | Per-agent MCPs |
| Execute Actions | Wallet + DEX | Transactions | 1inch, LiFi |

---

## 2. MCP Server Architecture

### 2.1 Available MCP Servers (11 Servers)
**File:** `src/app/infrastructure/mcp/servers/`

| Server | Port | Purpose | Tools Count | Feature Flag |
|--------|------|---------|-------------|--------------|
| DeFiLlama | 8081 | TVL & Protocol Data | 5 | `defillama_enabled` |
| CoinGecko | 8082 | Market Data | 4 | `coingecko_enabled` |
| The Graph | 8083 | Blockchain Indexing | 3 | `thegraph_enabled` |
| Perplexity | 8084 | AI Search & Research | 2 | `perplexity_enabled` |
| 1inch | 8085 | DEX Aggregation | 6 | `oneinch_enabled` |
| Curve | 8086 | Stable Swaps | 4 | `curve_enabled` |
| Aave | 8087 | Lending Protocol | 5 | `aave_enabled` |
| Morpho | 8088 | Yield Optimization | 4 | `morpho_enabled` |
| Hyperliquid | 8089 | Perpetual Futures | 5 | `hyperliquid_enabled` |
| LayerZero | 8090 | Cross-chain Messaging | 3 | `layerzero_enabled` |
| Portfolio | 8091 | Wallet Tracking | 4 | `portfolio_enabled` |

### 2.2 MCP Server Manager
**File:** `src/app/infrastructure/mcp/manager.py`

```
MCPServerManager
├── register_server(server, port)
│   ├── Check global MCP enabled
│   ├── Check server-specific flag
│   └── Map tools to server
├── start_all()
│   └── Start all registered servers
├── get_all_tools() → List[Tool]
│   └── Aggregate tools from all servers
└── call_tool(tool_name, params) → Result
    ├── Route to correct server
    └── Execute tool handler
```

### 2.3 MCP Integration Pattern
```python
# Handler uses MCP via direct client injection
class SwapHandler:
    def __init__(
        self,
        oneinch_client: OneInchClient,     # MCP: 1inch
        lifi_client: LiFiClient,           # External: LiFi
        hyperliquid_client: HyperliquidClient,  # MCP: Hyperliquid
    ):
        ...

# Agent uses MCP via source collection
class ResearchAgentPerplexity:
    def __init__(
        self,
        llm_client: LLMClientGateway,
        perplexity_client: PerplexityMCPServer,  # MCP: Perplexity
    ):
        ...
```

---

## 3. Distillation Engine

### 3.1 Distillation Flow
**File:** `src/app/domain/services/distillation/engine.py`

```
DistillationEngine.distill(query, user_id, context)
│
├── Step 1: Check Enabled
│   └── If disabled → Pass through (FULL_LLM)
│
├── Step 2: Intent Classification
│   └── IntentClassifier.classify(query)
│       ├── Rule-based patterns (95% confidence)
│       │   ├── Price patterns: "price of ETH"
│       │   ├── Swap patterns: "swap 100 ETH"
│       │   ├── Risk patterns: "is Aave safe"
│       │   └── 20+ pattern categories
│       └── ML fallback (if no match)
│
├── Step 3: Complexity Assessment
│   └── ComplexityAssessor.assess()
│       ├── TRIVIAL → Economy tier
│       ├── SIMPLE → Economy tier
│       ├── MODERATE → Standard tier
│       ├── COMPLEX → Premium tier
│       └── EXPERT → Premium tier
│
├── Step 4: Entity Extraction
│   └── EntityExtractor.extract()
│       ├── Tokens: ETH, USDC, WBTC
│       ├── Protocols: Aave, Uniswap, Morpho
│       ├── Amounts: $1000, 100 ETH
│       └── Chains: Ethereum, Base, Arbitrum
│
├── Step 5: Cache Lookup
│   └── CacheManager.get()
│       ├── Exact match (hash-based)
│       └── Semantic match (embedding similarity)
│
├── Step 6: Static Response Check
│   └── StaticResponder.check_available()
│       └── Pre-defined templates for common queries
│
├── Step 7: Route Decision
│   └── DistillationRouter.route()
│       ├── REJECT → Off-topic, harmful
│       ├── CACHE → Previously seen query
│       ├── STATIC → Template response
│       ├── LIGHT_LLM → Simple queries
│       └── FULL_LLM → Complex queries
│
└── Step 8: Telemetry
    └── Log metrics for cost optimization
```

### 3.2 Route Decision Matrix

| Condition | Route | Model | MCP Needed |
|-----------|-------|-------|------------|
| Off-topic/harmful | REJECT | None | None |
| Cache hit | CACHE | None | None |
| Static template | STATIC | None | None |
| Transaction intent | FULL_LLM | Premium | Yes |
| Research/Analysis | FULL_LLM | Premium | Perplexity |
| Price check | LIGHT_LLM | Economy | CoinGecko |
| General chat | LIGHT_LLM | Economy | None |

---

## 4. ULTRA Agents (4 Intents)

### 4.1 ULTRA_ARBITRAGE
**Files:**
- `src/app/application/ultra/arbitrage_discovery.py`
- `src/app/application/ultra/dex_price_fetcher.py`

```
Intent: ULTRA_ARBITRAGE
Handler: ArbitrageDiscovery.find_opportunities()
│
├── Input: "find arbitrage opportunities"
│
├── Step 1: Multi-DEX Price Fetch
│   ├── MCP: CoinGecko (token prices)
│   ├── External: 1inch quotes
│   └── External: DEX subgraphs
│
├── Step 2: Opportunity Discovery
│   ├── 2-hop arbitrage (cross-DEX)
│   ├── 3-hop arbitrage (multi-token)
│   └── Triangle arbitrage (same DEX)
│
├── Step 3: Profitability Check
│   ├── min_profit_usd: $50
│   ├── min_profit_percentage: 0.5%
│   └── gas_cost_estimation
│
├── Step 4: Risk Assessment
│   ├── confidence_score: 0.7+
│   ├── slippage_tolerance: 1%
│   └── liquidity_check
│
├── Post-Processing:
│   ├── Sources: CoinGecko, 1inch, DEX
│   └── Format: ArbitrageOpportunity list
│
└── Output: {
      "opportunities": [...],
      "total_potential_profit": "$X",
      "recommended_action": "..."
    }
```

**Trade-off Analysis:**
| Approach | Benefit | Cost | Risk |
|----------|---------|------|------|
| Real-time DEX queries | Accurate prices | API rate limits | Latency |
| Cached price data | Fast response | Stale data | Missed opportunities |
| Simulated execution | Validate before tx | Gas overhead | False positives |

### 4.2 ULTRA_FLASH_LOANS
**Files:**
- `src/app/application/ultra/flash_loan_engine.py`
- `src/app/application/ultra/flash_loan_executor.py`

```
Intent: ULTRA_FLASH_LOANS
Handler: FlashLoanEngine.find_opportunities()
│
├── Input: "flash loan opportunities for ETH"
│
├── Step 1: Protocol Discovery
│   ├── Aave V3 (0.09% fee)
│   ├── Uniswap V3 (0.05% fee)
│   └── Balancer (no fee)
│
├── Step 2: Liquidity Check
│   ├── MCP: Aave (available liquidity)
│   └── External: DeFiLlama TVL
│
├── Step 3: Strategy Generation
│   ├── Arbitrage flash loan
│   ├── Collateral swap
│   └── Liquidation bot
│
├── Post-Processing:
│   ├── Sources: Aave MCP, DeFiLlama
│   └── Format: FlashLoanOpportunity
│
└── Output: {
      "protocol": "aave_v3",
      "max_loan": "10000 ETH",
      "fee": "0.09%",
      "strategies": [...]
    }
```

### 4.3 ULTRA_MEV_PROTECTION
**Files:**
- `src/app/application/ultra/mev_protection.py`
- `src/app/application/ultra/flashbots_client.py`

```
Intent: ULTRA_MEV_PROTECTION
Handler: MEVProtection.protect_transaction()
│
├── Input: "protect my swap from MEV"
│
├── Step 1: Transaction Analysis
│   └── Detect MEV vulnerability
│
├── Step 2: Protection Strategy
│   ├── Flashbots bundle
│   ├── Private mempool
│   └── Slippage optimization
│
├── Step 3: Route Selection
│   ├── External: Flashbots Protect RPC
│   └── External: Eden Network
│
├── Post-Processing:
│   ├── Sources: Flashbots API
│   └── Format: ProtectionResult
│
└── Output: {
      "protection_method": "flashbots",
      "estimated_savings": "$X",
      "bundle_hash": "0x..."
    }
```

### 4.4 ULTRA_AUTO_EXECUTOR
**Files:**
- `src/app/application/ultra/auto_executor.py`
- `src/app/application/ultra/risk_manager.py`

```
Intent: ULTRA_AUTO_EXECUTOR
Handler: AutoExecutor.configure_strategy()
│
├── Input: "auto-execute profitable arbs"
│
├── Step 1: Strategy Configuration
│   ├── min_profit: $100
│   ├── max_gas: 100 gwei
│   └── tokens: WETH, USDC, USDT
│
├── Step 2: Risk Parameters
│   ├── max_exposure: $10,000
│   ├── stop_loss: 5%
│   └── daily_limit: $50,000
│
├── Step 3: Monitoring Setup
│   ├── Price feeds: CoinGecko MCP
│   ├── Gas oracle: 1inch MCP
│   └── Alert webhook
│
├── Post-Processing:
│   ├── Sources: Configuration
│   └── Format: ExecutorConfig
│
└── Output: {
      "strategy_id": "uuid",
      "status": "active",
      "parameters": {...}
    }
```

---

## 5. Hunter AI Agents (6 Intents)

### 5.1 HUNTER_SENTIMENT
**Files:**
- `src/app/application/hunter/sentiment_aggregator.py`
- `src/app/application/hunter/twitter_sentiment.py`
- `src/app/application/hunter/reddit_sentiment.py`
- `src/app/application/hunter/discord_sentiment.py`
- `src/app/application/hunter/news_sentiment.py`

```
Intent: HUNTER_SENTIMENT
Handler: SentimentAggregator.aggregate()
│
├── Input: "what's the sentiment on ETH"
│
├── Step 1: Multi-Source Collection
│   ├── Twitter: TwitterSentimentAnalyzer
│   │   └── Simulated (requires paid API)
│   ├── Reddit: RedditSentimentAnalyzer
│   │   └── Fallback mode (requires OAuth2)
│   ├── Discord: DiscordSentimentAnalyzer
│   │   └── Simulated (requires bot access)
│   └── News: NewsSentimentAnalyzer
│       └── RSS feeds (CoinDesk, CoinTelegraph) ✅
│
├── Step 2: Weighted Aggregation
│   ├── Twitter: 35%
│   ├── Reddit: 25%
│   ├── Discord: 20%
│   └── News: 20%
│
├── Step 3: Confidence Calculation
│   └── avg_confidence × source_count
│
├── Post-Processing:
│   ├── Sources: News RSS, LLM analysis
│   └── Format: AggregatedSentiment
│
└── Output: {
      "token": "ETH",
      "overall_score": 72,
      "sentiment": "bullish",
      "confidence": 0.85,
      "breakdown": {
        "twitter": {"score": 75, "status": "simulated"},
        "reddit": {"score": 68, "status": "fallback"},
        "news": {"score": 71, "status": "real"}
      }
    }
```

**MCP Usage:**
| Source | MCP Server | Status |
|--------|------------|--------|
| Twitter | None | Simulated |
| Reddit | None | Fallback |
| Discord | None | Simulated |
| News | RSS feeds | Real |
| Price context | CoinGecko | Real |

### 5.2 HUNTER_PRICE_PREDICTION
**Files:**
- `src/app/application/hunter/lstm_price_predictor.py`
- `src/app/application/hunter/price_data_service.py`

```
Intent: HUNTER_PRICE_PREDICTION
Handler: LSTMPricePredictor.predict()
│
├── Input: "predict ETH price next week"
│
├── Step 1: Historical Data Fetch
│   └── MCP: CoinGecko (OHLCV data)
│       └── 30-day historical prices
│
├── Step 2: LSTM Model Inference
│   ├── Feature engineering
│   │   ├── Price momentum
│   │   ├── Volume changes
│   │   └── Technical indicators
│   └── Model prediction
│
├── Step 3: Confidence Scoring
│   ├── Historical accuracy
│   ├── Market volatility
│   └── Data quality
│
├── Post-Processing:
│   ├── Sources: CoinGecko MCP
│   └── Format: PricePrediction
│
└── Output: {
      "token": "ETH",
      "current_price": 3024.50,
      "predicted_price": 3150.00,
      "predicted_change": "+4.15%",
      "timeframe": "7 days",
      "confidence": 0.72,
      "support_levels": [2950, 2850],
      "resistance_levels": [3200, 3350]
    }
```

### 5.3 HUNTER_RISK_SIGNALS
**File:** `src/app/application/hunter/risk_analyzer.py`

```
Intent: HUNTER_RISK_SIGNALS
Handler: RiskAnalyzer.analyze()
│
├── Input: "show ETH risk signals"
│
├── Step 1: Market Data Collection
│   └── MCP: CoinGecko (volatility, volume)
│
├── Step 2: On-Chain Analysis
│   └── MCP: The Graph (whale movements)
│
├── Step 3: Risk Scoring
│   ├── Volatility risk
│   ├── Liquidity risk
│   ├── Concentration risk
│   └── Technical risk
│
├── Post-Processing:
│   ├── Sources: CoinGecko, The Graph
│   └── Format: RiskSignals
│
└── Output: {
      "token": "ETH",
      "overall_risk": "medium",
      "risk_score": 45,
      "signals": [
        {"type": "volatility", "level": "high", "details": "..."},
        {"type": "whale_activity", "level": "medium", "details": "..."}
      ]
    }
```

### 5.4 HUNTER_TRADING_SIGNALS
**File:** `src/app/application/hunter/trading_signal_generator.py`

```
Intent: HUNTER_TRADING_SIGNALS
Handler: TradingSignalGenerator.generate()
│
├── Input: "trading signals for ETH 4h timeframe"
│
├── Step 1: OHLCV Data
│   └── MCP: CoinGecko (candle data)
│
├── Step 2: Technical Indicators
│   ├── RSI (Relative Strength Index)
│   ├── MACD (Moving Average Convergence)
│   ├── Bollinger Bands
│   └── Volume Profile
│
├── Step 3: Signal Generation
│   ├── Entry points
│   ├── Exit points
│   └── Stop-loss levels
│
├── Post-Processing:
│   ├── Sources: CoinGecko MCP
│   └── Format: TradingSignal
│
└── Output: {
      "token": "ETH",
      "timeframe": "4h",
      "signal": "buy",
      "strength": 0.75,
      "entry_price": 3020,
      "target_price": 3150,
      "stop_loss": 2950,
      "indicators": {...}
    }
```

### 5.5 HUNTER_PATTERNS
**File:** `src/app/application/hunter/pattern_recognition.py`

```
Intent: HUNTER_PATTERNS
Handler: PatternRecognizer.detect()
│
├── Input: "chart patterns for BTC"
│
├── Step 1: Candlestick Data
│   └── MCP: CoinGecko (daily OHLCV)
│
├── Step 2: Pattern Detection
│   ├── Head & Shoulders
│   ├── Double Top/Bottom
│   ├── Triangle patterns
│   ├── Cup & Handle
│   └── Wedge patterns
│
├── Step 3: Pattern Validation
│   ├── Historical accuracy
│   └── Current market context
│
├── Post-Processing:
│   ├── Sources: CoinGecko MCP
│   └── Format: PatternResult
│
└── Output: {
      "token": "BTC",
      "patterns_detected": [
        {
          "pattern": "ascending_triangle",
          "confidence": 0.82,
          "breakout_target": 45000,
          "invalidation": 41000
        }
      ]
    }
```

### 5.6 HUNTER_PORTFOLIO
**File:** `src/app/application/hunter/portfolio_optimizer.py`

```
Intent: HUNTER_PORTFOLIO
Handler: PortfolioOptimizer.optimize()
│
├── Input: "optimize my DeFi portfolio"
│
├── Step 1: Current Holdings Analysis
│   └── MCP: Portfolio (wallet tracking)
│
├── Step 2: Market Analysis
│   └── MCP: CoinGecko, DeFiLlama
│
├── Step 3: Optimization Strategy
│   ├── Mean-variance optimization
│   ├── Risk parity
│   └── Sharpe ratio maximization
│
├── Step 4: Recommendations
│   ├── Rebalancing suggestions
│   └── Yield opportunities
│
├── Post-Processing:
│   ├── Sources: Portfolio MCP, CoinGecko, DeFiLlama
│   └── Format: PortfolioOptimization
│
└── Output: {
      "current_allocation": {...},
      "optimal_allocation": {...},
      "rebalancing_trades": [...],
      "expected_improvement": "+15% Sharpe"
    }
```

---

## 6. DeFi Shortcuts (7 Intents)

### 6.1 LENDING
**File:** `src/app/application/chat/handlers/lending_handler.py`

```
Intent: LENDING
Handler: LendingHandler.handle()
│
├── Input: "deposit 100 USDC into Morpho"
│
├── Step 1: Entity Extraction
│   ├── amount: 100
│   ├── token: USDC
│   └── protocol: Morpho
│
├── Step 2: Protocol Data Fetch
│   ├── MCP: Morpho (vault info, APY)
│   └── MCP: Aave (fallback rates)
│
├── Step 3: Best Vault Selection
│   ├── Compare APYs
│   ├── Check TVL (safety)
│   └── Verify liquidity
│
├── Step 4: Quote Generation
│   ├── Expected yield
│   ├── Gas estimate
│   └── Transaction data
│
├── Post-Processing:
│   ├── Sources: Morpho MCP, Aave MCP
│   └── Format: LendingQuote
│
├── Output for /messages:
│   {
│     "content": "Ready to deposit 100 USDC into Morpho...",
│     "pending_action": {
│       "action_type": "deposit",
│       "protocol": "morpho",
│       "token": "USDC",
│       "amount": "100"
│     }
│   }
│
└── Output for /execute:
    → See Execute Actions section
```

### 6.2 MONEY_MARKET
**File:** `src/app/application/chat/handlers/money_market_handler.py`

```
Intent: MONEY_MARKET
Handler: MoneyMarketHandler.compare_rates()
│
├── Input: "compare lending rates for ETH"
│
├── Step 1: Multi-Protocol Query
│   ├── MCP: Morpho (vault APYs)
│   ├── MCP: Aave (supply rates)
│   └── External: DeFiLlama (Compound, etc.)
│
├── Step 2: Rate Normalization
│   ├── Base APY
│   ├── Reward APY
│   └── Net APY
│
├── Step 3: Ranking
│   ├── Sort by net APY
│   ├── Include safety scores
│   └── Highlight best options
│
├── Post-Processing:
│   ├── Sources: Morpho, Aave, DeFiLlama MCPs
│   └── Format: RateComparison
│
└── Output: {
      "token": "ETH",
      "rates": [
        {"protocol": "Morpho", "apy": "4.5%", "tvl": "$500M"},
        {"protocol": "Aave V3", "apy": "3.8%", "tvl": "$2B"},
        {"protocol": "Compound", "apy": "3.2%", "tvl": "$1.5B"}
      ],
      "recommendation": "Morpho offers best yield with good safety"
    }
```

### 6.3 SWAP
**File:** `src/app/application/chat/handlers/swap_handler.py`

```
Intent: SWAP
Handler: SwapHandler.get_swap_quote()
│
├── Input: "swap 1 ETH to USDC"
│
├── Step 1: Cross-Chain Detection
│   └── from_chain == to_chain?
│
├── Step 2: Aggregator Selection
│   ├── Same-chain: MCP: 1inch
│   └── Cross-chain: External: LiFi
│
├── Step 3: Quote Fetch
│   ├── Get best route
│   ├── Calculate output amount
│   ├── Estimate gas
│   └── Calculate price impact
│
├── Post-Processing:
│   ├── Sources: 1inch MCP or LiFi API
│   └── Format: SwapQuote
│
├── Output for /messages:
│   {
│     "content": "Ready to swap 1 ETH for ~3,024.50 USDC...",
│     "pending_action": {
│       "action_type": "swap",
│       "from_token": "ETH",
│       "to_token": "USDC",
│       "amount": "1"
│     }
│   }
│
└── Output for /execute:
    → See Execute Actions section
```

### 6.4 BALANCE (User Only)
**File:** `src/app/application/chat/handlers/portfolio_handler.py`

```
Intent: BALANCE
Handler: PortfolioHandler.get_balance()
│
├── Input: "what's my balance"
│
├── Step 1: Wallet Lookup
│   └── Privy: Get user wallet address
│
├── Step 2: Balance Fetch
│   ├── MCP: Portfolio (multi-chain balances)
│   └── MCP: CoinGecko (USD values)
│
├── Post-Processing:
│   ├── Sources: Portfolio MCP, CoinGecko MCP
│   └── Format: BalanceList
│
└── Output: {
      "wallet": "0x...",
      "total_usd": "$15,234.50",
      "balances": [
        {"token": "ETH", "amount": "3.5", "usd": "$10,585.75"},
        {"token": "USDC", "amount": "4648.75", "usd": "$4,648.75"}
      ]
    }
```

### 6.5 PORTFOLIO (User Only)
**File:** `src/app/application/chat/handlers/portfolio_handler.py`

```
Intent: PORTFOLIO
Handler: PortfolioHandler.get_full_portfolio()
│
├── Input: "show my portfolio"
│
├── Step 1: Wallet Lookup
│   └── Privy: Get all user wallets
│
├── Step 2: Multi-Asset Fetch
│   ├── MCP: Portfolio (balances)
│   ├── MCP: CoinGecko (prices)
│   ├── MCP: Aave (supplied assets)
│   └── MCP: Morpho (vault positions)
│
├── Step 3: Position Analysis
│   ├── Spot holdings
│   ├── Lending positions
│   ├── LP positions
│   └── Staking positions
│
├── Post-Processing:
│   ├── Sources: Multiple MCPs
│   └── Format: Portfolio
│
└── Output: {
      "total_value": "$50,234.50",
      "positions": {
        "spot": [...],
        "lending": [...],
        "lp": [...],
        "staking": [...]
      },
      "allocation": {...},
      "pnl_24h": "+2.5%"
    }
```

### 6.6 ACTIVITY (User Only)
**File:** `src/app/application/chat/handlers/activity_handler.py`

```
Intent: ACTIVITY
Handler: ActivityHandler.get_activity()
│
├── Input: "show my transaction history"
│
├── Step 1: Wallet Lookup
│   └── Privy: Get user wallet address
│
├── Step 2: Transaction Fetch
│   └── MCP: The Graph (tx history)
│
├── Step 3: Transaction Classification
│   ├── Swaps
│   ├── Transfers
│   ├── Approvals
│   └── Contract interactions
│
├── Post-Processing:
│   ├── Sources: The Graph MCP
│   └── Format: TransactionList
│
└── Output: {
      "recent_transactions": [
        {
          "hash": "0x...",
          "type": "swap",
          "from": "1 ETH",
          "to": "3024.50 USDC",
          "timestamp": "2h ago"
        }
      ]
    }
```

### 6.7 RECEIVE (User Only)
**File:** `src/app/application/chat/handlers/receive_handler.py`

```
Intent: RECEIVE
Handler: ReceiveHandler.get_receive_info()
│
├── Input: "how do I receive ETH"
│
├── Step 1: Wallet Lookup
│   └── Privy: Get user wallet address
│
├── Step 2: ENS Resolution (if available)
│   └── External: ENS resolver
│
├── Step 3: QR Code Generation
│   └── Generate QR for wallet address
│
├── Post-Processing:
│   ├── Sources: Privy, ENS
│   └── Format: ReceiveInfo
│
└── Output: {
      "address": "0x...",
      "ens": "user.eth",
      "qr_code": "data:image/png;base64,...",
      "supported_networks": ["Ethereum", "Base", "Arbitrum"]
    }
```

---

## 7. GraphRAG (3 Intents)

### 7.1 PROTOCOL_SEARCH
**File:** `src/app/application/chat/graph_search_handler.py`

```
Intent: PROTOCOL_SEARCH
Handler: ChatGraphSearchHandler.search_protocols_from_chat()
│
├── Input: "find low-risk staking on Ethereum"
│
├── Step 1: Query Embedding
│   └── LLM: Generate query embedding
│
├── Step 2: Hybrid Search
│   ├── Vector similarity (semantic)
│   └── Graph traversal (relationships)
│
├── Step 3: Risk Filtering
│   └── Apply user preferences
│
├── Step 4: Ranking & Recommendations
│   ├── Relevance score
│   ├── Risk score
│   └── TVL/APY metrics
│
├── Post-Processing:
│   ├── Sources: GraphRAG Knowledge Base
│   └── Format: ProtocolSearchResult
│
└── Output: {
      "results": [
        {
          "protocol": "Lido",
          "similarity": 0.92,
          "risk_score": 25,
          "risk_level": "low",
          "tvl": "$30B",
          "apy": "4.2%"
        }
      ],
      "recommendations": [...]
    }
```

### 7.2 RISK_ASSESSMENT
**File:** `src/app/application/chat/risk_insights_handler.py`

```
Intent: RISK_ASSESSMENT
Handler: ChatRiskInsightsHandler.get_protocol_risk_from_chat()
│
├── Input: "is Aave safe?"
│
├── Step 1: Protocol Lookup
│   └── GraphRAG: Find protocol entity
│
├── Step 2: Risk Factor Analysis
│   ├── Smart contract risk
│   ├── Audit history
│   ├── TVL stability
│   ├── Team/governance
│   └── Historical incidents
│
├── Step 3: ML Risk Scoring
│   └── Risk prediction model
│
├── Step 4: Alternatives (if risky)
│   └── Safer protocol suggestions
│
├── Post-Processing:
│   ├── Sources: GraphRAG KB, Risk Model
│   └── Format: RiskAnalysis
│
└── Output: {
      "protocol": "Aave",
      "risk_score": 18,
      "risk_level": "low",
      "factors": [
        {"factor": "audits", "impact": "positive", "count": 15},
        {"factor": "tvl", "impact": "positive", "value": "$10B"}
      ],
      "recommendation": "Aave is considered safe..."
    }
```

### 7.3 SIMILAR_PROTOCOLS
**File:** `src/app/application/chat/graph_search_handler.py`

```
Intent: SIMILAR_PROTOCOLS
Handler: ChatGraphSearchHandler.find_similar()
│
├── Input: "what's similar to Uniswap"
│
├── Step 1: Base Protocol Lookup
│   └── GraphRAG: Find Uniswap entity
│
├── Step 2: Graph Traversal
│   ├── Same category (DEX)
│   ├── Same chain
│   └── Similar features
│
├── Step 3: Similarity Scoring
│   ├── Feature overlap
│   ├── Risk profile
│   └── User reviews
│
├── Post-Processing:
│   ├── Sources: GraphRAG KB
│   └── Format: SimilarProtocols
│
└── Output: {
      "base_protocol": "Uniswap",
      "similar": [
        {"protocol": "SushiSwap", "similarity": 0.85},
        {"protocol": "Curve", "similarity": 0.72}
      ]
    }
```

---

## 8. Agent Squad (18 Agents)

### 8.1 Agent Overview

| Agent | Type | Model | MCP Used | Primary Function |
|-------|------|-------|----------|------------------|
| CHAT | Core | gemini-2.0-flash | None | General conversation |
| HUNTER_AI | Core | gemini-2.0-flash | CoinGecko | Market sentiment |
| RESEARCH | Core | gemini-2.0-flash | Perplexity | Deep analysis |
| EXECUTION | Core | gemini-2.0-flash | 1inch, Privy | Transaction execution |
| RISK_ANALYZER | Core | gemini-2.0-flash | GraphRAG | Risk assessment |
| PORTFOLIO | Core | gemini-2.0-flash | Portfolio, CoinGecko | Portfolio management |
| TAX_OPTIMIZER | Core | gemini-2.0-flash | Portfolio | Tax optimization |
| DEFI_YIELD | Core | gemini-2.0-flash | Morpho, Aave | Yield farming |
| SECURITY_AUDITOR | Core | gemini-2.0-flash | None (Slither) | Contract auditing |
| GAS_OPTIMIZER | Core | gemini-2.0-flash | 1inch | Gas optimization |
| COMPLIANCE_MONITOR | Enterprise | gemini-2.0-flash | Chainalysis | AML/KYC |
| MULTISIG_COORDINATOR | Enterprise | gemini-2.0-flash | Gnosis Safe | Multi-sig ops |
| ALERT_MONITORING | Enterprise | gemini-2.0-flash | Multiple | Real-time alerts |
| CRISIS_MANAGER | Enterprise | gemini-2.0-flash | Multiple | Emergency response |
| BRIDGE_CROSSCHAIN | Advanced | gemini-2.0-flash | LayerZero, LiFi | Cross-chain ops |
| LENDING_BORROWING | Advanced | gemini-2.0-flash | Aave, Morpho | Lending/borrowing |
| NFT_ASSET_MANAGER | Advanced | gemini-2.0-flash | OpenSea | NFT management |
| DAO_GOVERNANCE | Advanced | gemini-2.0-flash | Snapshot | DAO voting |

### 8.2 Agent Execution Flow
**File:** `src/app/infrastructure/adapters/agent_squad/agents/`

```
AgentGateway.execute(conversation_id, message, context)
│
├── Step 1: Source Collection Setup
│   └── Initialize sources list
│
├── Step 2: External Data Fetch (if needed)
│   ├── MCP: Call relevant MCP servers
│   └── External: Call external APIs
│
├── Step 3: Context Building
│   ├── System prompt
│   ├── Conversation history
│   └── Tool results
│
├── Step 4: LLM Call
│   └── LLMClientGateway.chat()
│       ├── Primary: Vertex AI (gemini-2.0-flash-exp)
│       └── Fallback: DeepInfra (llama-3.1-70b)
│
├── Step 5: Response Processing
│   ├── Extract content
│   ├── Parse tool calls
│   └── Format output
│
├── Step 6: Source Finalization
│   ├── Add LLM source
│   ├── Add API sources
│   └── Add MCP sources
│
└── Return: AgentResponse {
      content: str,
      agent_type: AgentType,
      tools_used: list[str],
      sources: list[SourceInfo],
      metadata: dict
    }
```

### 8.3 SPECIALIST_TASK Flow
**File:** `src/app/domain/services/agent_squad/agent_orchestrator.py`

```
Intent: SPECIALIST_TASK
Orchestrator: AgentOrchestrator.route_message()
│
├── Step 1: Intent Classification
│   └── Classify intent with LLM
│       └── Returns: agent_type, confidence
│
├── Step 2: Confidence Check
│   └── confidence >= 0.85 ? Use agent : Fallback to CHAT
│
├── Step 3: Agent Selection
│   └── Select best agent for task
│
├── Step 4: Agent Execution
│   └── agent.execute(message, context)
│
└── Return: AgentResponse
```

### 8.4 COMPLEX_WORKFLOW Flow
**File:** `src/app/application/agent_squad/commands/execute_supervisor_workflow.py`

```
Intent: COMPLEX_WORKFLOW
Supervisor: SupervisorCoordinator.coordinate()
│
├── Step 1: Task Decomposition
│   └── LLM breaks complex task into subtasks
│
├── Step 2: Agent Assignment
│   └── Assign agents to subtasks
│       ├── RESEARCH → Protocol research
│       ├── RISK_ANALYZER → Risk assessment
│       ├── PORTFOLIO → Allocation
│       └── CHAT → Summary
│
├── Step 3: Parallel Execution
│   └── Execute independent subtasks in parallel
│
├── Step 4: Dependency Resolution
│   └── Execute dependent subtasks sequentially
│
├── Step 5: Result Aggregation
│   └── Combine all agent outputs
│
├── Step 6: Final Synthesis
│   └── CHAT agent synthesizes final response
│
└── Return: WorkflowResult {
      final_response: str,
      agents_used: list[AgentType],
      subtask_results: list[AgentResponse]
    }
```

---

## 9. Execute Actions (6 Actions)

### 9.1 Execute Flow Overview
**File:** `src/app/application/chat/commands/execute_action.py`

```
POST /api/v1/user/chat/conversations/{id}/execute
│
├── Step 1: Authentication
│   └── JWT validation
│
├── Step 2: Conversation Verification
│   └── User owns conversation
│
├── Step 3: Wallet Lookup
│   └── Privy: Get user wallet
│
├── Step 4: Action Routing
│   ├── swap → _handle_swap()
│   ├── deposit → _handle_deposit()
│   ├── withdraw → _handle_withdraw()
│   ├── transfer → _handle_transfer()
│   ├── approve → _handle_approve()
│   └── bridge → _handle_bridge()
│
├── Step 5: Simulation/Execution
│   ├── confirmed=false → Return simulation
│   └── confirmed=true → Execute transaction
│
└── Return: ActionResult
```

### 9.2 SWAP Action
```
Action: swap
│
├── MCP Used:
│   ├── 1inch MCP (same-chain quotes)
│   └── External: LiFi API (cross-chain)
│
├── Simulation (confirmed=false):
│   ├── Get quote from aggregator
│   ├── Calculate output amount
│   ├── Estimate gas
│   └── Calculate price impact
│
├── Execution (confirmed=true):
│   ├── Build transaction
│   ├── Sign via Privy
│   └── Submit to network
│
├── Safety Limits:
│   └── MAX_SWAP_VALUE_USD = $50,000
│
└── Output: {
      "action_type": "swap",
      "status": "pending/awaiting_confirmation",
      "simulation": {...},
      "transaction": {"hash": "0x..."}
    }
```

### 9.3 DEPOSIT Action
```
Action: deposit
│
├── MCP Used:
│   ├── Morpho MCP (vault info)
│   └── Aave MCP (pool info)
│
├── Simulation:
│   ├── Get vault/pool APY
│   ├── Calculate expected shares
│   └── Estimate gas
│
├── Execution:
│   ├── Build deposit transaction
│   ├── Sign via Privy
│   └── Submit to network
│
├── Safety Limits:
│   └── MAX_DEPOSIT_VALUE_USD = $100,000
│
└── Output: {
      "action_type": "deposit",
      "protocol": "morpho",
      "vault_address": "0x...",
      "apy": "4.5%"
    }
```

### 9.4 WITHDRAW Action
```
Action: withdraw
│
├── MCP Used:
│   ├── Morpho MCP (position info)
│   └── Aave MCP (position info)
│
├── Simulation:
│   ├── Get current position
│   ├── Calculate withdrawal amount
│   └── Estimate gas
│
├── Execution:
│   ├── Build withdrawal transaction
│   ├── Sign via Privy
│   └── Submit to network
│
└── Output: {
      "action_type": "withdraw",
      "amount": "1000 USDC",
      "received": "1045.23 USDC"
    }
```

### 9.5 TRANSFER Action
```
Action: transfer
│
├── MCP Used:
│   └── None (direct ERC20/ETH transfer)
│
├── Simulation:
│   ├── Validate recipient address
│   ├── Check balance
│   └── Estimate gas
│
├── Execution:
│   ├── Build transfer transaction
│   ├── Sign via Privy
│   └── Submit to network
│
├── Safety Limits:
│   └── MAX_TRANSFER_VALUE_USD = $10,000
│
└── Output: {
      "action_type": "transfer",
      "recipient": "0x...",
      "amount": "100 USDC"
    }
```

### 9.6 APPROVE Action
```
Action: approve
│
├── MCP Used:
│   └── None (direct ERC20 approve)
│
├── Simulation:
│   ├── Validate spender
│   ├── Check current allowance
│   └── Warning if unlimited
│
├── Execution:
│   ├── Build approve transaction
│   ├── Sign via Privy
│   └── Submit to network
│
└── Output: {
      "action_type": "approve",
      "token": "USDC",
      "spender": "0x...",
      "amount": "unlimited"
    }
```

### 9.7 BRIDGE Action
```
Action: bridge
│
├── MCP Used:
│   └── External: LiFi API (cross-chain)
│
├── Simulation:
│   ├── Get bridge quote
│   ├── Estimate receive amount
│   ├── Estimate time (10-30 min)
│   └── Calculate bridge fee
│
├── Execution:
│   ├── Build bridge transaction
│   ├── Sign via Privy
│   └── Submit to source chain
│
└── Output: {
      "action_type": "bridge",
      "from_chain": "ethereum",
      "to_chain": "arbitrum",
      "estimated_time": "~15 minutes"
    }
```

---

## 10. Post-Processing Pipeline

### 10.1 Source Collection Pattern
**File:** `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

```python
# Every handler/agent collects sources
sources = []

# Add API sources
sources.append(create_api_source(
    source_name="CoinGecko",
    url="https://api.coingecko.com/...",
    endpoint="/simple/price",
    fetched_at=datetime.utcnow(),
))

# Add MCP sources
sources.append(create_mcp_source(
    mcp_server_name="morpho",
    tool_name="get_vault_info",
))

# Add LLM source
sources.append(create_llm_source(
    model="gemini-2.0-flash-exp",
    provider="Vertex AI",
))
```

### 10.2 Response Formatting

```python
# Standard response format
return {
    "user_message": {...},
    "agent_message": {
        "content": response_content,
        "sources": [s.to_dict() for s in sources],
    },
    "routing": {
        "intent": intent.value,
        "confidence": confidence,
        "handler": handler_name,
    },
    "enrichment": {
        # Handler-specific data
    }
}
```

### 10.3 Telemetry Logging

```python
# Log for cost optimization and debugging
telemetry = DistillationTelemetry(
    request_id=uuid4(),
    intent=intent.value,
    route_type=route.value,
    llm_model_used=model,
    tokens_used=tokens,
    latency_ms=latency,
    cache_hit=cache_hit,
)
await telemetry_service.log(telemetry)
```

---

## 11. Test Matrices

### 11.1 ULTRA Intent Tests
| Test ID | Input | Expected Intent | MCP Used | Expected Output |
|---------|-------|-----------------|----------|-----------------|
| U001 | "find arbitrage opportunities" | ULTRA_ARBITRAGE | CoinGecko, 1inch | Opportunity list |
| U002 | "flash loan for ETH" | ULTRA_FLASH_LOANS | Aave | Loan options |
| U003 | "protect my swap from MEV" | ULTRA_MEV_PROTECTION | None (Flashbots) | Protection strategy |
| U004 | "auto-execute profitable trades" | ULTRA_AUTO_EXECUTOR | Multiple | Config confirmation |

### 11.2 Hunter AI Intent Tests
| Test ID | Input | Expected Intent | MCP Used | Expected Output |
|---------|-------|-----------------|----------|-----------------|
| H001 | "sentiment on ETH" | HUNTER_SENTIMENT | CoinGecko, News | Sentiment score |
| H002 | "predict BTC price" | HUNTER_PRICE_PREDICTION | CoinGecko | Price prediction |
| H003 | "risk signals for SOL" | HUNTER_RISK_SIGNALS | CoinGecko, Graph | Risk signals |
| H004 | "trading signals ETH 4h" | HUNTER_TRADING_SIGNALS | CoinGecko | Trading signals |
| H005 | "chart patterns BTC" | HUNTER_PATTERNS | CoinGecko | Pattern detection |
| H006 | "optimize my portfolio" | HUNTER_PORTFOLIO | Portfolio, CoinGecko | Optimization |

### 11.3 DeFi Shortcut Tests
| Test ID | Input | Expected Intent | MCP Used | Expected Output |
|---------|-------|-----------------|----------|-----------------|
| D001 | "deposit 100 USDC Morpho" | LENDING | Morpho | Deposit quote |
| D002 | "compare ETH rates" | MONEY_MARKET | Morpho, Aave | Rate comparison |
| D003 | "swap 1 ETH to USDC" | SWAP | 1inch | Swap quote |
| D004 | "my balance" | BALANCE | Portfolio | Balance list |
| D005 | "show portfolio" | PORTFOLIO | Portfolio, Multiple | Full portfolio |
| D006 | "transaction history" | ACTIVITY | The Graph | Transaction list |
| D007 | "receive ETH" | RECEIVE | None | Address + QR |

### 11.4 Execute Action Tests
| Test ID | Action | Confirmed | Expected Status | MCP Used |
|---------|--------|-----------|-----------------|----------|
| E001 | swap | false | awaiting_confirmation | 1inch |
| E002 | swap | true | pending | 1inch, Privy |
| E003 | deposit | false | awaiting_confirmation | Morpho |
| E004 | deposit | true | pending | Morpho, Privy |
| E005 | bridge | false | awaiting_confirmation | LiFi |
| E006 | bridge | true | pending | LiFi, Privy |

---

## 12. Quick Reference

### 12.1 Intent → Handler → MCP Mapping

| Intent | Handler | Primary MCP | Fallback MCP |
|--------|---------|-------------|--------------|
| ULTRA_ARBITRAGE | ArbitrageDiscovery | CoinGecko | 1inch |
| ULTRA_FLASH_LOANS | FlashLoanEngine | Aave | Morpho |
| ULTRA_MEV_PROTECTION | MEVProtection | None | None |
| ULTRA_AUTO_EXECUTOR | AutoExecutor | Multiple | None |
| HUNTER_SENTIMENT | SentimentAggregator | CoinGecko | News RSS |
| HUNTER_PRICE_PREDICTION | LSTMPricePredictor | CoinGecko | None |
| HUNTER_RISK_SIGNALS | RiskAnalyzer | CoinGecko | The Graph |
| HUNTER_TRADING_SIGNALS | TradingSignalGenerator | CoinGecko | None |
| HUNTER_PATTERNS | PatternRecognizer | CoinGecko | None |
| HUNTER_PORTFOLIO | PortfolioOptimizer | Portfolio | CoinGecko |
| LENDING | LendingHandler | Morpho | Aave |
| MONEY_MARKET | MoneyMarketHandler | Morpho, Aave | DeFiLlama |
| SWAP | SwapHandler | 1inch | LiFi |
| BALANCE | PortfolioHandler | Portfolio | CoinGecko |
| PORTFOLIO | PortfolioHandler | Portfolio | Multiple |
| ACTIVITY | ActivityHandler | The Graph | None |
| RECEIVE | ReceiveHandler | None | ENS |
| PROTOCOL_SEARCH | GraphRAG | None | None |
| RISK_ASSESSMENT | GraphRAG | None | None |
| SIMILAR_PROTOCOLS | GraphRAG | None | None |
| SPECIALIST_TASK | AgentOrchestrator | Per-agent | None |
| COMPLEX_WORKFLOW | SupervisorCoordinator | Multiple | None |
| GENERAL_CONVERSATION | ChatAgent | None | None |

### 12.2 Execute Action → Integration Mapping

| Action | Primary Integration | Wallet | Safety Limit |
|--------|---------------------|--------|--------------|
| swap | 1inch / LiFi | Privy | $50,000 |
| deposit | Morpho / Aave | Privy | $100,000 |
| withdraw | Morpho / Aave | Privy | N/A |
| transfer | Direct ERC20 | Privy | $10,000 |
| approve | Direct ERC20 | Privy | N/A |
| bridge | LiFi | Privy | N/A |

---

## 13. Cost Analysis

### 13.1 LLM Token Costs Per Agent

All agents use **gemini-2.0-flash-exp** (Vertex AI native name).

| Agent | Max Tokens | Temp | Est. Input | Est. Output | Total/Req | Vertex AI Cost | DeepInfra Cost |
|-------|------------|------|------------|-------------|-----------|----------------|----------------|
| **Chat** | 1000 | 0.7 | ~300 | ~200 | ~500 | $0.00013 | $0.00004 |
| **Hunter AI** | 1500 | 0.3 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **Research** | 2000 | 0.2 | ~700 | ~400 | ~1100 | $0.00023 | $0.000088 |
| **Execution** | 1000 | 0.1 | ~400 | ~200 | ~600 | $0.00012 | $0.000048 |
| **Risk Analyzer** | 1500 | 0.2 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **Portfolio** | 2000 | 0.3 | ~600 | ~400 | ~1000 | $0.00021 | $0.00008 |
| **Tax Optimizer** | 1500 | 0.2 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **DeFi Yield** | 1500 | 0.3 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **Security Auditor** | 2000 | 0.1 | ~700 | ~400 | ~1100 | $0.00023 | $0.000088 |
| **Gas Optimizer** | 1000 | 0.2 | ~300 | ~200 | ~500 | $0.00013 | $0.00004 |
| **Compliance Monitor** | 2000 | 0.1 | ~700 | ~400 | ~1100 | $0.00023 | $0.000088 |
| **MultiSig Coordinator** | 1500 | 0.2 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **Alert Monitoring** | 1000 | 0.3 | ~400 | ~200 | ~600 | $0.00012 | $0.000048 |
| **Crisis Manager** | 2000 | 0.1 | ~700 | ~400 | ~1100 | $0.00023 | $0.000088 |
| **Bridge Crosschain** | 1500 | 0.2 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **Lending Borrowing** | 1500 | 0.2 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **NFT Asset Manager** | 1500 | 0.3 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |
| **DAO Governance** | 1500 | 0.3 | ~500 | ~300 | ~800 | $0.00017 | $0.000064 |

**Pricing Formula**:
- **Vertex AI**: Input × $0.10/1M + Output × $0.40/1M
- **DeepInfra**: Total × $0.08/1M

### 13.2 System LLM Costs (Per Request)

| Component | Model | Tokens/Req | Vertex AI | DeepInfra |
|-----------|-------|------------|-----------|-----------|
| **Intent Classification** | gemini-2.0-flash-exp | ~200 | $0.00002 | $0.000016 |
| **Agent Selection** | gemini-2.0-flash-exp | ~100 | $0.00001 | $0.000008 |
| **Supervisor Coordination** | gemini-2.0-flash-exp | ~500 | $0.00005 | $0.00004 |
| **Workflow Planning** | gemini-1.5-pro | ~800 | $0.00008 | $0.000064 |

**Total per User Message** (typical flow):
- Intent + Agent + Processing + Response: ~1,400 tokens
- **Vertex AI**: $0.00023-0.00047/message
- **DeepInfra**: $0.000112/message

### 13.3 MCP Server API Costs

| MCP Server | Port | API Provider | Pricing | Rate Limits | Notes |
|------------|------|--------------|---------|-------------|-------|
| **CoinGecko** | 8081 | CoinGecko API | ✅ Free | 30 req/min | Demo API key |
| **1inch** | 8082 | 1inch Fusion | ✅ Free | 10 req/min | Public API |
| **DeFiLlama** | 8083 | DeFiLlama | ✅ Free | Unlimited | Open API |
| **The Graph** | 8084 | The Graph | ✅ Free* | 100K queries/mo | *Free tier |
| **Aave** | 8085 | Aave Protocol | ✅ Free | On-chain calls | RPC costs only |
| **Portfolio** | 8086 | Internal | ✅ Free | N/A | Uses DB |
| **Perplexity** | 8087 | Perplexity AI | 💰 Paid | 50 req/min | ~$0.003/query |
| **Morpho** | 8088 | Morpho Protocol | ✅ Free | On-chain calls | RPC costs only |
| **Curve** | 8089 | Curve Protocol | ✅ Free | On-chain calls | RPC costs only |
| **HyperLiquid** | 8090 | HyperLiquid | ✅ Free | 100 req/min | Public API |
| **LayerZero** | 8091 | LayerZero | ✅ Free | On-chain calls | Bridge queries |

**RPC Costs** (for on-chain calls):
- Alchemy/Infura Free tier: 330K requests/month
- Paid tier: ~$49/month for 100M requests

### 13.4 Cost Per Intent Type

| Intent Category | Intent | LLM Cost | MCP Cost | Total/Request |
|-----------------|--------|----------|----------|---------------|
| **ULTRA** | | | | |
| | ARBITRAGE | $0.00017 | Free (CoinGecko + 1inch) | $0.00017 |
| | FLASH_LOANS | $0.00017 | Free (Aave/Morpho) | $0.00017 |
| | MEV_PROTECTION | $0.00012 | Free (Flashbots) | $0.00012 |
| | AUTO_EXECUTOR | $0.00023 | Free (1inch) | $0.00023 |
| **Hunter AI** | | | | |
| | SENTIMENT | $0.00017 | Free (CoinGecko + RSS) | $0.00017 |
| | PRICE_PREDICTION | $0.00017 | Free (CoinGecko) | $0.00017 |
| | RISK_SIGNALS | $0.00017 | Free (CoinGecko + Graph) | $0.00017 |
| | TRADING_SIGNALS | $0.00017 | Free (CoinGecko) | $0.00017 |
| | PATTERNS | $0.00017 | Free (CoinGecko) | $0.00017 |
| | PORTFOLIO | $0.00021 | Free (Portfolio + CoinGecko) | $0.00021 |
| **DeFi Shortcuts** | | | | |
| | LENDING | $0.00017 | Free (Morpho/Aave) | $0.00017 |
| | MONEY_MARKET | $0.00017 | Free (Morpho/Aave/DeFiLlama) | $0.00017 |
| | SWAP | $0.00012 | Free (1inch/LiFi) | $0.00012 |
| | BALANCE | $0.00012 | Free (Portfolio/CoinGecko) | $0.00012 |
| | PORTFOLIO | $0.00021 | Free (Portfolio) | $0.00021 |
| | ACTIVITY | $0.00012 | Free (The Graph) | $0.00012 |
| | RECEIVE | $0.00012 | Free (ENS) | $0.00012 |
| **GraphRAG** | | | | |
| | PROTOCOL_SEARCH | $0.00023 | Free (GraphRAG DB) | $0.00023 |
| | RISK_ASSESSMENT | $0.00023 | Free (GraphRAG DB) | $0.00023 |
| | SIMILAR_PROTOCOLS | $0.00023 | Free (GraphRAG DB) | $0.00023 |
| **Agent Squad** | | | | |
| | SPECIALIST_TASK | $0.00017-0.00023 | Varies by agent | $0.00017-0.00026 |
| | COMPLEX_WORKFLOW | $0.00050+ | Multiple agents | $0.00050+ |
| **General** | | | | |
| | CONVERSATION | $0.00013 | Free (None) | $0.00013 |

### 13.5 Execute Action Costs

| Action | LLM Cost | API Cost | RPC Cost | Gas Cost |
|--------|----------|----------|----------|----------|
| **swap** | $0.00012 | Free (1inch) | ~$0.001 | Variable |
| **deposit** | $0.00012 | Free (Morpho/Aave) | ~$0.001 | Variable |
| **withdraw** | $0.00012 | Free (Morpho/Aave) | ~$0.001 | Variable |
| **transfer** | $0.00012 | Free | ~$0.001 | Variable |
| **approve** | $0.00012 | Free | ~$0.001 | Variable |
| **bridge** | $0.00012 | Free (LiFi) | ~$0.002 | Variable |

**Notes**:
- RPC costs assume Alchemy/Infura free tier
- Gas costs depend on network congestion and operation complexity
- Bridge operations have both source and destination chain gas

### 13.6 Monthly Cost Projections

#### Low Usage (100 users × 50 msgs/month = 5,000 messages)

| Component | Tokens | Vertex AI | DeepInfra |
|-----------|--------|-----------|-----------|
| Intent Classification | 1M | $0.10 | $0.08 |
| Agent Processing | 4M | $1.00 | $0.32 |
| Supervisor (10%) | 0.25M | $0.025 | $0.02 |
| **LLM Total** | **5.25M** | **$1.125** | **$0.42** |
| MCP APIs | N/A | $0 | $0 |
| RPC Costs (est.) | N/A | $0 (free tier) | $0 |
| **Grand Total** | | **$1.125/mo** | **$0.42/mo** |

#### Medium Usage (1,000 users × 50 msgs/month = 50,000 messages)

| Component | Tokens | Vertex AI | DeepInfra |
|-----------|--------|-----------|-----------|
| Intent Classification | 10M | $1.00 | $0.80 |
| Agent Processing | 40M | $10.00 | $3.20 |
| Supervisor (10%) | 2.5M | $0.25 | $0.20 |
| **LLM Total** | **52.5M** | **$11.25** | **$4.20** |
| MCP APIs | N/A | $0 | $0 |
| RPC Costs (est.) | N/A | $0 (free tier) | $0 |
| **Grand Total** | | **$11.25/mo** | **$4.20/mo** |

#### High Usage (10,000 users × 50 msgs/month = 500,000 messages)

| Component | Tokens | Vertex AI | DeepInfra |
|-----------|--------|-----------|-----------|
| Intent Classification | 100M | $10.00 | $8.00 |
| Agent Processing | 400M | $100.00 | $32.00 |
| Supervisor (10%) | 25M | $2.50 | $2.00 |
| **LLM Total** | **525M** | **$112.50** | **$42.00** |
| MCP APIs | N/A | $0-$50* | $0-$50* |
| RPC Costs (est.) | N/A | $49 (paid tier) | $49 |
| **Grand Total** | | **$161.50/mo** | **$91.00/mo** |

*Perplexity API costs if heavily used

### 13.7 Cost Optimization Strategies

1. **Use DeepInfra for chat/simple tasks**: 68% savings
2. **Cache intent classifications**: 20-30% token reduction
3. **Batch similar requests**: Reduce redundant API calls
4. **Use free MCP endpoints**: All 11 MCP servers use free APIs
5. **Stay within RPC free tier**: 330K requests/month

### 13.8 Cost Comparison vs OpenAI

| Provider | Cost/1M tokens | Monthly (100M tokens) | Savings |
|----------|----------------|----------------------|---------|
| **OpenAI GPT-4o** | $5.00-15.00 | $355.50 | Baseline |
| **Vertex AI** | $0.10-0.40 | $29.75 | **91.6%** |
| **DeepInfra** | $0.08 | $8.00 | **97.7%** |

---

## Related Documentation

- `docs/steering/guest-chat-complete-flow-spec.md` - Guest chat flow
- `docs/steering/user-chat-complete-flow-spec.md` - User chat flow
- `docs/steering/guest-chat-intent-testing.md` - Intent test examples
- `docs/steering/llm-models-cost-analysis.md` - Detailed LLM cost analysis
- `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` - Agent configuration
- `docs/HUNTER_AI_DATA_SOURCES.md` - Hunter AI data sources
