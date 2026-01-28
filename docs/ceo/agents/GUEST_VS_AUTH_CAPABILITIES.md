# Guest vs Authenticated User Capabilities

**Date**: January 28, 2026
**Quick Reference**: What guests can do vs what requires signup

---

## 🎯 Quick Reference Table

| User Query | Guest Access | Auth Required | Routed To |
|------------|-------------|---------------|-----------|
| **Educational Queries** |
| "what is lending?" | ✅ Yes | No | `knowledge` |
| "how does money market work?" | ✅ Yes | No | `knowledge` |
| "can i lend usdc?" | ✅ Yes | No | `knowledge` |
| "explain Aave vs Compound" | ✅ Yes | No | `knowledge` |
| **Rate Information** |
| "compare usdc lending rates" | ✅ Yes | No | `hunter_ai` |
| "aave vs compound rates" | ✅ Yes | No | `hunter_ai` |
| "best usdc apy" | ✅ Yes | No | `hunter_ai` |
| "current lending rates on Base" | ✅ Yes | No | `hunter_ai` |
| **Deposit Actions** |
| "lend 100 usdc" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "deposit 100 usdc to aave" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "deposit to money market" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "execute the deposit" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| **Withdrawal Actions** |
| "withdraw from aave" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "withdraw my deposit" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| **Position Management** |
| "my deposits" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "my lending positions" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "check my balance" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| **Swap Actions** |
| "swap 100 usdc to eth" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |
| "execute the swap" | ❌ No | ✅ Yes | `guest_auth` → prompt signup |

---

## 📊 Capability Breakdown

### ✅ GUESTS CAN (No Login Required)

#### 1. Learn & Explore
- Educational content about DeFi, lending, swaps
- Protocol comparisons (Aave vs Compound)
- Feature explanations (how lending works)
- Risk and security information
- Multi-language support (en/es/pt)

#### 2. View Market Data
- Real-time crypto prices
- Lending APY rates across protocols
- Token swap rates
- Gas prices
- Market trends and analytics

#### 3. Ask "How To" Questions
- "how do i swap tokens?"
- "how to lend crypto?"
- "what is the process?"
- "how does it work?"

#### 4. Compare Options
- "aave vs compound rates"
- "best usdc apy"
- "compare lending rates"
- "which protocol is better?"

**Philosophy**: Maximum discovery, zero friction

---

### ❌ GUESTS CANNOT (Requires Signup)

#### 1. Execute Transactions
- Swap tokens
- Deposit to lending protocols
- Withdraw from protocols
- Send crypto to addresses
- Buy crypto with card

#### 2. View Personal Data
- Portfolio balance
- Transaction history
- Lending positions
- Wallet addresses
- Account settings

#### 3. Manage Positions
- Track active deposits
- Monitor lending positions
- View position history
- Receive rate alerts

**Philosophy**: Clear conversion path when action is needed

---

## 🔄 Conversion Flow Examples

### Example 1: Educational → Action → Signup

**User Journey**:
1. Guest: "what is lending?" → ✅ Knowledge agent explains
2. Guest: "compare usdc rates" → ✅ Hunter AI shows real rates
3. Guest: "deposit 100 usdc to aave" → ❌ Guest auth prompts signup
4. User signs up → ✅ Can now execute deposit

### Example 2: Direct Action Attempt

**User Journey**:
1. Guest: "lend 100 usdc" → ❌ Immediate signup prompt
2. Prompt shows: "You requested: Lend 100 USDC"
3. Prompt shows: "Create account to complete this"
4. Direct link to signup page

---

## 🎨 User Experience Design

### For Allowed Queries (Educational + Rates)

**Response Style**: Full, helpful information
```
📚 **DeFi Lending Explained**

Lending protocols let you earn APY by depositing crypto...

**Supported Protocols:**
- Aave V3: Multi-chain, variable rates
- Compound V3: USDC markets, efficient

Want to see current rates? Try: "compare usdc rates"
```

### For Blocked Actions (Transactions)

**Response Style**: Clear requirement + conversion prompt
```
❌ **Lending Requires an Account**

To deposit crypto and earn APY, create a free account.

**What you requested:**
Deposit 100 USDC to Aave V3 (3.45% APY)

**To complete this:**
1. Create your free account
2. Connect wallet (or create new)
3. Deposit and start earning

🚀 Get Started: https://app.anvil.fi/signup
Already have account? https://app.anvil.fi/login
```

---

## 🧠 Router Intelligence

### Guest Supervisor (`guest_supervisor.py`)

**Query Analysis**:
1. Detect if educational vs action request
2. Route educational → `knowledge` or `hunter_ai`
3. Route actions → `guest_auth` (conversion flow)

**Examples**:
```python
# Educational (ALLOWED)
"can i lend?" → knowledge agent
"how to lend?" → knowledge agent
"compare rates" → hunter_ai agent

# Action (BLOCKED)
"lend 100 usdc" → guest_auth (signup prompt)
"deposit to aave" → guest_auth (signup prompt)
"my deposits" → guest_auth (signup prompt)
```

### Authenticated Supervisor (`authenticated_supervisor.py`)

**Query Analysis**:
1. User is authenticated, has wallet
2. Educational queries → same as guest
3. Action queries → workflow agents (execution)

**Examples**:
```python
# Educational (same as guest)
"can i lend?" → knowledge agent
"compare rates" → hunter_ai agent

# Action (EXECUTE)
"lend 100 usdc" → lending_workflow agent (checks balance, executes)
"deposit to aave" → money_market_workflow agent (real execution)
"my deposits" → portfolio agent (shows real positions)
```

---

## 🌍 Multi-Language Support

All responses support:
- **English**: "can i lend?" / "deposit 100 usdc"
- **Spanish**: "puedo prestar?" / "depositar 100 usdc"
- **Portuguese**: "posso emprestar?" / "depositar 100 usdc"

Both educational and conversion prompts adapt to user language.

---

## 💡 Key Insights

### Why Allow Rate Data for Guests?

**Trust Building**:
- Shows real, transparent data
- Demonstrates platform value
- No commitment required
- Builds confidence before signup

**Conversion Optimization**:
- Guest sees rate: "4.12% APY on USDC"
- Guest wants that rate
- Guest tries to deposit
- Clear signup prompt appears
- Higher conversion rate

### Why Block Execution Actions?

**Security**:
- Transactions require authenticated wallet
- Cannot execute without private key control
- Guest mode has no wallet access

**User Safety**:
- Prevents accidental transactions
- Ensures user understands commitment
- Clear account creation process

---

## 📈 Expected Metrics

### Guest Engagement
- **Educational Queries**: High success rate (✅ instant answers)
- **Rate Queries**: High success rate (✅ real data)
- **Action Attempts**: Conversion opportunity (❌ → signup prompt)

### Conversion Funnel
1. Guest explores features (education)
2. Guest checks rates (market data)
3. Guest attempts action (blocked)
4. Clear signup prompt shown
5. User converts to account

**Target**: 15-25% conversion rate from action attempt

---

## 🔧 Configuration Files

**Guest Supervisor**: `src/app/domain/services/agent_squad/guest_supervisor.py`
- Lines 156-179: INFORMATIONAL vs ACTION rules
- Lines 181-203: Crypto/DeFi topics routing
- Lines 234-258: Example routing patterns

**Authenticated Supervisor**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- Same topics, but routes actions to workflow agents
- Full access to portfolio and execution

---

## Summary

**Guest Philosophy**: **"Learn everything, execute with account"**

✅ **Maximum Discovery**: No barriers to learning and exploring
✅ **Real Data**: Transparent market information builds trust
✅ **Clear Boundaries**: Actions clearly require signup
✅ **Smooth Conversion**: Direct path when user wants to act

❌ **No Confusion**: Never promise features without auth
❌ **No False Starts**: Don't let users think they can transact
❌ **No Friction**: Education and data always available

**Result**: Informed users who understand value before signup = higher quality conversions

---

**Status**: ✅ CONFIGURED
**Last Updated**: January 28, 2026
