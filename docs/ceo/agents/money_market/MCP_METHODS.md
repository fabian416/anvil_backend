# Money Market MCP Methods Reference

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Complete Method Catalog

---

## Table of Contents

1. [Aave V3 MCP Server Methods](#aave-v3-mcp-server-methods)
2. [Compound V3 Client Methods](#compound-v3-client-methods)
3. [Comparison Matrix](#comparison-matrix)
4. [Method Selection Guide](#method-selection-guide)

---

## Aave V3 MCP Server Methods

**Server Name**: `aave`
**Port**: 8085
**Version**: 1.0.0
**Base URL**: `http://localhost:8085`

### Overview

The Aave MCP server provides **9 comprehensive tools** for interacting with Aave V3 lending protocol across 6 chains. All methods use real-time on-chain data via RPC calls and include built-in safety validations.

---

### Method 1: `get_market_data`

**Purpose**: Fetch current lending/borrowing rates and liquidity for specified assets

**Use Cases**:
- 📊 Display current APYs to users
- 🤖 AI agents comparing rates across protocols
- 📈 Market analysis and trend monitoring
- 🔔 Rate change alerts

**Parameters**:
```json
{
  "chain_id": 1,              // 1=Ethereum, 137=Polygon, 42161=Arbitrum, 10=Optimism, 43114=Avalanche
  "assets": ["USDC", "ETH"]   // Optional: filter by assets, omit for all markets
}
```

**Response**:
```json
{
  "success": true,
  "chain_id": 1,
  "chain_name": "ethereum",
  "pool_address": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  "markets_count": 2,
  "markets": [
    {
      "asset": "USDC",
      "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "name": "USD Coin",
      "supply_apy": 4.52,           // Annual percentage yield for suppliers
      "borrow_apy_variable": 5.18,  // Variable borrow rate
      "borrow_apy_stable": 6.50,    // Stable borrow rate
      "total_supplied": "1250000000",     // Total supplied (in USDC)
      "total_supplied_usd": "1250000000", // Total supplied in USD
      "total_borrowed": "850000000",      // Total borrowed
      "total_borrowed_usd": "850000000",
      "utilization_rate": 0.68,     // 68% utilization
      "available_liquidity": "400000000",
      "ltv": 0.80,                  // 80% loan-to-value
      "liquidation_threshold": 0.85, // 85% liquidation threshold
      "liquidation_bonus": 0.05,    // 5% liquidation bonus
      "can_be_collateral": true,
      "can_be_borrowed": true,
      "is_frozen": false,
      "is_active": true,
      "price_usd": "1.00",
      "decimals": 6,
      "timestamp": "2026-01-27T10:30:00Z"
    }
  ]
}
```

**Agent Workflow Example**:
```python
# Hunter AI scanning for best lending opportunities
markets = await aave_mcp.call_tool("get_market_data", {
    "chain_id": 1,
    "assets": ["USDC", "USDT", "DAI"]
})

# Find highest supply APY
best_market = max(markets["markets"], key=lambda m: m["supply_apy"])
print(f"Best rate: {best_market['asset']} at {best_market['supply_apy']}%")
```

**Safety Features**:
- ✅ Returns only active, non-frozen markets
- ✅ Real-time on-chain data (no stale cache)
- ✅ Asset availability flags (can_be_collateral, can_be_borrowed)

**Performance**:
- Latency: ~500-800ms for 3-5 assets
- Caching: 60s recommended in adapter layer
- Rate Limit: Depends on RPC provider

---

### Method 2: `get_user_positions`

**Purpose**: Get comprehensive view of user's Aave position including supplies, borrows, and health factor

**Use Cases**:
- 👤 Display user's lending dashboard
- 🤖 AI agents assessing borrowing capacity
- ⚠️ Risk monitoring and liquidation alerts
- 📊 Portfolio tracking and analytics

**Parameters**:
```json
{
  "chain_id": 1,
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response (User with Position)**:
```json
{
  "success": true,
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "chain_id": 1,
  "chain_name": "ethereum",
  "has_position": true,
  "supplied": [
    {
      "asset": "USDC",
      "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "amount": "50000.00",        // 50,000 USDC supplied
      "amount_usd": "50000.00",
      "apy": 4.52,                 // Earning 4.52% APY
      "is_collateral": true        // Used as collateral
    },
    {
      "asset": "ETH",
      "asset_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "amount": "10.5",            // 10.5 ETH supplied
      "amount_usd": "23625.00",    // @ $2,250/ETH
      "apy": 2.15,
      "is_collateral": true
    }
  ],
  "borrowed": [
    {
      "asset": "USDT",
      "asset_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
      "amount": "30000.00",        // Borrowed 30,000 USDT
      "amount_usd": "30000.00",
      "apy": 5.18,                 // Paying 5.18% interest
      "rate_mode": "variable"      // Variable rate loan
    }
  ],
  "total_supplied_usd": "73625.00",     // Total collateral value
  "total_borrowed_usd": "30000.00",     // Total debt
  "total_collateral_usd": "73625.00",   // Collateral used
  "available_borrow_usd": "25900.00",   // Can borrow up to this amount more
  "health_factor": "2.08",              // Healthy position (> 1.0)
  "current_ltv": 40.75,                 // 40.75% LTV
  "max_ltv": 80.00,                     // Can go up to 80% LTV
  "net_worth_usd": "43625.00",          // Collateral - Debt
  "timestamp": "2026-01-27T10:30:00Z"
}
```

**Response (User with No Position)**:
```json
{
  "success": true,
  "user_address": "0x...",
  "chain_id": 1,
  "has_position": false,
  "supplied": [],
  "borrowed": [],
  "total_supplied_usd": "0",
  "total_borrowed_usd": "0",
  "health_factor": "inf",
  "net_worth_usd": "0"
}
```

**Agent Workflow Example**:
```python
# Risk Analyzer checking user position health
position = await aave_mcp.call_tool("get_user_positions", {
    "chain_id": 1,
    "user_address": user_wallet
})

health_factor = float(position["health_factor"])

if health_factor < 1.5:
    # Alert user: approaching liquidation risk
    send_alert("⚠️ Your health factor is low. Consider adding collateral.")
elif health_factor < 1.0:
    # CRITICAL: can be liquidated
    send_alert("🚨 URGENT: Position at risk of liquidation!")
```

**Safety Features**:
- ✅ Real-time health factor calculation
- ✅ Shows which assets are used as collateral
- ✅ Differentiates variable vs stable rate borrows

---

### Method 3: `calculate_health_factor`

**Purpose**: Calculate detailed health factor with risk analysis and recommendations

**Use Cases**:
- 🔴 Liquidation risk monitoring
- 🤖 AI agents validating borrow safety
- 📊 Risk dashboard displays
- 🔔 Health factor alerts

**Parameters**:
```json
{
  "chain_id": 1,
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response**:
```json
{
  "success": true,
  "chain_id": 1,
  "chain_name": "ethereum",
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "health_factor": "2.08",                        // HF = (Collateral * LiqThreshold) / Debt
  "risk_level": "low",                            // low, moderate, high, critical
  "risk_color": "green",                          // green, yellow, orange, red
  "total_collateral_usd": "73625.00",
  "total_debt_usd": "30000.00",
  "liquidation_threshold": 0.85,                  // 85%
  "distance_to_liquidation": "1.08",              // HF - 1.0 = safety buffer
  "price_drop_before_liquidation": "51.92%",      // Collateral can drop 51.92% before liquidation
  "is_liquidatable": false,
  "recommendation": "Healthy position. Consider borrowing more if needed."
}
```

**Risk Level Classification**:
```
HF >= 2.0  → low      (green)  : Very safe
HF >= 1.5  → moderate (yellow) : Good, monitor
HF >= 1.2  → high     (orange) : Monitor closely
HF >= 1.0  → critical (red)    : URGENT action needed
HF < 1.0   → LIQUIDATABLE      : Can be liquidated NOW
```

**Agent Workflow Example**:
```python
# Before allowing user to borrow more
hf_data = await aave_mcp.call_tool("calculate_health_factor", {
    "chain_id": 1,
    "user_address": user_wallet
})

if hf_data["risk_level"] in ["high", "critical"]:
    return {
        "action": "blocked",
        "reason": f"Your health factor is {hf_data['health_factor']} ({hf_data['risk_level']} risk)",
        "recommendation": hf_data["recommendation"]
    }
```

**Safety Features**:
- ✅ Price drop buffer calculation (useful for volatility assessment)
- ✅ Color-coded risk levels for UI
- ✅ Actionable recommendations based on HF
- ✅ Distance to liquidation metric

---

### Method 4: `get_available_to_borrow`

**Purpose**: Calculate maximum safe borrowing capacity for a specific asset

**Use Cases**:
- 💰 Show users how much they can borrow
- 🤖 AI agents planning leverage strategies
- 🔒 Pre-borrow validation
- 📊 Borrowing capacity dashboards

**Parameters**:
```json
{
  "chain_id": 1,
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "asset": "USDC",
  "target_health_factor": 1.5  // Optional, default 1.5 (recommended minimum)
}
```

**Response**:
```json
{
  "success": true,
  "chain_id": 1,
  "chain_name": "ethereum",
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "asset": "USDC",
  "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "max_borrow_amount": "25900.00",              // Can borrow up to 25,900 USDC
  "max_borrow_usd": "25900.00",
  "asset_price_usd": "1.00",
  "current_debt_usd": "30000.00",
  "total_collateral_usd": "73625.00",
  "current_health_factor": "2.08",
  "estimated_health_factor_after": "1.52",      // HF after borrowing max amount
  "target_health_factor": 1.5,
  "available_liquidity": "400000000",           // Protocol has liquidity
  "warning": "Always maintain health factor above 1.5 for safety. Market volatility can cause liquidation."
}
```

**Agent Workflow Example**:
```python
# Calculate safe borrow amount for leverage loop
available = await aave_mcp.call_tool("get_available_to_borrow", {
    "chain_id": 1,
    "user_address": user_wallet,
    "asset": "USDC",
    "target_health_factor": 1.8  # More conservative for leverage
})

max_safe_borrow = float(available["max_borrow_amount"])
print(f"Can safely borrow {max_safe_borrow} USDC while maintaining HF >= 1.8")
```

**Safety Features**:
- ✅ Considers current debt and collateral
- ✅ Respects target health factor threshold
- ✅ Checks protocol liquidity availability
- ✅ Shows estimated HF after borrowing

---

### Method 5: `supply_asset`

**Purpose**: Generate transaction to supply (deposit) assets to Aave to earn yield

**Use Cases**:
- 💵 Users depositing assets to earn APY
- 🤖 AI agents executing lending strategies
- 🔄 Auto-compounding yield optimizers
- 🔐 Transaction generation for wallet signing

**Parameters**:
```json
{
  "user_id": "user_123",                         // Required for wallet access
  "chain_id": 1,
  "asset": "USDC",
  "amount": "10000.00",                          // Human-readable amount
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "use_as_collateral": true                      // Optional, default true
}
```

**Response**:
```json
{
  "success": true,
  "action": "supply",
  "chain_id": 1,
  "chain_name": "ethereum",
  "asset": "USDC",
  "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "10000.00",
  "use_as_collateral": true,
  "from_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "transaction": {
    "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  // Aave V3 Pool
    "data": "0x617ba037...",                              // Encoded function call
    "value": "0x0",
    "gas_limit": "350000"
  },
  "requires_approval": true,                      // Must approve Pool to spend tokens first
  "approval_spender": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  "expected_apy": 4.52,                           // Will earn 4.52% APY
  "warning": "⚠️ Before signing this transaction, ensure you have:\n1. Approved the Pool contract to spend your tokens\n2. Sufficient balance of the asset\n3. Sufficient gas (ETH/MATIC) for transaction fees"
}
```

**Agent Workflow Example**:
```python
# Execution Agent generating supply transaction
supply_tx = await aave_mcp.call_tool("supply_asset", {
    "user_id": current_user.id,
    "chain_id": 1,
    "asset": "USDC",
    "amount": "10000",
    "from_address": user_wallet
})

# Step 1: User approves Pool to spend USDC
approval_tx = generate_erc20_approval(
    token=supply_tx["asset_address"],
    spender=supply_tx["approval_spender"],
    amount=supply_tx["amount"]
)

# Step 2: User signs and submits supply transaction
await wallet.sign_and_send(supply_tx["transaction"])
```

**Safety Features**:
- ✅ Checks if asset is active and not frozen
- ✅ Validates asset decimals for correct amount encoding
- ✅ Generates correct calldata for Pool contract
- ✅ Warns about approval requirement

---

### Method 6: `borrow_asset`

**Purpose**: Generate transaction to borrow assets against collateral (with safety validation)

**Use Cases**:
- 💸 Users borrowing against their deposits
- 🔄 Leverage loops (borrow → supply → repeat)
- 🤖 AI agents executing complex strategies
- 🛡️ Pre-validated safe borrows

**Parameters**:
```json
{
  "user_id": "user_123",
  "chain_id": 1,
  "asset": "USDC",
  "amount": "5000.00",
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "rate_mode": "variable"                        // "variable" or "stable"
}
```

**Response (Safe Borrow)**:
```json
{
  "success": true,
  "action": "borrow",
  "chain_id": 1,
  "chain_name": "ethereum",
  "asset": "USDC",
  "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "5000.00",
  "rate_mode": "variable",
  "from_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "transaction": {
    "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "data": "0xa415bcad...",
    "value": "0x0",
    "gas_limit": "400000"
  },
  "current_health_factor": "2.08",
  "estimated_health_factor_after": "1.75",      // Safe: HF still > 1.5
  "expected_borrow_apy": 5.18,
  "warning": "⚠️ BORROWING CREATES LIQUIDATION RISK\n• Your health factor will be: 1.75\n• Liquidation occurs if HF drops below 1.0\n• Monitor your position regularly\n• Consider repaying if HF drops below 1.5"
}
```

**Response (Unsafe Borrow - BLOCKED)**:
```json
{
  "success": false,
  "error": "UNSAFE BORROW BLOCKED",
  "reason": "This borrow would reduce your health factor to 1.15",
  "current_health_factor": "1.40",
  "estimated_health_factor_after": "1.15",
  "minimum_required": "1.20",
  "recommendation": "To borrow this amount safely:\n1. Supply more collateral, OR\n2. Borrow a smaller amount, OR\n3. Repay existing debt",
  "chain_id": 1
}
```

**Safety Threshold**:
- ⚠️ **Borrows are BLOCKED if estimated HF < 1.2**
- ✅ This prevents users from creating risky positions
- ✅ Protects against price volatility and liquidation

**Agent Workflow Example**:
```python
# Try to borrow, respecting safety checks
borrow_tx = await aave_mcp.call_tool("borrow_asset", {
    "user_id": current_user.id,
    "chain_id": 1,
    "asset": "USDC",
    "amount": "5000",
    "from_address": user_wallet,
    "rate_mode": "variable"
})

if not borrow_tx["success"]:
    # Borrow was blocked for safety
    return {
        "error": borrow_tx["error"],
        "recommendation": borrow_tx["recommendation"]
    }

# Safe to proceed
await wallet.sign_and_send(borrow_tx["transaction"])
```

---

### Method 7: `repay_loan`

**Purpose**: Generate transaction to repay borrowed assets

**Use Cases**:
- 💰 Users repaying debt to improve health factor
- 🤖 AI agents managing leverage positions
- 🔄 Automatic debt management
- ⚠️ Emergency liquidation prevention

**Parameters**:
```json
{
  "user_id": "user_123",
  "chain_id": 1,
  "asset": "USDC",
  "amount": "5000.00",                           // Or "max" for full repayment
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "rate_mode": "variable"
}
```

**Response**:
```json
{
  "success": true,
  "action": "repay",
  "chain_id": 1,
  "chain_name": "ethereum",
  "asset": "USDC",
  "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "5000.00",
  "rate_mode": "variable",
  "from_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "transaction": {
    "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "data": "0x573ade81...",
    "value": "0x0",
    "gas_limit": "350000"
  },
  "requires_approval": true,                      // Need to approve Pool to spend repayment tokens
  "approval_spender": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  "current_health_factor": "1.25",                // Low HF - good to repay!
  "estimated_health_factor_after": "1.60",        // Much healthier after repayment
  "health_factor_improvement": "Improved"
}
```

**Agent Workflow Example**:
```python
# Risk Analyzer detecting low health factor → trigger repayment
hf_data = await aave_mcp.call_tool("calculate_health_factor", {
    "chain_id": 1,
    "user_address": user_wallet
})

if float(hf_data["health_factor"]) < 1.3:
    # Repay 20% of debt to improve HF
    current_debt = float(position["total_borrowed_usd"])
    repay_amount = current_debt * 0.20

    repay_tx = await aave_mcp.call_tool("repay_loan", {
        "user_id": current_user.id,
        "chain_id": 1,
        "asset": "USDC",
        "amount": str(repay_amount),
        "from_address": user_wallet,
        "rate_mode": "variable"
    })

    # Execute repayment
    await wallet.sign_and_send(repay_tx["transaction"])
```

---

### Method 8: `withdraw_supply`

**Purpose**: Generate transaction to withdraw supplied assets (with safety validation)

**Use Cases**:
- 💸 Users withdrawing deposits
- 🤖 AI agents rebalancing portfolios
- 🔄 Moving funds between protocols
- 🛡️ Safe withdrawals that protect health factor

**Parameters**:
```json
{
  "user_id": "user_123",
  "chain_id": 1,
  "asset": "USDC",
  "amount": "5000.00",                           // Or "max" for full withdrawal
  "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response (Safe Withdrawal)**:
```json
{
  "success": true,
  "action": "withdraw",
  "chain_id": 1,
  "chain_name": "ethereum",
  "asset": "USDC",
  "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "5000.00",
  "from_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "transaction": {
    "to": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "data": "0x69328dec...",
    "value": "0x0",
    "gas_limit": "350000"
  },
  "current_health_factor": "2.50",
  "estimated_health_factor_after": "2.10"        // Still healthy
}
```

**Response (Unsafe Withdrawal - BLOCKED)**:
```json
{
  "success": false,
  "error": "UNSAFE WITHDRAWAL BLOCKED",
  "reason": "This withdrawal would reduce your health factor to 1.45",
  "current_health_factor": "1.80",
  "estimated_health_factor_after": "1.45",
  "minimum_required": "1.50",
  "recommendation": "Repay some debt before withdrawing, or withdraw a smaller amount",
  "chain_id": 1
}
```

**Safety Threshold**:
- ⚠️ **Withdrawals are BLOCKED if estimated HF < 1.5**
- ✅ More conservative than borrow threshold (1.2)
- ✅ Cannot withdraw collateral if any debt exists ("max" withdrawal blocked)

---

### Method 9: `get_liquidation_risk`

**Purpose**: Comprehensive liquidation risk analysis with per-asset breakdown

**Use Cases**:
- 🔴 Detailed risk monitoring dashboards
- 🤖 AI agents for proactive risk management
- 📊 Liquidation price calculations
- 🔔 Multi-level alert systems

**Parameters**:
```json
{
  "chain_id": 1,
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response**:
```json
{
  "success": true,
  "chain_id": 1,
  "chain_name": "ethereum",
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "has_position": true,
  "risk_level": "moderate",                      // low, moderate, high, critical
  "risk_description": "Moderate risk. Monitor market conditions.",
  "health_factor": "1.75",
  "distance_to_liquidation": "0.75",
  "price_drop_before_liquidation": "42.86%",     // Collateral can drop 42.86%
  "total_collateral_usd": "73625.00",
  "total_debt_usd": "30000.00",
  "liquidation_scenarios": [                     // Per-asset liquidation prices
    {
      "collateral_asset": "USDC",
      "collateral_amount": "50000.00",
      "collateral_usd": "50000.00",
      "current_price_usd": "1.00",
      "liquidation_price_usd": "0.71",           // USDC would need to drop to $0.71
      "price_drop_percentage": "29.00%",
      "liquidation_threshold": 0.85
    },
    {
      "collateral_asset": "ETH",
      "collateral_amount": "10.5",
      "collateral_usd": "23625.00",
      "current_price_usd": "2250.00",
      "liquidation_price_usd": "1603.57",        // ETH would need to drop to $1,603.57
      "price_drop_percentage": "28.75%",
      "liquidation_threshold": 0.85
    }
  ],
  "recommendations": [
    "🔔 Set up price alerts for your collateral assets",
    "⚙️ Consider switching to stable rate if variable rates are rising"
  ]
}
```

**Agent Workflow Example**:
```python
# Risk Analyzer with tiered alert system
risk_data = await aave_mcp.call_tool("get_liquidation_risk", {
    "chain_id": 1,
    "user_address": user_wallet
})

# Analyze each collateral asset
for scenario in risk_data["liquidation_scenarios"]:
    price_buffer = float(scenario["price_drop_percentage"].rstrip("%"))

    if price_buffer < 15:
        # CRITICAL: very close to liquidation
        send_push_notification(
            f"🚨 URGENT: {scenario['collateral_asset']} can only drop {price_buffer:.1f}% before liquidation!"
        )
    elif price_buffer < 30:
        # WARNING: moderate buffer
        send_email_alert(
            f"⚠️ Warning: {scenario['collateral_asset']} liquidation price at ${scenario['liquidation_price_usd']}"
        )
```

**Key Features**:
- ✅ Per-asset liquidation price calculations
- ✅ Price drop buffer analysis
- ✅ Multi-asset position breakdown
- ✅ Actionable recommendations

---

## Compound V3 Client Methods

**Client Name**: `CompoundClient`
**Deployment**: Direct integration (no standalone MCP server)
**Protocol**: Compound V3 (Comet)

### Overview

Compound V3 client provides **4 core methods** for accessing Comet markets. Unlike Aave's full MCP server, Compound is accessed via direct Python client integration. Supports USDC and WETH markets across 4 chains.

---

### Method 1: `get_market`

**Purpose**: Fetch market data for a specific Compound V3 asset/chain combination

**Use Cases**:
- 📊 Compare rates with Aave
- 🤖 AI agents finding best yields
- 📈 Market tracking and analysis

**Parameters**:
```python
asset: str = "USDC"          # USDC or WETH
chain: str = "ethereum"      # ethereum, base, arbitrum, polygon
```

**Response**:
```python
CompoundMarket(
    chain="ethereum",
    base_asset="USDC",
    comet_address="0xc3d688B66703497DAA19211EEdff47f25384cdc3",
    supply_apy=4.20,                   # 4.20% supply APY
    borrow_apy=5.50,                   # 5.50% borrow APY
    utilization=0.72,                  # 72% utilization
    total_supply=1500000000.0,         # 1.5B USDC supplied
    total_borrow=1080000000.0,         # 1.08B USDC borrowed
    supply_apy_base=4.20,              # Base APY (no rewards)
    supply_apy_reward=0.0,             # COMP rewards (TODO)
    borrow_apy_base=5.50,
    borrow_apy_reward=0.0
)
```

**Agent Workflow Example**:
```python
# Compare Compound vs Aave for USDC on Ethereum
compound_market = await compound_client.get_market("USDC", "ethereum")
aave_markets = await aave_mcp.call_tool("get_market_data", {
    "chain_id": 1,
    "assets": ["USDC"]
})

if compound_market.supply_apy > aave_markets["markets"][0]["supply_apy"]:
    print(f"Compound offers better rate: {compound_market.supply_apy}%")
```

---

### Method 2: `get_markets`

**Purpose**: Get all Compound V3 markets on a specific chain

**Parameters**:
```python
chain: str = "ethereum"
```

**Response**:
```python
[
    CompoundMarket(
        chain="ethereum",
        base_asset="USDC",
        comet_address="0xc3d688B66703497DAA19211EEdff47f25384cdc3",
        supply_apy=4.20,
        ...
    ),
    CompoundMarket(
        chain="ethereum",
        base_asset="WETH",
        comet_address="0xA17581A9E3356d9A858b789D68B4d866e593aE94",
        supply_apy=1.85,
        ...
    )
]
```

---

### Method 3: `get_user_position`

**Purpose**: Get user's position in a specific Compound V3 market

**Parameters**:
```python
user_address: str
asset: str = "USDC"
chain: str = "ethereum"
```

**Response**:
```python
CompoundPosition(
    chain="ethereum",
    base_asset="USDC",
    comet_address="0xc3d688B66703497DAA19211EEdff47f25384cdc3",
    user_address="0x742d35cc6634c0532925a3b844bc9e7595f0beb",
    supplied=25000.0,                    # 25,000 USDC supplied
    borrowed=10000.0,                    # 10,000 USDC borrowed
    collateral_usd=25000.0,
    health_factor=2.0,                   # Simplified calculation
    is_liquidatable=False
)
```

**Note**: Compound V3 has a simpler collateral model than Aave. Each Comet market has one base asset (USDC or WETH) that can be supplied/borrowed.

---

### Method 4: `get_all_markets`

**Purpose**: Get ALL Compound V3 markets across all supported chains

**Response**:
```python
[
    # Ethereum markets
    CompoundMarket(chain="ethereum", base_asset="USDC", ...),
    CompoundMarket(chain="ethereum", base_asset="WETH", ...),
    # Base markets
    CompoundMarket(chain="base", base_asset="USDC", ...),
    CompoundMarket(chain="base", base_asset="WETH", ...),
    # Arbitrum markets
    CompoundMarket(chain="arbitrum", base_asset="USDC", ...),
    CompoundMarket(chain="arbitrum", base_asset="WETH", ...),
    # Polygon markets
    CompoundMarket(chain="polygon", base_asset="USDC", ...)
]
```

**Use Case**: Cross-chain yield comparison

---

## Comparison Matrix

| Feature | Aave V3 MCP | Compound V3 Client |
|---------|-------------|-------------------|
| **Server Type** | Standalone MCP Server (Port 8085) | Direct Python Client |
| **Total Methods** | 9 comprehensive tools | 4 core methods |
| **Supported Chains** | 6 (Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Base) | 4 (Ethereum, Base, Arbitrum, Polygon) |
| **Supported Assets** | 10+ per chain (USDC, USDT, DAI, ETH, WETH, WBTC, etc.) | 2 per chain (USDC, WETH) |
| **Health Factor Calculation** | ✅ Real-time, detailed | ✅ Simplified |
| **Transaction Generation** | ✅ Supply, Borrow, Repay, Withdraw | ❌ Read-only |
| **Safety Validations** | ✅ Pre-transaction HF checks | ❌ No built-in validation |
| **Liquidation Analysis** | ✅ Per-asset breakdown | ❌ Not available |
| **Market Data Granularity** | High (LTV, liquidation threshold, utilization, etc.) | Medium (APY, utilization, supply/borrow) |
| **Position Tracking** | ✅ Multi-asset supplies/borrows | ✅ Single-asset per market |
| **Rate Types** | Variable + Stable | Variable only |
| **Multi-Language Support** | ✅ (via MoneyMarketHandler) | ✅ (via MoneyMarketHandler) |
| **Caching Strategy** | Adapter-layer (60s recommended) | In-memory (60s default) |
| **Performance** | 500-800ms per call | 300-600ms per call |

---

## Method Selection Guide

### For AI Agents

**Scenario**: Hunter AI scanning for best lending opportunities
- **Use**: `Aave: get_market_data` + `Compound: get_all_markets`
- **Why**: Compare rates across all protocols and chains

**Scenario**: Risk Analyzer monitoring user positions
- **Use**: `Aave: get_user_positions` + `calculate_health_factor` + `get_liquidation_risk`
- **Why**: Comprehensive risk analysis with actionable alerts

**Scenario**: Execution Agent creating supply transaction
- **Use**: `Aave: supply_asset`
- **Why**: Only Aave MCP generates transaction calldata

**Scenario**: Portfolio Manager rebalancing between protocols
- **Use**: `Aave: get_user_positions` + `Compound: get_user_position`
- **Why**: Compare positions to find optimization opportunities

### For User Dashboards

**Lending Rates Page**:
```python
# Compare all protocols
aave_markets = await aave_mcp.call_tool("get_market_data", {"chain_id": 1})
compound_markets = await compound_client.get_markets("ethereum")
morpho_vaults = await morpho_mcp.call_tool("get_vaults", {"chain_id": 1})

# Display side-by-side comparison
```

**My Positions Page**:
```python
# Get positions from all protocols
aave_position = await aave_mcp.call_tool("get_user_positions", {
    "chain_id": 1,
    "user_address": wallet
})

compound_position = await compound_client.get_user_position(
    user_address=wallet,
    asset="USDC",
    chain="ethereum"
)

# Aggregate net worth
```

**Risk Dashboard**:
```python
# Aave has the most detailed risk analysis
risk_data = await aave_mcp.call_tool("get_liquidation_risk", {
    "chain_id": 1,
    "user_address": wallet
})

# Show health factor, liquidation prices, recommendations
```

---

## Best Practices

### 1. Always Use Safety Validations

```python
# ❌ Bad: Directly borrowing without checks
borrow_tx = await aave_mcp.call_tool("borrow_asset", {...})

# ✅ Good: Check health factor first
hf_data = await aave_mcp.call_tool("calculate_health_factor", {...})
if float(hf_data["health_factor"]) < 1.5:
    return "Cannot borrow: health factor too low"

borrow_tx = await aave_mcp.call_tool("borrow_asset", {...})
```

### 2. Implement Caching

```python
# ✅ Cache market data for 60 seconds
@cache(ttl=60)
async def get_cached_markets(chain_id: int):
    return await aave_mcp.call_tool("get_market_data", {"chain_id": chain_id})
```

### 3. Handle Errors Gracefully

```python
# ✅ Always check success field
result = await aave_mcp.call_tool("get_market_data", {...})
if not result.get("success"):
    # Fall back to estimated rates
    return get_fallback_rates(asset, chain)
```

### 4. Monitor Rate Limits

```python
# ✅ Track RPC calls to avoid rate limits
if rpc_call_count > 100:
    await asyncio.sleep(1)  # Back off
```

---

## Integration Examples

See [USE_CASES.md](./USE_CASES.md) for complete workflow examples.

---

**Status**: ✅ Complete Method Reference | 🚀 Ready for Implementation
