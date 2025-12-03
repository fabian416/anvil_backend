# Feature Flags Reference - Complete Library Control

**Purpose:** Enterprise-grade enable/disable switches for all library integrations  
**Location:** `.env.local`, `.env.prod`, or TOML configuration  
**Default:** All new features **OFF** by default (safe deployment)

---

## 🎛️ **MASTER FEATURE FLAGS**

### **Syntax:**
```bash
FEATURE_NAME_ENABLED=false  # or true
```

### **All Flags:**

```bash
# ============================================================
# LIBRARY FEATURE FLAGS - MASTER SWITCHES
# ============================================================

# ───────────────────────────────────────────────────────────
# TIER 1: CRITICAL - REVENUE GENERATORS
# ───────────────────────────────────────────────────────────

# ULTRA-PRODUCTION DeFi Arbitrage Bot
ULTRA_ARBITRAGE_ENABLED=false           # Master switch
ULTRA_ARBITRAGE_AUTO_EXEC=false         # Auto-execution (requires manual approval if false)
ULTRA_ARBITRAGE_FLASH_LOANS=true        # Enable flash loans
ULTRA_ARBITRAGE_MEV_PROTECTION=true     # Enable MEV protection
ULTRA_ARBITRAGE_MIN_PROFIT=50           # Min $50 profit to execute
ULTRA_ARBITRAGE_MAX_POSITION=100000     # Max $100k per trade
ULTRA_ARBITRAGE_MAX_DAILY_LOSS=5000     # Max $5k loss per day

# Hunter AI Trading Bot
HUNTER_ENABLED=false                    # Master switch
HUNTER_AUTO_TRADING=false               # Auto-trading (manual if false)
HUNTER_AI_ANALYSIS=true                 # AI analysis engine
HUNTER_TOKEN_SCANNER=true               # Token scanner
HUNTER_PORTFOLIO_TRACKING=true          # Portfolio management
HUNTER_MAX_POSITION_SIZE=1000           # Max $1k per trade
HUNTER_MAX_POSITIONS=10                 # Max 10 concurrent positions
HUNTER_MAX_DAILY_LOSS=500               # Max $500 loss per day

# ───────────────────────────────────────────────────────────
# TIER 2: VALUE-ADD FEATURES
# ───────────────────────────────────────────────────────────

# Crypto Portfolio Tracker
PORTFOLIO_ENABLED=false                 # Master switch
PORTFOLIO_DEFI_TRACKING=true            # Track DeFi positions
PORTFOLIO_TAX_REPORTS=false             # Generate tax reports (premium)
PORTFOLIO_SYNC_INTERVAL=15              # Sync every 15 minutes

# Aave V3 Data API
AAVE_DATA_ENABLED=false                 # Master switch
AAVE_CACHE_TTL=3600                     # Cache for 1 hour (data updates daily)

# ───────────────────────────────────────────────────────────
# TIER 3: EDUCATIONAL & TOOLS
# ───────────────────────────────────────────────────────────

# DeFi Tools Library
DEFI_TOOLS_ENABLED=false                # Master switch

# DeFi Yield Calculator
YIELD_CALC_ENABLED=false                # Master switch

# ───────────────────────────────────────────────────────────
# ALREADY IMPLEMENTED (Phases 1-6)
# ───────────────────────────────────────────────────────────

# Agent Squad (Multi-Agent Orchestration)
AGENT_SQUAD_ENABLED=true                # Master switch
AGENT_SQUAD_USE_LIBRARY=false           # Use Agent Squad library vs hand-rolled

# Agno (Agent Runtime + MCP)
AGNO_ENABLED=true                       # Master switch

# GraphRAG (Knowledge Graph Retrieval)
GRAPHRAG_ENABLED=true                   # Master switch

# MCP Servers (Data Providers)
MCP_ONEINCH_ENABLED=true                # 1inch DEX
MCP_DEFILLAMA_ENABLED=true              # DeFiLlama analytics
MCP_THEGRAPH_ENABLED=true               # The Graph queries
MCP_COINGECKO_ENABLED=true              # CoinGecko prices
```

---

## 🔐 **SECURITY LEVELS**

### **Trading Bot Safety:**

```bash
# ULTRA Arbitrage Bot - HIGHEST SECURITY
ULTRA_ARBITRAGE_ENABLED=false           # Must explicitly enable
ULTRA_ARBITRAGE_AUTO_EXEC=false         # Manual approval required
ULTRA_ARBITRAGE_MULTI_SIG=true          # Multi-sig for >$10k trades
ULTRA_ARBITRAGE_EMERGENCY_STOP=true     # Emergency stop available

# Hunter Trading Bot - HIGH SECURITY
HUNTER_ENABLED=false                    # Must explicitly enable
HUNTER_AUTO_TRADING=false               # Manual trading only initially
HUNTER_REQUIRE_2FA=true                 # 2FA for trade execution
```

### **Data Services:**

```bash
# Lower risk, can enable more freely
AAVE_DATA_ENABLED=false                 # Read-only API
PORTFOLIO_ENABLED=false                 # Read-only tracking
DEFI_TOOLS_ENABLED=false                # Educational tools
```

---

## 🚀 **DEPLOYMENT SCENARIOS**

### **Scenario 1: Development Environment**
```bash
# .env.local

# Enable all for testing
ULTRA_ARBITRAGE_ENABLED=true
HUNTER_ENABLED=true
PORTFOLIO_ENABLED=true
AAVE_DATA_ENABLED=true

# But keep auto-trading OFF
ULTRA_ARBITRAGE_AUTO_EXEC=false
HUNTER_AUTO_TRADING=false

# Use testnet/low limits
ULTRA_ARBITRAGE_MAX_POSITION=100
HUNTER_MAX_POSITION_SIZE=10
```

### **Scenario 2: Staging Environment**
```bash
# .env.staging

# Enable selectively
PORTFOLIO_ENABLED=true              # Safe, read-only
AAVE_DATA_ENABLED=true              # Safe, read-only
DEFI_TOOLS_ENABLED=true             # Safe, educational

# Trading bots still OFF
ULTRA_ARBITRAGE_ENABLED=false
HUNTER_ENABLED=false
```

### **Scenario 3: Production (Conservative)**
```bash
# .env.prod

# Only enable proven, safe features
AGENT_SQUAD_ENABLED=true
AGNO_ENABLED=true
GRAPHRAG_ENABLED=true
PORTFOLIO_ENABLED=true
AAVE_DATA_ENABLED=true

# Trading bots OFF until fully tested
ULTRA_ARBITRAGE_ENABLED=false
HUNTER_ENABLED=false
```

### **Scenario 4: Production (Full Features)**
```bash
# .env.prod (after validation)

# Enable all libraries
ULTRA_ARBITRAGE_ENABLED=true
HUNTER_ENABLED=true
PORTFOLIO_ENABLED=true
AAVE_DATA_ENABLED=true
DEFI_TOOLS_ENABLED=true
YIELD_CALC_ENABLED=true

# But keep strict safety limits
ULTRA_ARBITRAGE_AUTO_EXEC=false         # Manual approval
ULTRA_ARBITRAGE_MAX_POSITION=100000     # $100k max
ULTRA_ARBITRAGE_MAX_DAILY_LOSS=5000     # $5k max loss

HUNTER_AUTO_TRADING=false               # Manual trading
HUNTER_MAX_POSITION_SIZE=1000           # $1k max
HUNTER_MAX_DAILY_LOSS=500               # $500 max loss
```

---

## 🎯 **GRADUAL ROLLOUT STRATEGY**

### **Phase 1: Enable Read-Only Features** (Week 1)
```bash
PORTFOLIO_ENABLED=true
AAVE_DATA_ENABLED=true
DEFI_TOOLS_ENABLED=true
YIELD_CALC_ENABLED=true
```
**Risk:** Low (no trading, no capital at risk)

### **Phase 2: Enable AI Analysis** (Week 2-4)
```bash
HUNTER_ENABLED=true
HUNTER_AI_ANALYSIS=true
HUNTER_TOKEN_SCANNER=true

# But trading OFF
HUNTER_AUTO_TRADING=false
```
**Risk:** Low (analysis only, no execution)

### **Phase 3: Enable Manual Trading** (Week 5-8)
```bash
HUNTER_AUTO_TRADING=false               # Still manual
ULTRA_ARBITRAGE_ENABLED=true
ULTRA_ARBITRAGE_AUTO_EXEC=false         # Still manual

# Low position limits
HUNTER_MAX_POSITION_SIZE=100            # $100 only
ULTRA_ARBITRAGE_MAX_POSITION=1000       # $1k only
```
**Risk:** Medium (manual approval gates)

### **Phase 4: Enable Auto-Trading** (Week 9+)
```bash
HUNTER_AUTO_TRADING=true
ULTRA_ARBITRAGE_AUTO_EXEC=true

# Gradual limit increases
HUNTER_MAX_POSITION_SIZE=1000           # $1k
ULTRA_ARBITRAGE_MAX_POSITION=10000      # $10k

# Monitor closely, increase limits based on performance
```
**Risk:** High (automated execution, requires close monitoring)

---

## 📊 **MONITORING & ALERTS**

### **Critical Alerts (Trading Bots):**
```bash
# Send alerts when:
- Daily loss exceeds 50% of limit
- Unusual number of failed trades
- Position size approaching limit
- Flash loan failures
- MEV attacks detected
```

### **Performance Monitoring:**
```bash
# Track metrics:
- Trades executed per day
- Win rate %
- Average profit per trade
- Gas efficiency
- Flash loan success rate
- MEV protection effectiveness
```

---

## 🔄 **CONFIGURATION MANAGEMENT**

### **Code:**
```python
# src/app/setup/config/libs.py

from dataclasses import dataclass
import os

@dataclass
class LibraryFeaturesConfig:
    """Master configuration for all library integrations"""
    
    # TIER 1: CRITICAL
    ultra_arbitrage_enabled: bool = False
    hunter_enabled: bool = False
    
    # TIER 2: VALUE-ADD
    portfolio_tracker_enabled: bool = False
    aave_data_enabled: bool = False
    
    # TIER 3: EDUCATIONAL
    defi_tools_enabled: bool = False
    yield_calculator_enabled: bool = False
    
    # Already Implemented
    agent_squad_enabled: bool = True
    agno_enabled: bool = True
    graphrag_enabled: bool = True
    mcp_enabled: bool = True


def load_library_features() -> LibraryFeaturesConfig:
    """Load library feature flags from environment"""
    return LibraryFeaturesConfig(
        # TIER 1
        ultra_arbitrage_enabled=os.getenv("ULTRA_ARBITRAGE_ENABLED", "false").lower() == "true",
        hunter_enabled=os.getenv("HUNTER_ENABLED", "false").lower() == "true",
        
        # TIER 2
        portfolio_tracker_enabled=os.getenv("PORTFOLIO_ENABLED", "false").lower() == "true",
        aave_data_enabled=os.getenv("AAVE_DATA_ENABLED", "false").lower() == "true",
        
        # TIER 3
        defi_tools_enabled=os.getenv("DEFI_TOOLS_ENABLED", "false").lower() == "true",
        yield_calculator_enabled=os.getenv("YIELD_CALC_ENABLED", "false").lower() == "true",
        
        # Already Implemented
        agent_squad_enabled=os.getenv("AGENT_SQUAD_ENABLED", "true").lower() == "true",
        agno_enabled=os.getenv("AGNO_ENABLED", "true").lower() == "true",
        graphrag_enabled=os.getenv("GRAPHRAG_ENABLED", "true").lower() == "true",
        mcp_enabled=os.getenv("MCP_ENABLED", "true").lower() == "true",
    )
```

### **Usage in Code:**
```python
# Check if feature is enabled before using
from app.setup.config.libs import load_library_features

config = load_library_features()

if config.hunter_enabled:
    # Use Hunter features
    from app.infrastructure.hunter import HunterService
    hunter = HunterService()
    analysis = await hunter.analyze_token(token_address)
else:
    # Fallback to basic analysis
    analysis = await basic_token_analysis(token_address)
```

---

## 📚 **DOCUMENTATION**

**Main Documents:**
- `docs/LIBS_COMPLETE_INTEGRATION_PLAN.md` - Complete integration plan
- `docs/FEATURE_FLAGS_REFERENCE.md` - This document
- Individual specs in `libs/{library}_spec/README.md`

**Per-Library Documentation:**
- `libs/Hunter_spec/README.md`
- `libs/ULTRA-PRODUCTION-DEFI-ARBITRAGE-BOT_spec/README.md`
- `libs/aave-v3-data_spec/README.md`
- `libs/crypto_tracker_spec/README.md`
- `libs/defi_spec/README.md`
- `libs/defi-yield-calculator_spec/README.md`

---

## ✅ **BEST PRACTICES**

1. **Start Disabled:** All new features default to `false`
2. **Enable Gradually:** Test in dev → staging → production
3. **Monitor Closely:** Track metrics for enabled features
4. **Rollback Ready:** Can disable instantly if issues arise
5. **Document Changes:** Log all feature flag changes
6. **Security First:** Trading features require extra validation
7. **User Tier Gating:** Premium features check subscription level

---

**Last Updated:** December 2, 2025  
**Status:** ✅ Complete Reference Guide
