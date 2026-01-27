Input:
Compare Aave vs Compound

Output:
📊 Money Market Comparison - USDC

Comparing Aave & Compound rates on ETHEREUM:

| Protocol | Supply APY | Borrow APY | |

|----------|-----------|------------|--------|

| Aave V3 🏆 | 4.50% | 5.20% | 🟢 |

| Compound V3 | 3.23% | 3.99% | 🟢 |

🟢 Real-time | 🟡 Estimated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Best Supply Rate: Aave V3 (4.50% APY)

🎯 Best Borrow Rate: Compound V3 (3.99% APY)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 For higher yields on stablecoins, try: "deposit USDC on Morpho"

👉 Sign up to execute this action → /signup

Input:
Best money market rates for USDC

Output:
📊 Money Market Comparison - USDC

Comparing Aave & Compound rates on ETHEREUM:

| Protocol | Supply APY | Borrow APY | |

|----------|-----------|------------|--------|

| Aave V3 🏆 | 4.50% | 5.20% | 🟢 |

| Compound V3 | 3.23% | 3.99% | 🟢 |

🟢 Real-time | 🟡 Estimated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Best Supply Rate: Aave V3 (4.50% APY)

🎯 Best Borrow Rate: Compound V3 (3.99% APY)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 For higher yields on stablecoins, try: "deposit USDC on Morpho"

👉 Sign up to execute this action → /signup

Input:
Compare lending rates for ETH

Output:
📊 Money Market Comparison - ETH

Comparing Aave & Compound rates on ETHEREUM:

| Protocol | Supply APY | Borrow APY | |

|----------|-----------|------------|--------|

| Aave V3 🏆 | 2.10% | 3.50% | 🟡 |

| Compound V3 | 1.80% | 3.20% | 🟡 |

🟢 Real-time | 🟡 Estimated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Best Supply Rate: Aave V3 (2.10% APY)

🎯 Best Borrow Rate: Compound V3 (3.20% APY)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 For higher yields on stablecoins, try: "deposit USDC on Morpho"

👉 Sign up to execute this action → /signup

---

## MONEY_MARKET vs LENDING Distinction

### When to Use MONEY_MARKET

**MONEY_MARKET shortcut is for Aave and Compound rate comparisons**

Use MONEY_MARKET when you want to:
- Compare Aave V3 vs Compound V3 lending/borrow rates
- Find best money market rates for specific assets (USDC, ETH, etc.)
- Get real-time on-chain rate data from traditional money markets

**Example Queries:**
- "Compare Aave vs Compound"
- "Best money market rates for USDC"
- "Compare lending rates for ETH"
- "Aave or Compound better for USDC?"

**Intent:** `MONEY_MARKET`
**Handler:** `MoneyMarketHandler`
**Data Sources:** Aave V3 MCP (9 methods), Compound V3 Client (4 methods)
**Chains:** Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Base

---

### When to Use LENDING

**LENDING shortcut is for Morpho vault operations and discovery**

Use LENDING when you want to:
- Discover best Morpho vaults by APY
- Compare Morpho vault yields
- Deposit/withdraw from specific Morpho vaults
- Get vault recommendations for specific assets

**Example Queries:**
- "Best lending vaults"
- "Best morpho vaults"
- "Show best vaults"
- "Compare vaults"
- "Deposit USDC on Morpho"
- "List morpho vaults"

**Intent:** `LENDING`
**Handler:** `LendingHandler`
**Data Sources:** Morpho MCP (vault rates, positions, transactions)
**Features:** Curated vaults, automated strategies, higher yields than traditional money markets

---

### Quick Decision Guide

| Your Goal | Use This | Example Query |
|-----------|----------|---------------|
| Compare Aave vs Compound | **MONEY_MARKET** | "Compare Aave vs Compound" |
| Find best vault yields | **LENDING** | "Best lending vaults" |
| Check money market rates | **MONEY_MARKET** | "Best money market rates for USDC" |
| Deposit on Morpho | **LENDING** | "Deposit USDC on Morpho" |
| Compare protocols | **MONEY_MARKET** | "Aave or Compound?" |
| Vault discovery | **LENDING** | "Show best vaults" |

**Pro Tip:** MONEY_MARKET often suggests trying Morpho for higher yields via the hint: _"For higher yields on stablecoins, try: 'deposit USDC on Morpho'"_

