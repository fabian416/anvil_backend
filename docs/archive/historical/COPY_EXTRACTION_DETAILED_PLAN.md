# Copy Extraction: Detailed Enterprise Implementation Plan

**Date:** December 2, 2025  
**Purpose:** Detailed breakdown of what to copy, use cases, and enterprise-grade configuration  
**Architecture:** Hexagonal Architecture (Clean Architecture) with CQRS

---

## 📚 **TABLE OF CONTENTS**

1. [Hunter AI Trading Bot - Extraction Details](#hunter-ai-trading-bot)
2. [ULTRA Arbitrage Bot - Extraction Details](#ultra-arbitrage-bot)
3. [Crypto Portfolio Tracker - Extraction Details](#crypto-portfolio-tracker)
4. [Aave V3 Data - Integration Details](#aave-v3-data)
5. [DeFi Tools - Extraction Details](#defi-tools)
6. [Yield Calculator - Extraction Details](#yield-calculator)
7. [Configuration System Architecture](#configuration-system)
8. [Use Cases & Feature Matrix](#use-cases-matrix)

---

## 🤖 **1. HUNTER AI TRADING BOT** {#hunter-ai-trading-bot}

### **1.1 What to Copy: 6 Core AI Modules (~5,000 lines)**

#### **Module 1: AI Sentiment Analyzer (847 lines)**

**Source:** `libs/Hunter/src/ai/ai_sentiment_analyzer.py`  
**Target:** `src/app/infrastructure/hunter/ai/sentiment_analyzer.py`

**What it does:**
- Analyzes social media sentiment (Twitter, Reddit, Discord)
- Real-time sentiment scoring (0-100)
- Trend detection and momentum analysis
- News impact assessment
- Multi-source aggregation

**Core Functions to Copy:**
```python
# COPY: Sentiment analysis algorithms
class SentimentAnalyzer:
    def analyze_token_sentiment(self, token: str) -> SentimentScore:
        """Multi-source sentiment analysis"""
        # ML-based sentiment scoring
        # Twitter API integration
        # Reddit sentiment scraping
        # Discord community sentiment
        # Aggregate and normalize scores
        
    def detect_sentiment_trends(self, token: str, hours: int) -> TrendData:
        """Detect sentiment momentum"""
        # Time-series analysis
        # Trend direction detection
        # Velocity calculations
        
    def assess_news_impact(self, token: str) -> ImpactScore:
        """Evaluate news impact on sentiment"""
        # News API integration
        # Impact scoring algorithm
        # Event correlation
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class SentimentConfig:
    """Sentiment analyzer configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_twitter: bool = True
    enable_reddit: bool = True
    enable_discord: bool = True
    enable_news_analysis: bool = True
    
    # API limits
    twitter_rate_limit: int = 100  # requests/hour
    reddit_rate_limit: int = 60
    discord_rate_limit: int = 300
    
    # Analysis thresholds
    min_sentiment_score: float = 30.0  # Below = bearish
    max_sentiment_score: float = 70.0  # Above = bullish
    high_confidence_threshold: float = 0.75  # 75% confidence
    
    # Data sources weights
    twitter_weight: float = 0.35
    reddit_weight: float = 0.25
    discord_weight: float = 0.20
    news_weight: float = 0.20
    
    # Cache settings
    cache_ttl_minutes: int = 15  # 15 min cache
    
    # Quality filters
    min_tweet_engagement: int = 10  # Min likes/retweets
    min_reddit_karma: int = 100
    verified_accounts_only: bool = False
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H1: Token Research** | Research Agent analyzes token sentiment | `enabled=True`, `enable_twitter=True` |
| **UC-H2: Risk Assessment** | Risk scoring based on sentiment | `min_sentiment_score`, `high_confidence_threshold` |
| **UC-H3: Real-time Alerts** | Alert users on sentiment shifts | `cache_ttl_minutes`, WebSocket integration |
| **UC-H4: Portfolio Analysis** | Sentiment-based portfolio scoring | All weights configuration |
| **UC-H5: Market Intelligence** | Dashboard sentiment indicators | `enable_news_analysis=True` |

---

#### **Module 2: AI Price Predictor (612 lines)**

**Source:** `libs/Hunter/src/ai/ai_price_predictor.py`  
**Target:** `src/app/infrastructure/hunter/ai/price_predictor.py`

**What it does:**
- LSTM neural network price prediction
- Multi-timeframe forecasting (1h, 4h, 24h, 7d)
- Confidence interval calculations
- Technical indicator integration
- Historical pattern matching

**Core Functions to Copy:**
```python
# COPY: LSTM price prediction model
class PricePredictor:
    def __init__(self):
        self.lstm_model = self._load_lstm_model()
        
    def predict_price(
        self, 
        token: str, 
        timeframe: str = "24h"
    ) -> PricePrediction:
        """Predict future price using LSTM"""
        # Load historical data
        # Preprocess features
        # LSTM inference
        # Calculate confidence intervals
        # Return prediction with bounds
        
    def get_prediction_accuracy(self, token: str) -> float:
        """Historical accuracy score"""
        # Compare past predictions vs actual
        # Calculate MAPE (Mean Absolute Percentage Error)
        
    def analyze_prediction_factors(self, token: str) -> List[Factor]:
        """Explain prediction factors"""
        # Feature importance analysis
        # Top contributing factors
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class PricePredictorConfig:
    """Price prediction configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_1h_predictions: bool = True
    enable_4h_predictions: bool = True
    enable_24h_predictions: bool = True
    enable_7d_predictions: bool = False  # Premium only
    
    # Model settings
    lstm_model_path: str = "models/hunter/lstm_v2.h5"
    confidence_level: float = 0.90  # 90% confidence intervals
    min_historical_data_days: int = 90
    
    # Accuracy thresholds
    min_model_accuracy: float = 0.65  # 65% accuracy floor
    retrain_threshold_days: int = 30  # Retrain every 30 days
    
    # Prediction limits
    max_predictions_per_user_day: int = 50  # Free tier
    max_predictions_per_premium_day: int = 500
    
    # Data requirements
    required_indicators: List[str] = field(default_factory=lambda: [
        "rsi", "macd", "bb", "ema_20", "volume"
    ])
    
    # Cache settings
    prediction_cache_ttl_minutes: int = 60  # 1 hour cache
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H6: Price Forecasting** | Show price predictions in dashboard | `enable_24h_predictions=True` |
| **UC-H7: Trading Signals** | Generate buy/sell signals | `min_model_accuracy`, `confidence_level` |
| **UC-H8: Risk Analysis** | Calculate potential loss scenarios | `confidence_level=0.90` for bounds |
| **UC-H9: Portfolio Planning** | Optimize portfolio based on predictions | All timeframe flags |
| **UC-H10: Premium Features** | 7-day predictions for premium users | `enable_7d_predictions=True` |

---

#### **Module 3: AI Risk Assessor (734 lines)**

**Source:** `libs/Hunter/src/ai/ai_risk_assessor.py`  
**Target:** `src/app/infrastructure/hunter/ai/risk_assessor.py`

**What it does:**
- ML-based risk scoring (0-100)
- Liquidity risk assessment
- Volatility analysis
- Smart contract risk evaluation
- Correlation risk detection

**Core Functions to Copy:**
```python
# COPY: Risk assessment algorithms
class RiskAssessor:
    def calculate_risk_score(self, token: str) -> RiskScore:
        """Comprehensive risk assessment"""
        # Liquidity risk (pool depth, volume)
        # Volatility risk (historical price swings)
        # Smart contract risk (audit status, exploits)
        # Market cap risk (dilution, concentration)
        # Correlation risk (portfolio impact)
        # Aggregate into 0-100 score
        
    def assess_liquidity_risk(self, token: str) -> LiquidityRisk:
        """Evaluate liquidity depth"""
        # DEX liquidity analysis
        # Slippage calculations
        # Pool concentration
        
    def evaluate_smart_contract_risk(self, token: str) -> ContractRisk:
        """Smart contract security assessment"""
        # Audit verification
        # Known exploit database check
        # Ownership analysis (renounced, multi-sig)
        # Proxy pattern detection
        
    def calculate_portfolio_risk(
        self, 
        portfolio: List[Position]
    ) -> PortfolioRisk:
        """Portfolio-level risk analysis"""
        # Correlation matrix
        # Diversification score
        # Max drawdown scenarios
        # VaR (Value at Risk) calculations
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class RiskAssessorConfig:
    """Risk assessment configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_liquidity_risk: bool = True
    enable_volatility_risk: bool = True
    enable_contract_risk: bool = True
    enable_correlation_risk: bool = True
    
    # Risk scoring weights
    liquidity_weight: float = 0.30
    volatility_weight: float = 0.25
    contract_weight: float = 0.25
    correlation_weight: float = 0.20
    
    # Risk thresholds (0-100 scale)
    low_risk_threshold: float = 30.0      # Below = LOW
    medium_risk_threshold: float = 60.0   # 30-60 = MEDIUM
    # Above 60 = HIGH risk
    
    # Liquidity requirements
    min_liquidity_usd: float = 100000.0   # $100k min liquidity
    max_slippage_percent: float = 5.0     # 5% max slippage
    
    # Volatility limits
    max_daily_volatility: float = 0.20    # 20% max daily swing
    volatility_window_days: int = 30      # 30-day volatility calc
    
    # Contract safety
    require_audit: bool = True             # Require audit for low risk
    trusted_auditors: List[str] = field(default_factory=lambda: [
        "certik", "quantstamp", "trailofbits", "consensys", "peckshield"
    ])
    allow_unverified_contracts: bool = False
    
    # Portfolio risk
    max_position_concentration: float = 0.30  # Max 30% in one asset
    var_confidence_level: float = 0.95        # 95% VaR
    max_portfolio_volatility: float = 0.15    # 15% max portfolio vol
    
    # Alert thresholds
    critical_risk_score: float = 80.0     # Send immediate alert
    alert_check_interval_minutes: int = 30
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H11: Token Risk Scoring** | Show risk score on token pages | All weights, thresholds |
| **UC-H12: Portfolio Risk Dashboard** | Display portfolio risk metrics | `enable_correlation_risk`, VaR settings |
| **UC-H13: Risk Alerts** | Alert on high-risk positions | `critical_risk_score`, alert interval |
| **UC-H14: Smart Contract Validation** | Verify contract safety | `require_audit`, `trusted_auditors` |
| **UC-H15: Trading Guardrails** | Block high-risk trades | `max_slippage_percent`, liquidity mins |
| **UC-H16: Liquidity Warnings** | Warn on low liquidity | `min_liquidity_usd` |

---

#### **Module 4: AI Pattern Recognizer (589 lines)**

**Source:** `libs/Hunter/src/ai/ai_pattern_recognizer.py`  
**Target:** `src/app/infrastructure/hunter/ai/pattern_recognizer.py`

**What it does:**
- Chart pattern detection (head & shoulders, triangles, flags)
- Candlestick pattern recognition (doji, hammer, engulfing)
- Support/resistance identification
- Breakout detection
- Pattern success probability

**Core Functions to Copy:**
```python
# COPY: Pattern recognition algorithms
class PatternRecognizer:
    def detect_chart_patterns(
        self, 
        token: str, 
        timeframe: str = "4h"
    ) -> List[ChartPattern]:
        """Detect technical chart patterns"""
        # Head & Shoulders
        # Double top/bottom
        # Triangles (ascending, descending, symmetrical)
        # Flags and pennants
        # Channels
        
    def recognize_candlestick_patterns(
        self, 
        token: str
    ) -> List[CandlestickPattern]:
        """Identify candlestick formations"""
        # Doji, Hammer, Hanging Man
        # Engulfing patterns
        # Morning/Evening star
        # Three white soldiers / Three black crows
        
    def identify_support_resistance(
        self, 
        token: str
    ) -> SupportResistanceLevels:
        """Calculate key price levels"""
        # Historical price clustering
        # Volume profile analysis
        # Fibonacci retracements
        # Pivot points
        
    def detect_breakouts(self, token: str) -> List[Breakout]:
        """Real-time breakout detection"""
        # Support/resistance breaks
        # Volume confirmation
        # Momentum indicators
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class PatternRecognizerConfig:
    """Pattern recognition configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_chart_patterns: bool = True
    enable_candlestick_patterns: bool = True
    enable_support_resistance: bool = True
    enable_breakout_detection: bool = True
    
    # Pattern detection settings
    min_pattern_confidence: float = 0.70   # 70% confidence min
    lookback_candles: int = 200            # Analyze last 200 candles
    supported_timeframes: List[str] = field(default_factory=lambda: [
        "15m", "1h", "4h", "1d"
    ])
    
    # Chart pattern weights (success probability adjustments)
    pattern_success_rates: Dict[str, float] = field(default_factory=lambda: {
        "head_and_shoulders": 0.73,
        "double_top": 0.68,
        "ascending_triangle": 0.72,
        "flag": 0.67,
    })
    
    # Support/resistance settings
    touch_tolerance_percent: float = 2.0   # 2% tolerance for level
    min_touches_for_level: int = 3         # Min 3 touches to confirm
    
    # Breakout confirmation
    require_volume_confirmation: bool = True
    volume_multiplier_threshold: float = 1.5  # 1.5x avg volume
    retest_window_hours: int = 24          # Allow 24h retest
    
    # Alert settings
    notify_on_patterns: List[str] = field(default_factory=lambda: [
        "head_and_shoulders", "double_top", "breakout"
    ])
    pattern_alert_cooldown_hours: int = 6  # Don't spam alerts
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H17: Pattern Alerts** | Alert users on detected patterns | `notify_on_patterns`, confidence |
| **UC-H18: Chart Analysis** | Show patterns on charts | `enable_chart_patterns=True` |
| **UC-H19: Support/Resistance Lines** | Display key levels | `min_touches_for_level`, tolerance |
| **UC-H20: Breakout Signals** | Generate breakout trading signals | Volume confirmation, retest window |
| **UC-H21: Pattern Success Stats** | Show historical pattern performance | `pattern_success_rates` |
| **UC-H22: Multi-Timeframe Analysis** | Analyze across timeframes | `supported_timeframes` |

---

#### **Module 5: AI Portfolio Optimizer (923 lines)**

**Source:** `libs/Hunter/src/ai/ai_portfolio_optimizer.py`  
**Target:** `src/app/infrastructure/hunter/ai/portfolio_optimizer.py`

**What it does:**
- Modern Portfolio Theory (MPT) optimization
- Risk-adjusted return maximization (Sharpe ratio)
- Rebalancing recommendations
- Asset allocation strategies
- Constraint-based optimization

**Core Functions to Copy:**
```python
# COPY: Portfolio optimization algorithms
class PortfolioOptimizer:
    def optimize_portfolio(
        self, 
        assets: List[str],
        constraints: OptimizationConstraints
    ) -> OptimizedPortfolio:
        """MPT-based portfolio optimization"""
        # Calculate expected returns
        # Build covariance matrix
        # Efficient frontier calculation
        # Max Sharpe ratio portfolio
        # Apply constraints
        
    def calculate_efficient_frontier(
        self, 
        assets: List[str]
    ) -> EfficientFrontier:
        """Generate efficient frontier"""
        # Risk-return tradeoff curve
        # Minimum variance portfolio
        # Maximum Sharpe portfolio
        # Tangency portfolio
        
    def generate_rebalancing_plan(
        self, 
        current: Portfolio,
        target: Portfolio
    ) -> RebalancingPlan:
        """Calculate rebalancing trades"""
        # Minimize transaction costs
        # Tax-loss harvesting opportunities
        # Slippage consideration
        # Optimal execution strategy
        
    def backtest_strategy(
        self,
        strategy: AllocationStrategy,
        start_date: str,
        end_date: str
    ) -> BacktestResults:
        """Historical strategy performance"""
        # Portfolio simulation
        # Sharpe ratio calculation
        # Max drawdown analysis
        # Risk metrics
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class PortfolioOptimizerConfig:
    """Portfolio optimization configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_mpt_optimization: bool = True
    enable_rebalancing_alerts: bool = True
    enable_tax_loss_harvesting: bool = True  # Premium
    enable_backtesting: bool = True
    
    # Optimization constraints
    min_position_size_percent: float = 5.0    # Min 5% allocation
    max_position_size_percent: float = 30.0   # Max 30% allocation
    max_assets_in_portfolio: int = 20
    min_assets_in_portfolio: int = 3
    
    # Risk parameters
    target_annual_return: float = 0.20        # 20% target return
    max_acceptable_volatility: float = 0.25   # 25% max volatility
    risk_free_rate: float = 0.04              # 4% risk-free rate (T-bills)
    
    # Rebalancing settings
    rebalancing_threshold_percent: float = 5.0  # Rebalance if >5% drift
    min_rebalance_interval_days: int = 7      # Min 7 days between
    rebalancing_frequency: str = "monthly"     # monthly, quarterly, annually
    
    # Transaction costs
    assume_transaction_cost_bps: int = 30     # 0.3% per trade
    assume_slippage_bps: int = 20             # 0.2% slippage
    
    # Asset constraints
    allow_leverage: bool = False
    allow_short_positions: bool = False
    min_liquidity_usd: float = 100000.0       # Only liquid assets
    
    # Optimization algorithm
    optimization_method: str = "max_sharpe"   # max_sharpe, min_variance, risk_parity
    historical_lookback_days: int = 365       # 1 year historical data
    monte_carlo_simulations: int = 10000      # For frontier calculation
    
    # Tax optimization (Premium)
    tax_rate_short_term: float = 0.37         # 37% short-term cap gains
    tax_rate_long_term: float = 0.20          # 20% long-term cap gains
    holding_period_long_term_days: int = 365
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H23: Portfolio Optimization** | Suggest optimal allocations | All constraints, optimization method |
| **UC-H24: Efficient Frontier** | Show risk-return tradeoffs | Monte Carlo sims, lookback period |
| **UC-H25: Rebalancing Alerts** | Notify when to rebalance | `rebalancing_threshold_percent` |
| **UC-H26: Tax-Loss Harvesting** | Identify tax opportunities | Tax rates, holding period |
| **UC-H27: Strategy Backtesting** | Test strategies historically | `enable_backtesting=True` |
| **UC-H28: Risk-Adjusted Returns** | Calculate Sharpe ratios | `risk_free_rate`, volatility params |
| **UC-H29: Allocation Constraints** | Enforce position limits | Min/max position sizes |

---

#### **Module 6: AI Microstructure Analyzer (1,245 lines)**

**Source:** `libs/Hunter/src/ai/ai_microstructure_analyzer.py`  
**Target:** `src/app/infrastructure/hunter/ai/microstructure_analyzer.py`

**What it does:**
- Order book analysis (bid/ask spread, depth)
- Trade flow analysis (buy/sell pressure)
- Market maker behavior detection
- Whale activity tracking
- MEV (Maximal Extractable Value) impact

**Core Functions to Copy:**
```python
# COPY: Market microstructure algorithms
class MicrostructureAnalyzer:
    def analyze_order_book(
        self, 
        token: str
    ) -> OrderBookAnalysis:
        """Deep order book analysis"""
        # Bid-ask spread calculation
        # Order book depth (cumulative)
        # Liquidity concentration
        # Spoofing detection
        # Hidden liquidity estimation
        
    def analyze_trade_flow(
        self, 
        token: str,
        window_minutes: int = 60
    ) -> TradeFlowAnalysis:
        """Real-time trade flow metrics"""
        # Buy/sell pressure ratio
        # Large trade detection
        # Trade velocity
        # Volume-weighted average price (VWAP)
        # Price impact calculations
        
    def detect_whale_activity(
        self, 
        token: str
    ) -> List[WhaleActivity]:
        """Track large holder movements"""
        # Wallet tracking
        # Large transfer detection
        # Smart money indicators
        # Accumulation/distribution patterns
        
    def estimate_mev_impact(
        self, 
        token: str,
        trade_size_usd: float
    ) -> MEVImpact:
        """Estimate MEV for trade"""
        # Sandwich attack probability
        # Frontrunning risk
        # Backrunning likelihood
        # Expected MEV loss
```

**Enterprise Configuration:**
```python
# src/app/setup/config/hunter.py

@dataclass
class MicrostructureConfig:
    """Market microstructure configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_order_book_analysis: bool = True
    enable_trade_flow_analysis: bool = True
    enable_whale_tracking: bool = True
    enable_mev_detection: bool = True
    
    # Order book settings
    order_book_depth_levels: int = 50      # Analyze top 50 levels
    spread_alert_threshold_bps: int = 100  # Alert if spread >1%
    min_book_depth_usd: float = 50000.0    # Min $50k depth
    
    # Trade flow settings
    large_trade_threshold_usd: float = 10000.0  # $10k = large
    trade_flow_window_minutes: int = 60    # 1 hour window
    buy_pressure_threshold: float = 0.65   # 65% buy = bullish
    
    # Whale tracking
    whale_wallet_threshold_usd: float = 1000000.0  # $1M = whale
    track_top_n_holders: int = 100         # Track top 100 holders
    whale_transfer_alert_threshold_usd: float = 100000.0  # $100k
    
    # MEV settings
    mev_analysis_enabled: bool = True
    min_trade_size_for_mev_usd: float = 5000.0  # Analyze if >$5k
    high_mev_risk_threshold_bps: int = 50  # >0.5% MEV = high risk
    
    # Data refresh rates
    order_book_refresh_seconds: int = 5    # Real-time book
    trade_flow_refresh_seconds: int = 10
    whale_scan_interval_minutes: int = 15
    
    # Alert settings
    enable_whale_alerts: bool = True
    enable_large_trade_alerts: bool = True
    enable_mev_warnings: bool = True
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-H30: Order Book Depth** | Display live order book | `order_book_depth_levels`, refresh rate |
| **UC-H31: Spread Monitoring** | Alert on wide spreads | `spread_alert_threshold_bps` |
| **UC-H32: Buy/Sell Pressure** | Show market sentiment | `trade_flow_window_minutes`, threshold |
| **UC-H33: Whale Alerts** | Notify on whale activity | Whale thresholds, alert flags |
| **UC-H34: MEV Protection** | Warn about MEV risk | `mev_analysis_enabled`, risk threshold |
| **UC-H35: Smart Money Tracking** | Track institutional flows | `track_top_n_holders` |
| **UC-H36: Liquidity Analysis** | Real-time liquidity metrics | Book depth, refresh rates |

---

### **1.2 Hunter Integration Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                (FastAPI + WebSocket)                         │
├─────────────────────────────────────────────────────────────┤
│  POST /api/v1/hunter/sentiment/{token}                      │
│  POST /api/v1/hunter/predict/{token}                        │
│  POST /api/v1/hunter/risk-score/{token}                     │
│  POST /api/v1/hunter/patterns/{token}                       │
│  POST /api/v1/hunter/optimize-portfolio                     │
│  POST /api/v1/hunter/microstructure/{token}                 │
│  WS   /ws/hunter/alerts                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│                      (Interactors)                           │
├─────────────────────────────────────────────────────────────┤
│  AnalyzeTokenSentiment                                      │
│  PredictTokenPrice                                          │
│  CalculateRiskScore                                         │
│  DetectChartPatterns                                        │
│  OptimizePortfolio                                          │
│  AnalyzeMarketMicrostructure                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│                (Hunter AI Modules - COPIED)                  │
├─────────────────────────────────────────────────────────────┤
│  src/app/infrastructure/hunter/ai/                          │
│    ├── sentiment_analyzer.py       (COPIED 847 lines)      │
│    ├── price_predictor.py          (COPIED 612 lines)      │
│    ├── risk_assessor.py            (COPIED 734 lines)      │
│    ├── pattern_recognizer.py       (COPIED 589 lines)      │
│    ├── portfolio_optimizer.py      (COPIED 923 lines)      │
│    └── microstructure_analyzer.py  (COPIED 1,245 lines)    │
│                                                              │
│  src/app/infrastructure/hunter/services/                    │
│    ├── hunter_service.py           (NEW - orchestrator)    │
│    └── cache_manager.py            (NEW - Redis caching)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                          │
│              (Replaced from Hunter standalone)               │
├─────────────────────────────────────────────────────────────┤
│  ❌ REMOVED: Telegram Bot                                   │
│  ✅ ADDED:   WebSocket (Anvil)                              │
│                                                              │
│  ❌ REMOVED: Standalone Redis                               │
│  ✅ ADDED:   PostgreSQL + Redis Cache (Anvil)              │
│                                                              │
│  ❌ REMOVED: Custom Config System                           │
│  ✅ ADDED:   TOML Config (Anvil)                            │
│                                                              │
│  ❌ REMOVED: Custom Monitoring                              │
│  ✅ ADDED:   Anvil Monitoring                               │
│                                                              │
│  ✅ KEEP:    DEX APIs (1inch MCP Server)                    │
│  ✅ KEEP:    Twitter/Reddit APIs                            │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ **2. ULTRA ARBITRAGE BOT** {#ultra-arbitrage-bot}

### **2.1 What to Copy: 5 Core Modules (~8,000 lines)**

#### **Module 1: Quantum Arbitrage Engine (2,134 lines)**

**Source:** `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/ai/quantum_arbitrage.py`  
**Target:** `src/app/infrastructure/arbitrage/core/arbitrage_engine.py`

**What it does:**
- Multi-hop arbitrage path discovery (2-hop, 3-hop, 4-hop)
- Cross-DEX arbitrage (Uniswap, Curve, Balancer, SushiSwap)
- Real-time profit calculation with gas costs
- Flash loan integration for capital efficiency
- MEV-aware execution

**Core Functions to Copy:**
```python
# COPY: Arbitrage discovery and execution
class ArbitrageEngine:
    def discover_arbitrage_paths(
        self,
        token_in: str,
        token_out: str,
        max_hops: int = 3
    ) -> List[ArbitragePath]:
        """Discover profitable arbitrage paths"""
        # Graph-based path discovery
        # DFS/BFS for multi-hop routes
        # Filter by liquidity requirements
        # Sort by expected profit
        
    def calculate_arbitrage_profit(
        self,
        path: ArbitragePath,
        amount_in: float
    ) -> ArbitrageProfit:
        """Calculate net profit after all costs"""
        # Swap price calculations
        # Gas cost estimation
        # Slippage impact
        # Flash loan fees
        # MEV protection costs
        # Net profit calculation
        
    def execute_arbitrage(
        self,
        opportunity: ArbitrageOpportunity,
        use_flash_loan: bool = True
    ) -> ExecutionResult:
        """Execute arbitrage trade"""
        # Flash loan acquisition
        # Multi-hop swap execution
        # MEV protection activation
        # Flash loan repayment
        # Profit extraction
        
    def simulate_execution(
        self,
        opportunity: ArbitrageOpportunity
    ) -> SimulationResult:
        """Simulate before real execution"""
        # Fork mainnet state
        # Simulate full execution
        # Check for reverts
        # Validate profit expectations
```

**Enterprise Configuration:**
```python
# src/app/setup/config/arbitrage.py

@dataclass
class ArbitrageEngineConfig:
    """Arbitrage engine configuration"""
    
    # Feature flags
    enabled: bool = False  # Disabled by default
    enable_flash_loans: bool = True
    enable_mev_protection: bool = True
    enable_cross_dex_arb: bool = True
    enable_simulation_mode: bool = True  # Dry run first
    
    # Discovery settings
    max_hop_count: int = 3                 # Max 3-hop paths
    min_profit_threshold_usd: float = 50.0  # Min $50 profit
    max_discovery_time_ms: int = 500       # 500ms discovery limit
    
    # Supported DEXs
    enabled_dexs: List[str] = field(default_factory=lambda: [
        "uniswap_v2", "uniswap_v3", "sushiswap", 
        "curve", "balancer", "pancakeswap"
    ])
    
    # Liquidity requirements
    min_pool_liquidity_usd: float = 100000.0  # $100k min
    max_price_impact_percent: float = 2.0     # 2% max impact
    
    # Gas settings
    max_gas_price_gwei: float = 100.0      # Max 100 gwei
    gas_buffer_multiplier: float = 1.2     # 20% buffer
    priority_fee_gwei: float = 2.0         # 2 gwei priority
    
    # Flash loan settings
    preferred_provider: str = "balancer"   # balancer, aave, dydx
    max_flash_loan_fee_bps: int = 50       # Max 0.5% fee
    flash_loan_buffer_percent: float = 5.0  # 5% extra borrowed
    
    # MEV protection
    use_private_relay: bool = True
    preferred_relay: str = "flashbots"     # flashbots, bloxroute
    mev_protection_tip_percent: float = 10.0  # 10% of profit as tip
    
    # Risk limits (CRITICAL)
    max_position_size_usd: float = 100000.0  # Max $100k per trade
    max_daily_trades: int = 50             # Max 50 trades/day
    max_daily_loss_usd: float = 5000.0     # Max $5k loss/day
    circuit_breaker_loss_usd: float = 2000.0  # Stop if $2k loss
    
    # Execution settings
    require_simulation_success: bool = True
    min_simulation_profit_ratio: float = 0.90  # 90% of expected
    max_execution_time_seconds: int = 30
    
    # Access control
    min_user_tier: str = "ultra_premium"   # Premium feature
    min_capital_requirement_usd: float = 5000.0
    require_kyc: bool = True               # Regulatory compliance
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-A1: Arbitrage Discovery** | Scan markets for opportunities | `max_hop_count`, `enabled_dexs` |
| **UC-A2: Profit Calculation** | Show potential profits | `min_profit_threshold_usd`, gas settings |
| **UC-A3: Flash Loan Arbitrage** | Execute capital-free trades | Flash loan settings, preferred provider |
| **UC-A4: MEV Protection** | Protect from frontrunning | `use_private_relay`, `preferred_relay` |
| **UC-A5: Simulation Mode** | Test strategies risk-free | `enable_simulation_mode=True` |
| **UC-A6: Risk Management** | Prevent excessive losses | All risk limits (max loss, position size) |
| **UC-A7: Auto-Execution** | Automated arbitrage trading | `enabled=True`, execution settings |

---

#### **Module 2: Quantum Signal (Opportunity Scanner) (1,456 lines)**

**Source:** `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/ai/quantum_signal.py`  
**Target:** `src/app/infrastructure/arbitrage/core/opportunity_scanner.py`

**What it does:**
- Real-time DEX price monitoring
- Price discrepancy detection
- Opportunity scoring and ranking
- Historical opportunity tracking
- Market condition analysis

**Core Functions to Copy:**
```python
# COPY: Opportunity detection algorithms
class OpportunityScanner:
    def scan_all_dexs(
        self,
        tokens: List[str]
    ) -> List[Opportunity]:
        """Scan all DEXs for price discrepancies"""
        # Parallel price fetching
        # Cross-DEX price comparison
        # Opportunity identification
        # Scoring and ranking
        
    def calculate_opportunity_score(
        self,
        opportunity: Opportunity
    ) -> float:
        """Score opportunity quality (0-100)"""
        # Profit potential
        # Execution probability
        # Liquidity depth
        # Gas cost efficiency
        # Historical success rate
        
    def monitor_mempool(self) -> List[PendingOpportunity]:
        """Monitor mempool for opportunities"""
        # Pending transaction analysis
        # Price impact prediction
        # Arbitrage opportunity detection
        # MEV opportunity identification
        
    def analyze_market_conditions(self) -> MarketConditions:
        """Assess current market state"""
        # Volatility analysis
        # Liquidity conditions
        # Gas price trends
        # Network congestion
```

**Enterprise Configuration:**
```python
# src/app/setup/config/arbitrage.py

@dataclass
class OpportunityScannerConfig:
    """Opportunity scanner configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_mempool_monitoring: bool = True  # Premium
    enable_historical_tracking: bool = True
    enable_opportunity_alerts: bool = True
    
    # Scanning settings
    scan_interval_seconds: int = 5         # Scan every 5 seconds
    monitored_token_count: int = 100       # Top 100 tokens
    parallel_requests: int = 10            # Concurrent API calls
    
    # Opportunity thresholds
    min_opportunity_score: float = 60.0    # Score 60+ to alert
    min_profit_usd: float = 50.0
    max_execution_complexity: int = 4      # Max 4-hop paths
    
    # Price discrepancy settings
    min_price_diff_percent: float = 0.5    # Min 0.5% diff
    max_price_age_seconds: int = 10        # Max 10s old price
    
    # Market condition filters
    max_gas_price_for_scan_gwei: float = 200.0  # Stop if gas >200
    min_overall_liquidity_usd: float = 1000000.0  # $1M min
    
    # Mempool monitoring (Premium)
    mempool_scan_interval_ms: int = 100    # 100ms mempool scan
    max_pending_tx_age_seconds: int = 30
    
    # Alert settings
    alert_high_score_threshold: float = 85.0  # Immediate alert
    alert_cooldown_seconds: int = 60       # Don't spam
    max_alerts_per_hour: int = 20
    
    # Cache settings
    price_cache_ttl_seconds: int = 5       # Very short cache
    opportunity_cache_ttl_seconds: int = 30
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-A8: Real-time Scanning** | Continuously scan for opportunities | `scan_interval_seconds`, parallel requests |
| **UC-A9: Opportunity Alerts** | Notify users of profitable opportunities | Alert thresholds, cooldown settings |
| **UC-A10: Mempool Analysis** | Advanced MEV opportunity detection | `enable_mempool_monitoring=True` |
| **UC-A11: Opportunity Ranking** | Show best opportunities first | `min_opportunity_score` |
| **UC-A12: Market Filtering** | Only scan in good conditions | Gas limits, liquidity requirements |
| **UC-A13: Historical Tracking** | Track success rates | `enable_historical_tracking=True` |

---

#### **Module 3: Flash Loan Providers (2,304 lines total)**

**Sources:**
- `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/providers/flashloan_balancer.py` (892 lines)
- `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/providers/flashloan_curve.py` (734 lines)
- `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/providers/flashloan_aave.py` (678 lines)

**Target:** `src/app/infrastructure/arbitrage/flash_loans/`

**What they do:**
- Execute flash loans from multiple protocols
- Automatic fee calculation
- Gas-optimized contract calls
- Fallback provider logic
- Error handling and retry

**Core Functions to Copy:**
```python
# COPY: Flash loan execution for each provider
class BalancerFlashLoan:
    def execute_flash_loan(
        self,
        token: str,
        amount: float,
        callback_data: bytes
    ) -> FlashLoanResult:
        """Execute Balancer flash loan"""
        # Call Balancer vault
        # Execute arbitrage in callback
        # Repay loan + fee
        # Extract profit
        
class AaveFlashLoan:
    def execute_flash_loan(
        self,
        assets: List[str],
        amounts: List[float],
        callback_data: bytes
    ) -> FlashLoanResult:
        """Execute Aave flash loan"""
        # Similar structure
        
class CurveFlashLoan:
    def execute_flash_loan(
        self,
        token: str,
        amount: float,
        callback_data: bytes
    ) -> FlashLoanResult:
        """Execute Curve flash loan"""
        # Similar structure

# NEW: Provider orchestrator
class FlashLoanOrchestrator:
    def select_best_provider(
        self,
        token: str,
        amount: float
    ) -> str:
        """Choose optimal flash loan provider"""
        # Compare fees
        # Check liquidity availability
        # Consider gas costs
        # Return best option
        
    def execute_with_fallback(
        self,
        token: str,
        amount: float,
        callback_data: bytes
    ) -> FlashLoanResult:
        """Execute with automatic fallback"""
        # Try preferred provider
        # Fallback to alternatives on failure
        # Track success rates
```

**Enterprise Configuration:**
```python
# src/app/setup/config/arbitrage.py

@dataclass
class FlashLoanConfig:
    """Flash loan provider configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_balancer: bool = True
    enable_aave: bool = True
    enable_curve: bool = True
    enable_dydx: bool = False  # Future
    enable_auto_fallback: bool = True
    
    # Provider preferences (ordered by priority)
    provider_priority: List[str] = field(default_factory=lambda: [
        "balancer",  # Usually lowest fee (0.00%)
        "curve",     # Low fee (~0.04%)
        "aave",      # Higher fee (~0.09%)
    ])
    
    # Fee thresholds
    max_acceptable_fee_bps: int = 50       # Max 0.5% fee
    fee_comparison_enabled: bool = True    # Auto-select cheapest
    
    # Liquidity requirements
    min_available_liquidity_usd: float = 100000.0
    liquidity_buffer_percent: float = 10.0  # Borrow 10% less than available
    
    # Gas optimization
    use_batched_flash_loans: bool = True   # Batch multiple loans
    gas_estimation_buffer: float = 1.3     # 30% gas buffer
    
    # Execution settings
    max_flash_loan_amount_usd: float = 500000.0  # Max $500k
    flash_loan_timeout_seconds: int = 45
    
    # Retry logic
    enable_retry_on_failure: bool = True
    max_retry_attempts: int = 2
    retry_delay_seconds: int = 2
    
    # Safety limits
    require_simulation_before_execution: bool = True
    max_simultaneous_flash_loans: int = 3
    
    # Provider-specific settings
    balancer_vault_address: str = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    aave_pool_address: str = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    curve_provider_address: str = "..."  # Varies by network
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-A14: Flash Loan Execution** | Execute capital-free arbitrage | Provider flags, priority order |
| **UC-A15: Fee Optimization** | Select cheapest provider | `fee_comparison_enabled`, max fee |
| **UC-A16: Multi-Provider Fallback** | Retry on failure | `enable_auto_fallback`, retry settings |
| **UC-A17: Liquidity Check** | Verify loan availability | Liquidity requirements, buffer |
| **UC-A18: Gas Optimization** | Minimize gas costs | Batching, gas buffer |
| **UC-A19: Safety Limits** | Prevent excessive borrowing | Max loan amount, simultaneous limits |

---

#### **Module 4: MEV Protection (1,023 lines)**

**Source:** `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/mev/mev_protection.py`  
**Target:** `src/app/infrastructure/arbitrage/mev/mev_protection.py`

**What it does:**
- Private transaction submission (Flashbots, Bloxroute)
- MEV-Share profit redistribution
- Sandwich attack prevention
- Frontrunning protection
- Backrunning mitigation

**Core Functions to Copy:**
```python
# COPY: MEV protection mechanisms
class MEVProtection:
    def submit_private_transaction(
        self,
        tx: Transaction,
        relay: str = "flashbots"
    ) -> PrivateTxResult:
        """Submit tx to private mempool"""
        # Sign transaction
        # Submit to private relay
        # Wait for inclusion
        # Verify execution
        
    def calculate_optimal_tip(
        self,
        expected_profit: float,
        gas_used: int
    ) -> int:
        """Calculate MEV tip for validators"""
        # Profit sharing calculation
        # Competitive tip estimation
        # Balance profit retention
        
    def detect_mev_risk(
        self,
        tx: Transaction
    ) -> MEVRisk:
        """Assess MEV vulnerability"""
        # Sandwich attack probability
        # Frontrunning risk score
        # Expected MEV loss
        # Protection recommendation
        
    def use_mev_blocker(
        self,
        tx: Transaction
    ) -> BlockedTxResult:
        """Submit via MEV Blocker"""
        # MEV-Share integration
        # Profit redistribution
        # RPC endpoint usage
```

**Enterprise Configuration:**
```python
# src/app/setup/config/arbitrage.py

@dataclass
class MEVProtectionConfig:
    """MEV protection configuration"""
    
    # Feature flags
    enabled: bool = True
    use_private_relay: bool = True
    use_mev_blocker: bool = False  # Alternative to Flashbots
    enable_mev_share: bool = True   # Profit redistribution
    
    # Relay preferences (ordered by priority)
    preferred_relays: List[str] = field(default_factory=lambda: [
        "flashbots",      # Most popular
        "bloxroute",      # Alternative
        "eden",           # Alternative
    ])
    
    # Flashbots settings
    flashbots_relay_url: str = "https://relay.flashbots.net"
    flashbots_auth_key: str = ""  # Set via env var
    flashbots_builder_preference: List[str] = field(default_factory=lambda: [
        "builder0x69", "beaverbuild", "flashbots"
    ])
    
    # MEV tip calculation
    min_profit_tip_percent: float = 5.0    # Min 5% to validators
    max_profit_tip_percent: float = 20.0   # Max 20% tip
    competitive_tip_multiplier: float = 1.1  # 10% above competition
    
    # MEV risk thresholds
    high_risk_threshold: float = 0.5       # >0.5% expected loss = high
    require_protection_if_risk_bps: int = 10  # Protect if >0.1% risk
    
    # Transaction settings
    max_blocks_for_inclusion: int = 3      # Try for 3 blocks
    revert_protection: bool = True         # Don't include if revert
    
    # MEV-Share settings (Profit redistribution)
    mev_share_enabled: bool = True
    user_profit_share_percent: float = 90.0  # Users get 90%
    
    # MEV Blocker (Alternative)
    mev_blocker_rpc: str = "https://rpc.mevblocker.io"
    mev_blocker_kickback_address: str = ""  # Where to receive kickback
    
    # Monitoring
    track_mev_saved: bool = True
    log_mev_attempts: bool = True
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-A20: Private Transactions** | Hide trades from public mempool | `use_private_relay=True`, relay prefs |
| **UC-A21: MEV Risk Assessment** | Show MEV risk before trade | Risk thresholds, detection settings |
| **UC-A22: Validator Tips** | Optimize tips for inclusion | Tip calculation params |
| **UC-A23: Profit Sharing** | MEV-Share integration | `mev_share_enabled`, user share percent |
| **UC-A24: MEV Blocker** | Alternative protection method | `use_mev_blocker=True` |
| **UC-A25: MEV Analytics** | Track MEV savings | `track_mev_saved=True` |

---

#### **Module 5: Multi-Relay Broadcaster (1,245 lines)**

**Source:** `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT/relay/multi_relay_broadcaster.py`  
**Target:** `src/app/infrastructure/arbitrage/relay/multi_relay_broadcaster.py`

**What it does:**
- Simultaneous submission to multiple relays
- Relay performance tracking
- Automatic relay selection
- Bundle creation and optimization
- Relay failover logic

**Core Functions to Copy:**
```python
# COPY: Multi-relay broadcasting
class MultiRelayBroadcaster:
    def broadcast_to_all_relays(
        self,
        tx: Transaction
    ) -> BroadcastResult:
        """Submit to all enabled relays simultaneously"""
        # Parallel submission
        # Track which relay includes first
        # Record performance metrics
        
    def create_bundle(
        self,
        txs: List[Transaction]
    ) -> Bundle:
        """Create transaction bundle"""
        # Bundle multiple txs
        # Optimize ordering
        # Calculate total profit
        # Set bundle tip
        
    def select_optimal_relay(
        self,
        tx_metadata: TxMetadata
    ) -> str:
        """Choose best relay for tx"""
        # Historical success rates
        # Current network conditions
        # Relay availability
        # Profit maximization
        
    def monitor_relay_health(self) -> Dict[str, RelayHealth]:
        """Track relay status"""
        # Response times
        # Success rates
        # Inclusion rates
        # Uptime monitoring
```

**Enterprise Configuration:**
```python
# src/app/setup/config/arbitrage.py

@dataclass
class RelayBroadcasterConfig:
    """Multi-relay broadcaster configuration"""
    
    # Feature flags
    enabled: bool = True
    broadcast_to_all: bool = True          # Parallel submission
    enable_relay_selection: bool = True     # Auto-select best
    enable_bundle_creation: bool = True
    enable_health_monitoring: bool = True
    
    # Supported relays
    enabled_relays: List[str] = field(default_factory=lambda: [
        "flashbots",
        "bloxroute",
        "eden",
        "manifold",
        "builder0x69",
    ])
    
    # Broadcasting strategy
    broadcast_strategy: str = "all"         # all, best, round_robin
    min_relays_for_submission: int = 2      # Submit to at least 2
    
    # Relay endpoints
    relay_endpoints: Dict[str, str] = field(default_factory=lambda: {
        "flashbots": "https://relay.flashbots.net",
        "bloxroute": "https://mev.api.blxrbdn.com",
        "eden": "https://api.edennetwork.io/v1/rpc",
    })
    
    # Performance tracking
    track_inclusion_rate: bool = True
    track_response_times: bool = True
    performance_window_hours: int = 24      # 24h rolling window
    
    # Relay selection criteria
    min_historical_success_rate: float = 0.70  # 70% success rate
    max_avg_response_time_ms: int = 500
    prefer_faster_relays: bool = True
    
    # Bundle settings
    max_txs_per_bundle: int = 5
    bundle_tip_percent: float = 10.0        # 10% of bundle profit
    
    # Failover logic
    enable_failover: bool = True
    failover_delay_seconds: int = 2
    max_failover_attempts: int = 3
    
    # Health monitoring
    health_check_interval_minutes: int = 5
    mark_unhealthy_after_failures: int = 3
    auto_disable_unhealthy_relays: bool = True
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-A26: Multi-Relay Submission** | Maximize inclusion probability | `broadcast_to_all=True`, enabled relays |
| **UC-A27: Relay Performance** | Show relay stats | Performance tracking flags |
| **UC-A28: Optimal Relay Selection** | Auto-select best relay | Selection criteria, success rate |
| **UC-A29: Bundle Creation** | Create multi-tx bundles | Bundle settings, max txs |
| **UC-A30: Relay Failover** | Fallback on relay failure | Failover settings, attempts |
| **UC-A31: Health Monitoring** | Track relay status | Health check interval, auto-disable |

---

### **2.2 Arbitrage Integration Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                (FastAPI + WebSocket)                         │
├─────────────────────────────────────────────────────────────┤
│  POST /api/v1/arbitrage/scan                                │
│  POST /api/v1/arbitrage/execute                             │
│  POST /api/v1/arbitrage/simulate                            │
│  GET  /api/v1/arbitrage/opportunities                       │
│  GET  /api/v1/arbitrage/history                             │
│  WS   /ws/arbitrage/opportunities                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│                      (Interactors)                           │
├─────────────────────────────────────────────────────────────┤
│  ScanArbitrageOpportunities                                 │
│  ExecuteArbitrageTrade                                      │
│  SimulateArbitrage                                          │
│  GetArbitrageHistory                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│            (Arbitrage Modules - COPIED)                      │
├─────────────────────────────────────────────────────────────┤
│  src/app/infrastructure/arbitrage/                          │
│    ├── core/                                                │
│    │   ├── arbitrage_engine.py      (COPIED 2,134 lines)   │
│    │   └── opportunity_scanner.py   (COPIED 1,456 lines)   │
│    ├── flash_loans/                                         │
│    │   ├── balancer.py              (COPIED 892 lines)     │
│    │   ├── aave.py                  (COPIED 678 lines)     │
│    │   └── curve.py                 (COPIED 734 lines)     │
│    ├── mev/                                                 │
│    │   └── mev_protection.py        (COPIED 1,023 lines)   │
│    └── relay/                                               │
│        └── multi_relay_broadcaster.py (COPIED 1,245 lines) │
│                                                              │
│  src/app/infrastructure/arbitrage/services/                 │
│    └── arbitrage_service.py         (NEW - orchestrator)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                          │
├─────────────────────────────────────────────────────────────┤
│  ✅ KEEP: DEX APIs (1inch, Uniswap, Curve, Balancer)       │
│  ✅ KEEP: Flash loan protocols                              │
│  ✅ KEEP: MEV relays (Flashbots, Bloxroute)                │
│  ✅ ADDED: Anvil Web3 setup                                 │
│  ✅ ADDED: PostgreSQL for history                           │
│  ✅ ADDED: WebSocket for real-time alerts                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 💼 **3. CRYPTO PORTFOLIO TRACKER** {#crypto-portfolio-tracker}

### **3.1 What to Copy: Data Models & Tracking Logic (~2,000 lines)**

**Source:** `libs/crypto_tracker/src/`  
**Target:** `src/app/infrastructure/portfolio/`

**What to Copy:**
```python
# COPY: Portfolio data models
from libs/crypto_tracker/src/database/models.py:
  - Portfolio model
  - Wallet model
  - Transaction model
  - Position model
  - HistoricalBalance model

# COPY: Multi-chain tracking service
from libs/crypto_tracker/src/services/portfolio_service.py:
  - Multi-wallet balance aggregation
  - Cross-chain position tracking
  - DeFi protocol integration (Uniswap, Aave, Compound)
  - Transaction history parsing
  - PnL calculations

# COPY: Blockchain fetchers
from libs/crypto_tracker/src/api/blockchain_fetchers.py:
  - Ethereum balance fetcher
  - BSC balance fetcher
  - Polygon balance fetcher
  - Token balance aggregation
```

**Enterprise Configuration:**
```python
# src/app/setup/config/portfolio.py

@dataclass
class PortfolioTrackerConfig:
    """Portfolio tracker configuration"""
    
    # Feature flags
    enabled: bool = True
    enable_multi_chain: bool = True
    enable_defi_tracking: bool = True
    enable_nft_tracking: bool = False  # Future
    enable_tax_reporting: bool = True  # Premium
    
    # Supported chains
    enabled_chains: List[str] = field(default_factory=lambda: [
        "ethereum", "polygon", "bsc", "arbitrum", "optimism", "base"
    ])
    
    # Tracking settings
    sync_interval_minutes: int = 15        # Sync every 15 min
    track_dust_positions: bool = False     # Ignore <$1 positions
    min_position_value_usd: float = 1.0
    
    # DeFi protocol support
    supported_protocols: List[str] = field(default_factory=lambda: [
        "uniswap_v2", "uniswap_v3", "aave", "compound", 
        "curve", "convex", "yearn"
    ])
    
    # RPC endpoints
    eth_rpc_url: str = "https://eth.llamarpc.com"
    polygon_rpc_url: str = "https://polygon.llamarpc.com"
    bsc_rpc_url: str = "https://bsc-dataseed.binance.org"
    
    # Performance
    max_wallets_per_user: int = 50
    max_historical_days: int = 365         # 1 year history
    cache_balance_ttl_minutes: int = 10
    
    # Tax reporting (Premium)
    tax_calculation_method: str = "fifo"   # fifo, lifo, hifo
    include_gas_in_cost_basis: bool = True
    generate_8949_form: bool = True
```

**Use Cases Affected:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-P1: Multi-Wallet Tracking** | Track all user wallets | `max_wallets_per_user`, chains |
| **UC-P2: DeFi Position Tracking** | Show LP tokens, staked assets | `enable_defi_tracking`, protocols |
| **UC-P3: Portfolio Dashboard** | Real-time portfolio value | Sync interval, cache TTL |
| **UC-P4: Transaction History** | Show all transactions | `max_historical_days` |
| **UC-P5: Tax Reporting** | Generate tax reports | `enable_tax_reporting`, method |
| **UC-P6: PnL Calculations** | Show profit/loss | Cost basis settings |

---

## 📊 **4. AAVE V3 DATA** {#aave-v3-data}

### **4.1 Integration (HTTP Client - No Code Copying)**

**Target:** `src/app/infrastructure/aave/aave_client.py`

**Implementation:**
```python
# NEW: Simple HTTP client (no copying needed)
class AaveDataClient:
    BASE_URL = "https://th3nolo.github.io/aave-v3-data"
    
    async def get_all_markets(self) -> List[AaveMarket]:
        """Fetch all Aave V3 markets"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/aave_v3_data.json")
            data = response.json()
            # Parse and return
            
    async def get_reserve_data(self, asset: str) -> ReserveData:
        """Get reserve data for specific asset"""
        # Fetch + filter
```

**Enterprise Configuration:**
```python
# src/app/setup/config/aave.py

@dataclass
class AaveDataConfig:
    """Aave V3 data configuration"""
    
    enabled: bool = True
    api_base_url: str = "https://th3nolo.github.io/aave-v3-data"
    cache_ttl_minutes: int = 30
    supported_networks: List[str] = field(default_factory=lambda: [
        "ethereum", "polygon", "arbitrum", "optimism"
    ])
```

**Use Cases:**

| Use Case | Description | Configuration Impact |
|----------|-------------|---------------------|
| **UC-AV1: Lending Rates** | Show current lending rates | Cache TTL |
| **UC-AV2: Borrow Rates** | Show borrowing costs | Networks supported |
| **UC-AV3: Risk Dashboard** | Display risk parameters | API URL |

---

## 🧮 **5. DEFI TOOLS** {#defi-tools}

### **5.1 What to Copy: Utility Functions (606 lines)**

**Source:** `libs/defi/defi/defi_tools.py`  
**Target:** `src/app/utils/defi_calculations.py`

**Functions to Copy:**
```python
# COPY: IL calculator
def calculate_impermanent_loss(price_ratio: float) -> float:
    """Calculate impermanent loss percentage"""
    il = 2 * (price_ratio**0.5 / (1 + price_ratio)) - 1
    return il

# COPY: Staking vs farming comparison
def compare_yield_strategies(
    days: int,
    price_change_a: float,
    price_change_b: float,
    stake_apy_a: float,
    stake_apy_b: float,
    farm_apy: float,
    farm_fees_apy: float
) -> Dict[str, float]:
    """Compare buy-hold vs staking vs LP farming"""
    # Calculations...
    
# COPY: DeFiLlama integration
def get_protocol_tvl(protocol: str) -> float:
    """Fetch TVL from DeFiLlama API"""
    # API call...
```

**Enterprise Configuration:**
```python
# src/app/setup/config/defi_tools.py

@dataclass
class DeFiToolsConfig:
    enabled: bool = True
    enable_il_calculator: bool = True
    enable_yield_comparison: bool = True
    enable_tvl_tracking: bool = True
    cache_ttl_minutes: int = 60
```

---

## 📈 **6. YIELD CALCULATOR** {#yield-calculator}

### **6.1 What to Copy: Calculation Logic (~500 lines)**

**Source:** `libs/defi-yield-calculator/src/yield_calculator.py`  
**Target:** `src/app/utils/yield_calculator.py`

**Functions to Copy:**
```python
# COPY: Yield calculation
def calculate_defi_yield(
    principal: float,
    apr: float,
    days: int,
    compound_frequency: str = "daily"
) -> YieldResult:
    """Calculate DeFi yield with compounding"""
    # Compound interest calculations
    # IL adjustments
    # Gas cost considerations
```

**Configuration:**
```python
@dataclass
class YieldCalculatorConfig:
    enabled: bool = True
    default_compound_frequency: str = "daily"
    include_gas_costs: bool = True
    avg_gas_price_gwei: float = 30.0
```

---

## ⚙️ **7. CONFIGURATION SYSTEM ARCHITECTURE** {#configuration-system}

### **7.1 Master Configuration File**

```python
# src/app/setup/config/libs.py

from dataclasses import dataclass, field
from typing import List, Dict
import os

@dataclass
class LibraryFeaturesConfig:
    """Master configuration for all library integrations"""
    
    # ═══════════════════════════════════════════════════════
    # TIER 1: CRITICAL (Revenue Generators)
    # ═══════════════════════════════════════════════════════
    
    # ULTRA Arbitrage Bot
    ultra_arbitrage_enabled: bool = False
    arbitrage: 'ArbitrageConfig' = field(default_factory=lambda: ArbitrageConfig())
    
    # Hunter AI Bot
    hunter_enabled: bool = False
    hunter: 'HunterConfig' = field(default_factory=lambda: HunterConfig())
    
    # ═══════════════════════════════════════════════════════
    # TIER 2: VALUE-ADD
    # ═══════════════════════════════════════════════════════
    
    # Crypto Portfolio Tracker
    portfolio_tracker_enabled: bool = False
    portfolio: 'PortfolioTrackerConfig' = field(default_factory=lambda: PortfolioTrackerConfig())
    
    # Aave V3 Data
    aave_data_enabled: bool = False
    aave: 'AaveDataConfig' = field(default_factory=lambda: AaveDataConfig())
    
    # ═══════════════════════════════════════════════════════
    # TIER 3: EDUCATIONAL
    # ═══════════════════════════════════════════════════════
    
    # DeFi Tools
    defi_tools_enabled: bool = False
    defi_tools: 'DeFiToolsConfig' = field(default_factory=lambda: DeFiToolsConfig())
    
    # Yield Calculator
    yield_calculator_enabled: bool = False
    yield_calc: 'YieldCalculatorConfig' = field(default_factory=lambda: YieldCalculatorConfig())
    
    # ═══════════════════════════════════════════════════════
    # ALREADY IMPLEMENTED
    # ═══════════════════════════════════════════════════════
    
    agent_squad_enabled: bool = True
    agno_enabled: bool = True
    graphrag_enabled: bool = True
    mcp_enabled: bool = True


def load_library_features() -> LibraryFeaturesConfig:
    """Load library feature flags from environment/TOML"""
    return LibraryFeaturesConfig(
        # TIER 1
        ultra_arbitrage_enabled=_get_bool_env("ULTRA_ARBITRAGE_ENABLED", False),
        hunter_enabled=_get_bool_env("HUNTER_ENABLED", False),
        
        # TIER 2
        portfolio_tracker_enabled=_get_bool_env("PORTFOLIO_ENABLED", False),
        aave_data_enabled=_get_bool_env("AAVE_DATA_ENABLED", False),
        
        # TIER 3
        defi_tools_enabled=_get_bool_env("DEFI_TOOLS_ENABLED", False),
        yield_calculator_enabled=_get_bool_env("YIELD_CALC_ENABLED", False),
    )


def _get_bool_env(key: str, default: bool) -> bool:
    """Helper to parse boolean env vars"""
    return os.getenv(key, str(default)).lower() == "true"
```

### **7.2 TOML Configuration Example**

```toml
# config/local/config.toml

[libraries]
# Master feature flags (all default to false for safety)
ultra_arbitrage_enabled = false
hunter_enabled = false
portfolio_tracker_enabled = false
aave_data_enabled = false
defi_tools_enabled = false
yield_calculator_enabled = false

# ═══════════════════════════════════════════════════════
# HUNTER AI BOT CONFIGURATION
# ═══════════════════════════════════════════════════════

[libraries.hunter]
# Core modules
enable_sentiment_analysis = true
enable_price_prediction = true
enable_risk_assessment = true
enable_pattern_recognition = true
enable_portfolio_optimization = true
enable_microstructure_analysis = true

# Sentiment analyzer
[libraries.hunter.sentiment]
min_sentiment_score = 30.0
max_sentiment_score = 70.0
twitter_weight = 0.35
reddit_weight = 0.25

# Price predictor
[libraries.hunter.price_predictor]
enable_24h_predictions = true
enable_7d_predictions = false  # Premium
confidence_level = 0.90

# Risk assessor
[libraries.hunter.risk]
low_risk_threshold = 30.0
high_risk_threshold = 60.0
require_audit = true
min_liquidity_usd = 100000.0

# ═══════════════════════════════════════════════════════
# ULTRA ARBITRAGE BOT CONFIGURATION
# ═══════════════════════════════════════════════════════

[libraries.arbitrage]
# Core settings
enable_flash_loans = true
enable_mev_protection = true
enable_simulation_mode = true

# Discovery
max_hop_count = 3
min_profit_threshold_usd = 50.0

# Risk limits (CRITICAL)
max_position_size_usd = 100000.0
max_daily_trades = 50
max_daily_loss_usd = 5000.0

# MEV protection
use_private_relay = true
preferred_relay = "flashbots"
mev_protection_tip_percent = 10.0

# Flash loans
[libraries.arbitrage.flash_loans]
preferred_provider = "balancer"
max_acceptable_fee_bps = 50

# ═══════════════════════════════════════════════════════
# PORTFOLIO TRACKER CONFIGURATION
# ═══════════════════════════════════════════════════════

[libraries.portfolio]
enable_multi_chain = true
enable_defi_tracking = true
enable_tax_reporting = false  # Premium

enabled_chains = ["ethereum", "polygon", "bsc"]
sync_interval_minutes = 15

# ═══════════════════════════════════════════════════════
# AAVE V3 DATA CONFIGURATION
# ═══════════════════════════════════════════════════════

[libraries.aave]
api_base_url = "https://th3nolo.github.io/aave-v3-data"
cache_ttl_minutes = 30
```

### **7.3 Environment Variables (Secrets)**

```bash
# .env (not tracked in git)

# ═══════════════════════════════════════════════════════
# MASTER FEATURE FLAGS
# ═══════════════════════════════════════════════════════
ULTRA_ARBITRAGE_ENABLED=false
HUNTER_ENABLED=false
PORTFOLIO_ENABLED=false

# ═══════════════════════════════════════════════════════
# HUNTER AI BOT SECRETS
# ═══════════════════════════════════════════════════════
TWITTER_API_KEY=your_twitter_key
REDDIT_API_KEY=your_reddit_key
DISCORD_BOT_TOKEN=your_discord_token

# ═══════════════════════════════════════════════════════
# ARBITRAGE BOT SECRETS
# ═══════════════════════════════════════════════════════
FLASHBOTS_AUTH_KEY=your_flashbots_key
BLOXROUTE_AUTH_TOKEN=your_bloxroute_token
MEV_BLOCKER_API_KEY=your_mev_blocker_key

# Flash loan provider keys (if needed)
AAVE_PRIVATE_KEY=your_aave_key
BALANCER_PRIVATE_KEY=your_balancer_key

# ═══════════════════════════════════════════════════════
# PORTFOLIO TRACKER SECRETS
# ═══════════════════════════════════════════════════════
ETHERSCAN_API_KEY=your_etherscan_key
POLYGONSCAN_API_KEY=your_polygonscan_key
BSCSCAN_API_KEY=your_bscscan_key

# RPC endpoints (optional - defaults to public)
ETH_RPC_URL=https://your-private-eth-rpc.com
POLYGON_RPC_URL=https://your-private-polygon-rpc.com
```

---

## 📋 **8. USE CASES & FEATURE MATRIX** {#use-cases-matrix}

### **8.1 Complete Use Case Mapping**

| Use Case ID | Feature | Library | Config Flag | User Tier | Priority |
|-------------|---------|---------|-------------|-----------|----------|
| **HUNTER AI BOT** |
| UC-H1 | Token Sentiment Analysis | Hunter | `hunter.sentiment.enabled` | Free | HIGH |
| UC-H2 | AI Risk Scoring | Hunter | `hunter.risk.enabled` | Free | HIGH |
| UC-H3 | Real-time Sentiment Alerts | Hunter | `hunter.sentiment.alerts` | Premium | MEDIUM |
| UC-H4 | Portfolio Sentiment Score | Hunter | `hunter.sentiment.portfolio` | Premium | MEDIUM |
| UC-H5 | Market Intelligence Dashboard | Hunter | `hunter.sentiment.dashboard` | Free | HIGH |
| UC-H6 | 24h Price Forecasting | Hunter | `hunter.predictor.enable_24h` | Free | HIGH |
| UC-H7 | AI Trading Signals | Hunter | `hunter.predictor.signals` | Premium | HIGH |
| UC-H8 | Risk-Adjusted Predictions | Hunter | `hunter.predictor.risk_adjusted` | Premium | MEDIUM |
| UC-H9 | Portfolio Planning | Hunter | `hunter.optimizer.enabled` | Premium | MEDIUM |
| UC-H10 | 7-Day Price Predictions | Hunter | `hunter.predictor.enable_7d` | Ultra Premium | LOW |
| UC-H11 | Token Risk Scoring | Hunter | `hunter.risk.token_score` | Free | HIGH |
| UC-H12 | Portfolio Risk Dashboard | Hunter | `hunter.risk.portfolio` | Premium | HIGH |
| UC-H13 | High Risk Alerts | Hunter | `hunter.risk.alerts` | Premium | MEDIUM |
| UC-H14 | Smart Contract Validation | Hunter | `hunter.risk.contract_check` | Free | HIGH |
| UC-H15 | Trading Guardrails | Hunter | `hunter.risk.guardrails` | Premium | HIGH |
| UC-H16 | Liquidity Warnings | Hunter | `hunter.risk.liquidity_check` | Free | MEDIUM |
| UC-H17 | Chart Pattern Alerts | Hunter | `hunter.patterns.alerts` | Premium | MEDIUM |
| UC-H18 | Pattern Recognition | Hunter | `hunter.patterns.enabled` | Free | HIGH |
| UC-H19 | Support/Resistance Lines | Hunter | `hunter.patterns.sr_lines` | Free | MEDIUM |
| UC-H20 | Breakout Signals | Hunter | `hunter.patterns.breakouts` | Premium | HIGH |
| UC-H21 | Pattern Success Stats | Hunter | `hunter.patterns.stats` | Free | LOW |
| UC-H22 | Multi-Timeframe Analysis | Hunter | `hunter.patterns.multi_tf` | Premium | MEDIUM |
| UC-H23 | Portfolio Optimization | Hunter | `hunter.optimizer.enabled` | Premium | HIGH |
| UC-H24 | Efficient Frontier | Hunter | `hunter.optimizer.frontier` | Premium | MEDIUM |
| UC-H25 | Rebalancing Alerts | Hunter | `hunter.optimizer.rebalance` | Premium | MEDIUM |
| UC-H26 | Tax-Loss Harvesting | Hunter | `hunter.optimizer.tax_harvest` | Ultra Premium | LOW |
| UC-H27 | Strategy Backtesting | Hunter | `hunter.optimizer.backtest` | Premium | MEDIUM |
| UC-H28 | Risk-Adjusted Returns | Hunter | `hunter.optimizer.sharpe` | Premium | MEDIUM |
| UC-H29 | Allocation Constraints | Hunter | `hunter.optimizer.constraints` | Premium | LOW |
| UC-H30 | Order Book Depth | Hunter | `hunter.microstructure.book` | Free | MEDIUM |
| UC-H31 | Spread Monitoring | Hunter | `hunter.microstructure.spread` | Premium | LOW |
| UC-H32 | Buy/Sell Pressure | Hunter | `hunter.microstructure.flow` | Free | HIGH |
| UC-H33 | Whale Alerts | Hunter | `hunter.microstructure.whale` | Premium | HIGH |
| UC-H34 | MEV Protection Warnings | Hunter | `hunter.microstructure.mev` | Premium | MEDIUM |
| UC-H35 | Smart Money Tracking | Hunter | `hunter.microstructure.smart_money` | Ultra Premium | MEDIUM |
| UC-H36 | Liquidity Analysis | Hunter | `hunter.microstructure.liquidity` | Free | MEDIUM |
| **ULTRA ARBITRAGE BOT** |
| UC-A1 | Arbitrage Discovery | Arbitrage | `arbitrage.enabled` | Ultra Premium | HIGH |
| UC-A2 | Profit Calculation | Arbitrage | `arbitrage.profit_calc` | Ultra Premium | HIGH |
| UC-A3 | Flash Loan Arbitrage | Arbitrage | `arbitrage.flash_loans.enabled` | Ultra Premium | HIGH |
| UC-A4 | MEV Protection | Arbitrage | `arbitrage.mev.enabled` | Ultra Premium | HIGH |
| UC-A5 | Simulation Mode | Arbitrage | `arbitrage.simulation` | Ultra Premium | HIGH |
| UC-A6 | Risk Management | Arbitrage | `arbitrage.risk_limits` | Ultra Premium | CRITICAL |
| UC-A7 | Auto-Execution | Arbitrage | `arbitrage.auto_execute` | Ultra Premium | HIGH |
| UC-A8 | Real-time Scanning | Arbitrage | `arbitrage.scanner.enabled` | Ultra Premium | HIGH |
| UC-A9 | Opportunity Alerts | Arbitrage | `arbitrage.scanner.alerts` | Ultra Premium | MEDIUM |
| UC-A10 | Mempool Analysis | Arbitrage | `arbitrage.scanner.mempool` | Ultra Premium | MEDIUM |
| UC-A11 | Opportunity Ranking | Arbitrage | `arbitrage.scanner.ranking` | Ultra Premium | MEDIUM |
| UC-A12 | Market Filtering | Arbitrage | `arbitrage.scanner.filters` | Ultra Premium | MEDIUM |
| UC-A13 | Historical Tracking | Arbitrage | `arbitrage.scanner.history` | Ultra Premium | LOW |
| UC-A14 | Flash Loan Execution | Arbitrage | `arbitrage.flash_loans.execute` | Ultra Premium | HIGH |
| UC-A15 | Fee Optimization | Arbitrage | `arbitrage.flash_loans.fee_opt` | Ultra Premium | MEDIUM |
| UC-A16 | Multi-Provider Fallback | Arbitrage | `arbitrage.flash_loans.fallback` | Ultra Premium | HIGH |
| UC-A17 | Liquidity Check | Arbitrage | `arbitrage.flash_loans.liquidity` | Ultra Premium | HIGH |
| UC-A18 | Gas Optimization | Arbitrage | `arbitrage.flash_loans.gas_opt` | Ultra Premium | MEDIUM |
| UC-A19 | Safety Limits | Arbitrage | `arbitrage.flash_loans.limits` | Ultra Premium | CRITICAL |
| UC-A20 | Private Transactions | Arbitrage | `arbitrage.mev.private_relay` | Ultra Premium | HIGH |
| UC-A21 | MEV Risk Assessment | Arbitrage | `arbitrage.mev.risk_assessment` | Ultra Premium | HIGH |
| UC-A22 | Validator Tips | Arbitrage | `arbitrage.mev.tips` | Ultra Premium | MEDIUM |
| UC-A23 | Profit Sharing (MEV-Share) | Arbitrage | `arbitrage.mev.mev_share` | Ultra Premium | MEDIUM |
| UC-A24 | MEV Blocker | Arbitrage | `arbitrage.mev.mev_blocker` | Ultra Premium | LOW |
| UC-A25 | MEV Analytics | Arbitrage | `arbitrage.mev.analytics` | Ultra Premium | LOW |
| UC-A26 | Multi-Relay Submission | Arbitrage | `arbitrage.relay.multi` | Ultra Premium | HIGH |
| UC-A27 | Relay Performance | Arbitrage | `arbitrage.relay.performance` | Ultra Premium | MEDIUM |
| UC-A28 | Optimal Relay Selection | Arbitrage | `arbitrage.relay.selection` | Ultra Premium | MEDIUM |
| UC-A29 | Bundle Creation | Arbitrage | `arbitrage.relay.bundles` | Ultra Premium | LOW |
| UC-A30 | Relay Failover | Arbitrage | `arbitrage.relay.failover` | Ultra Premium | MEDIUM |
| UC-A31 | Relay Health Monitoring | Arbitrage | `arbitrage.relay.health` | Ultra Premium | LOW |
| **PORTFOLIO TRACKER** |
| UC-P1 | Multi-Wallet Tracking | Portfolio | `portfolio.multi_wallet` | Free | HIGH |
| UC-P2 | DeFi Position Tracking | Portfolio | `portfolio.defi_tracking` | Premium | HIGH |
| UC-P3 | Portfolio Dashboard | Portfolio | `portfolio.dashboard` | Free | HIGH |
| UC-P4 | Transaction History | Portfolio | `portfolio.tx_history` | Free | MEDIUM |
| UC-P5 | Tax Reporting | Portfolio | `portfolio.tax_reporting` | Premium | MEDIUM |
| UC-P6 | PnL Calculations | Portfolio | `portfolio.pnl` | Free | HIGH |
| **AAVE V3 DATA** |
| UC-AV1 | Lending Rates | Aave | `aave.lending_rates` | Free | MEDIUM |
| UC-AV2 | Borrow Rates | Aave | `aave.borrow_rates` | Free | MEDIUM |
| UC-AV3 | Risk Dashboard | Aave | `aave.risk_dashboard` | Premium | MEDIUM |
| **DEFI TOOLS** |
| UC-DT1 | IL Calculator | DeFi Tools | `defi_tools.il_calc` | Free | MEDIUM |
| UC-DT2 | Yield Comparison | DeFi Tools | `defi_tools.yield_comp` | Free | MEDIUM |
| UC-DT3 | TVL Tracking | DeFi Tools | `defi_tools.tvl` | Free | LOW |
| **YIELD CALCULATOR** |
| UC-YC1 | Yield Estimation | Yield Calc | `yield_calc.enabled` | Free | LOW |
| UC-YC2 | Compound Interest | Yield Calc | `yield_calc.compound` | Free | LOW |

---

## 🎯 **STATUS & NEXT STEPS**

**Status:** ✅ **DETAILED EXTRACTION PLAN COMPLETE**

**Deliverables:**
- ✅ 6 AI modules detailed (Hunter: ~5,000 lines)
- ✅ 5 arbitrage modules detailed (ULTRA: ~8,000 lines)
- ✅ Portfolio tracker extraction plan
- ✅ Aave integration strategy
- ✅ DeFi tools extraction plan
- ✅ Yield calculator extraction plan
- ✅ Complete configuration system
- ✅ 67 use cases mapped
- ✅ Enterprise-grade configs for all

**Total Lines to Copy:** ~16,000 lines of core value  
**Total Configs Created:** 200+ configuration parameters  
**Total Use Cases:** 67 mapped use cases

**Next Step:** Begin Week 1 extraction (ULTRA Arbitrage Engine)

**Ready For:** Executive approval & implementation kickoff! 🚀
