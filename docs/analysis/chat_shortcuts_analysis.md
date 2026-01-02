# Chat Shortcuts Feature Analysis (Updated with CEO Requirements)

## CTO Methodology Applied

### 1. Requirements from CEO

The CEO clarified the following shortcuts for the unified chat:

---

### 0. L2 Support Analysis (Arbitrum / Base)

**Question**: Can we add Arbitrum/Base RPC L2 execution for swaps and earn?

#### ✅ **YES - L2 Support Already Exists!**

| Protocol | Ethereum | Arbitrum | Base | Polygon | Optimism |
|----------|----------|----------|------|---------|----------|
| **Aave V3** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **1inch** | ✅ | ✅ (42161) | ✅ (8453) | ✅ | ✅ |
| **Morpho** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Hyperliquid** | - | - | - | - | - (native L1) |

#### Aave L2 Implementation (in code):

```python
# src/app/infrastructure/adapters/external/aave_client.py

AAVE_V3_POOLS = {
    "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # ✅
    "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",      # ✅
}

CHAIN_RPC_ENDPOINTS = {
    "ethereum": "https://eth.llamarpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",  # ✅
    "base": "https://mainnet.base.org",          # ✅
    ...
}
```

#### 1inch L2 Implementation (in code):

```python
# src/app/infrastructure/adapters/external/oneinch_client.py

class OneInchClient:
    CHAINS = {
        "ethereum": 1,
        "bsc": 56,
        "polygon": 137,
        "optimism": 10,
        "arbitrum": 42161,    # ✅
        "base": 8453,         # ✅
        "gnosis": 100,
        "avalanche": 43114,
        "fantom": 250,
    }
```

#### ChainType Enum (in code):

```python
# src/app/domain/enums/chain_type.py

class ChainType(Enum):
    ARBITRUM = "arbitrum"   # ✅
    BASE = "base"           # ✅
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    OPTIMISM = "optimism"
    HYPERLIQUID = "hyperliquid"
```

#### Morpho L2 Status:

Morpho currently only supports **Ethereum mainnet** via their subgraph:
```python
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/morpho-association/morpho-blue-mainnet"
```

**Note**: Morpho has announced Base deployment but is not yet live in the API.

#### Recommendation for L2 in Chat Shortcuts:

1. **Money Market (Aave)**: Add `chain` parameter - user can say "earn on Base" or "Aave rates on Arbitrum"
2. **Swap (1inch)**: Add `chain` parameter - user can say "swap on Arbitrum" for lower gas
3. **Lending (Morpho)**: Ethereum only for now (no L2 subgraph available)
4. **Portfolio/Balance**: Already supports multi-chain via wallet aggregation

| Shortcut | Description | Protocols/Sources |
|----------|-------------|-------------------|
| **Money Market** | Compare lending rates | Aave ✅, Compound 🔧, Spark ❌ |
| **Lending** | Yield vaults | Morpho ✅ |
| **Swap** | Token exchange | Hyperliquid ✅, 1inch ✅, UniswapX ❌ |
| **Receive** | Show address | QR code + Handle + Copy button |
| **Portfolio** | Full portfolio details | All tokens, positions, values |
| **Balance** | Simple USDC value only | Total value in USDC |
| **Activity** | Transaction history | Recent transactions |

---

### 2. Current Implementation Status

#### ✅ READY TO USE (Existing APIs)

| Feature | Implementation | API Endpoint |
|---------|----------------|--------------|
| **Aave (Money Market)** | `AaveGateway` | `GET /aave/markets`, `GET /aave/rates/{asset}` |
| **Morpho (Lending)** | `MorphoGateway` | `GET /morpho/vaults`, `GET /morpho/compare` |
| **1inch (Swap)** | `OneInchClient` | Swap quotes via `get_quote()` |
| **Hyperliquid (Swap)** | `HyperliquidGateway` | `GET /hyperliquid/markets` |
| **Portfolio** | `PortfolioService` | `GET /user/portfolio/me` |
| **Transactions** | `TransactionHandler` | `GET /user/transactions` |
| **Wallets** | `WalletRepository` | `GET /wallet/me` |

#### 🔧 NEEDS INTEGRATION (Agent exists, needs API)

| Feature | Status | Notes |
|---------|--------|-------|
| **Compound** | Agent exists (`compound_advisor.py`) | Need Compound V3 API integration |

#### ❌ NOT IMPLEMENTED (Needs new development)

| Feature | Status | Notes |
|---------|--------|-------|
| **Spark (Sky/MakerDAO Savings)** | Not implemented | Need Spark Protocol API |
| **UniswapX** | Not implemented | Different from Uniswap V3 |

---

### 3. Proposed Intent Structure

```python
class ChatIntent(Enum):
    # ... existing intents ...
    
    # New Wallet Shortcuts
    SHORTCUT_MONEY_MARKET = "shortcut_money_market"  # Compare Aave/Compound/Spark
    SHORTCUT_LENDING = "shortcut_lending"            # Morpho vaults
    SHORTCUT_SWAP = "shortcut_swap"                  # Compare swap routes
    SHORTCUT_SEND = "shortcut_send"                  # Send tokens preview
    SHORTCUT_RECEIVE = "shortcut_receive"            # QR + Handle + Address
    SHORTCUT_PORTFOLIO = "shortcut_portfolio"        # Full portfolio details
    SHORTCUT_BALANCE = "shortcut_balance"            # USDC value only
    SHORTCUT_ACTIVITY = "shortcut_activity"          # Transaction history
```

---

### 4. Detailed Implementation Plan

#### 4.1 `SHORTCUT_MONEY_MARKET` - Compare Lending Rates

**Keywords**: "money market", "earn interest", "supply rates", "lending rates", "compare aave compound", "where to lend"

**What it does**:
1. Fetch supply APY from Aave via `AaveGateway`
2. (Future) Fetch from Compound and Spark
3. Compare and show best rates

**Example Response**:
```
💰 **Money Market Rates Comparison**

**USDC Supply Rates:**
• Aave V3 (Ethereum): 4.52% APY ⭐ Best
• Compound V3: 3.89% APY
• Spark: 4.12% APY

**ETH Supply Rates:**
• Aave V3: 2.15% APY
• Compound V3: 1.92% APY ⭐ Best
• Spark: 2.08% APY

💡 Higher rates = higher utilization = more risk
```

**Dependencies**: `AaveGateway` ✅

---

#### 4.2 `SHORTCUT_LENDING` - Morpho Vaults

**Keywords**: "lending", "morpho", "vaults", "yield vaults", "best yields"

**What it does**:
1. Fetch Morpho vaults via `GetVaults` query
2. Show top vaults by APY with risk tier

**Example Response**:
```
🏦 **Morpho Lending Vaults**

**Top Opportunities:**
1. Steakhouse USDC (12.4% APY) - Low Risk
2. Gauntlet ETH (8.2% APY) - Medium Risk
3. Re7 wstETH (15.1% APY) - High Risk

**Your Positions:** None

💡 Use "deposit 1000 USDC in Steakhouse" to start earning
```

**Dependencies**: `GetVaults`, `GetUserPositions` ✅

---

#### 4.3 `SHORTCUT_SWAP` - Compare Swap Routes

**Keywords**: "swap", "exchange", "convert", "trade", "buy", "sell"

**What it does**:
1. Parse tokens and amount from message
2. Get quotes from 1inch and Hyperliquid
3. (Future) Add UniswapX comparison
4. Return best route with gas estimate

**Example Response**:
```
🔄 **Swap 1 ETH → USDC**

**Best Routes:**
1. 1inch: 3,450.25 USDC (0.1% slippage) ⭐
   Gas: ~$2.50 | Route: ETH → WETH → USDC

2. Hyperliquid: 3,448.00 USDC
   Gas: ~$1.20 | Route: Perp conversion

**Rate:** 1 ETH = $3,450.25
**Price Impact:** 0.02%

💡 Reply "execute" to proceed via 1inch
```

**Dependencies**: `OneInchClient` ✅, `HyperliquidGateway` ✅

---

#### 4.4 `SHORTCUT_RECEIVE` - Address with QR

**Keywords**: "receive", "my address", "deposit address", "show qr", "qr code", "wallet address"

**What it does**:
1. Get user's primary wallet from `WalletRepository`
2. Return address with:
   - Full address (copyable)
   - Handle/ENS if available
   - QR code data (for frontend to render)

**Example Response**:
```
📥 **Receive Crypto**

**Your Address:**
`0x1234567890abcdef1234567890abcdef12345678`

**Handle:** @mati.eth

**QR Code:** [Rendered on frontend]

**Supported Networks:**
• Ethereum ✅
• Base ✅
• Arbitrum ✅

💡 Only send compatible tokens to this address
```

**Response Enrichment**:
```json
{
  "enrichment": {
    "wallet_address": "0x...",
    "handle": "@mati.eth",
    "qr_data": "ethereum:0x...",
    "chains": ["ethereum", "base", "arbitrum"],
    "is_copyable": true
  }
}
```

**Dependencies**: `WalletRepository` ✅

---

#### 4.5 `SHORTCUT_PORTFOLIO` - Full Portfolio

**Keywords**: "portfolio", "my tokens", "all holdings", "show portfolio", "assets"

**What it does**:
1. Fetch full portfolio via `PortfolioService`
2. List all tokens with amounts and USD values
3. Show allocation percentages

**Example Response**:
```
📊 **Your Portfolio**

**Total Value:** $15,234.50

**Holdings:**
| Token | Amount | Value | % |
|-------|--------|-------|---|
| ETH   | 2.5    | $8,625 | 56.6% |
| USDC  | 5,000  | $5,000 | 32.8% |
| AAVE  | 10     | $1,609 | 10.6% |

**24h Change:** +$234.50 (+1.56%) 📈

💡 Use "swap" to rebalance your portfolio
```

**Dependencies**: `PortfolioService` ✅

---

#### 4.6 `SHORTCUT_BALANCE` - USDC Value Only

**Keywords**: "balance", "how much", "total value", "net worth"

**What it does**:
1. Fetch portfolio via `PortfolioService`
2. Return only total USD value

**Example Response**:
```
💵 **Your Balance**

**$15,234.50** USDC equivalent

📊 For full breakdown, say "portfolio"
```

**Dependencies**: `PortfolioService` ✅

---

#### 4.7 `SHORTCUT_ACTIVITY` - Transaction History

**Keywords**: "activity", "transactions", "history", "recent trades", "past transactions"

**What it does**:
1. Fetch transactions via `GetTransactionHistoryHandler`
2. Show last 10 with type, amount, status

**Example Response**:
```
📜 **Recent Activity**

| Time | Type | Amount | Status |
|------|------|--------|--------|
| 2h ago | Swap | 1 ETH → 3,450 USDC | ✅ |
| 1d ago | Send | 500 USDC → 0x8a... | ✅ |
| 2d ago | Receive | 2 ETH from 0x4b... | ✅ |

**Total:** 42 transactions

💡 Say "send" or "swap" to start a new transaction
```

**Dependencies**: `GetTransactionHistoryHandler` ✅

---

### 5. Implementation Priority

| Priority | Shortcut | Effort | Status |
|----------|----------|--------|--------|
| 1 | Balance | Low | Can implement now |
| 2 | Portfolio | Low | Can implement now |
| 3 | Activity | Low | Can implement now |
| 4 | Receive | Low | Can implement now |
| 5 | Money Market (Aave only) | Low | Can implement now |
| 6 | Lending (Morpho) | Low | Can implement now |
| 7 | Swap (1inch + Hyperliquid) | Medium | Can implement now |
| 8 | Money Market (+ Compound) | Medium | Need Compound API |
| 9 | Send (preview) | Medium | Need gas estimation |
| 10 | Money Market (+ Spark) | High | Need Spark API |
| 11 | Swap (+ UniswapX) | High | Need UniswapX API |

---

### 6. Files to Modify

1. **`src/app/application/chat/services/intent_detector.py`**
   - Add 8 new `ChatIntent` enum values

2. **`src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py`**
   - Add keyword patterns for each shortcut

3. **`src/app/infrastructure/adapters/chat/llm_intent_detection_adapter.py`**
   - Update LLM prompt with new intents

4. **`src/app/application/chat/commands/send_message_unified.py`**
   - Add 8 `_handle_shortcut_*` methods

5. **`src/app/setup/ioc/chat_phase2.py`**
   - Wire new dependencies

---

### 7. Summary

**CAN IMPLEMENT NOW (Phase 1):**
- ✅ Balance (USDC value)
- ✅ Portfolio (full details)
- ✅ Activity (transaction history)
- ✅ Receive (QR + Handle + Address)
- ✅ Money Market (Aave only)
- ✅ Lending (Morpho)
- ✅ Swap (1inch + Hyperliquid)

**NEEDS MORE WORK (Phase 2):**
- 🔧 Compound API integration
- 🔧 Send preview with gas estimation

**FUTURE (Phase 3):**
- ❌ Spark Protocol integration
- ❌ UniswapX integration

---

### 8. Recommendation

**Start with Phase 1** - We can implement 7 shortcuts immediately using existing infrastructure. This gives users the core functionality while we work on Compound and UniswapX integrations.

**Shall I proceed with implementation?**
