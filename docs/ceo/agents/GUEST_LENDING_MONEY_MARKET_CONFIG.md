# Guest Lending & Money Market Configuration

**Date**: January 28, 2026
**Status**: ✅ CONFIGURED
**Updated By**: @backend-engineer

---

## Executive Summary

Configured the **Guest Supervisor** to support lending and money market features with clear separation between:
- ✅ **ALLOWED FOR GUESTS**: Informational queries (education, rate comparison, protocol info)
- ❌ **REQUIRES SIGNUP**: Transaction actions (deposits, withdrawals, position management)

---

## Guest Capabilities Matrix

### ✅ Lending & Money Market - ALLOWED (No Signup Required)

#### Educational Queries → `knowledge` agent
```
"can i lend usdc?"
"how to lend tokens?"
"what is money market?"
"what is lending?"
"how does lending work?"
"what are the risks of lending?"
"explain Aave"
"explain Compound"
"difference between Aave and Compound"
"what lending protocols are supported?"
"puedo prestar usdc?" (Spanish)
"posso emprestar tokens?" (Portuguese)
```

**Response**: Knowledge agent explains lending concepts, how it works, supported protocols, etc.

#### Rate Comparison Queries → `hunter_ai` agent
```
"compare USDC lending rates"
"aave vs compound rates"
"best USDC APY"
"what are current lending rates?"
"compare rates for USDC on Base"
"best lending rate for USDC"
"show me Aave rates"
"what's the APY on Compound?"
```

**Response**: Hunter AI provides real-time rate data from protocols (informational only)

---

### ❌ Lending & Money Market - REQUIRES SIGNUP

#### Deposit Actions → `guest_auth` agent
```
"lend 100 USDC"
"deposit 100 USDC to Aave"
"deposit to money market"
"supply USDC to Compound"
"deposit 50 USDC on Base"
"lend to Aave"
"execute the deposit"
"do the lending"
```

**Response**: Guest auth agent prompts user to create account/login:
```
❌ Lending and deposits require an account.

Create your free account to:
✅ Lend crypto and earn APY
✅ Compare rates across Aave, Compound
✅ Track your lending positions
✅ Automatic rate optimization

Sign up: https://app.anvil.fi/signup
```

#### Withdrawal Actions → `guest_auth` agent
```
"withdraw from Aave"
"withdraw my deposit"
"withdraw USDC from Compound"
"remove liquidity"
```

**Response**: Prompts for signup (cannot withdraw without authenticated wallet)

#### Position Management → `guest_auth` agent
```
"my deposits"
"my lending positions"
"check my lended amount"
"show my positions"
"how much did I lend?"
```

**Response**: Prompts for signup (requires authenticated wallet to query positions)

---

## Router Configuration Details

**File**: `src/app/domain/services/agent_squad/guest_supervisor.py`

### Query Detection Rules (Lines 156-184)

```python
3. INFORMATIONAL vs ACTION QUERIES (CRITICAL FOR GUESTS):
   **INFORMATIONAL QUERIES → Can answer directly:**
   - "can i lend?" → "knowledge" (asking about capabilities)
   - "how to lend?" → "knowledge" (asking for instructions)
   - "compare USDC rates" → "hunter_ai" (rate information)
   - "aave vs compound rates" → "hunter_ai" (rate comparison)
   - "what is money market?" → "knowledge" (education)

   **ACTION REQUESTS → "guest_auth" agent (REQUIRES LOGIN):**
   - "lend 100 USDC" → "guest_auth" (transaction - needs wallet)
   - "deposit to Aave" → "guest_auth" (deposit - needs wallet)
   - "withdraw from Compound" → "guest_auth" (withdrawal - needs wallet)
   - "my deposits" → "guest_auth" (requires wallet)
   - "execute the deposit" → "guest_auth" (execution - needs wallet)
```

### Example Routing (Lines 234-246)

**Informational (ALLOWED):**
```json
"can i lend usdc?" → {"tasks":[{"agent_type":"knowledge","task_description":"Explain lending capabilities","depends_on":[]}]}

"compare usdc lending rates" → {"tasks":[{"agent_type":"hunter_ai","task_description":"Compare USDC lending rates across protocols","depends_on":[]}]}

"aave vs compound rates" → {"tasks":[{"agent_type":"hunter_ai","task_description":"Compare Aave vs Compound lending rates","depends_on":[]}]}
```

**Actions (BLOCKED):**
```json
"lend 100 usdc" → {"tasks":[{"agent_type":"guest_auth","task_description":"Handle lending transaction - requires login","depends_on":[]}]}

"deposit 100 usdc to aave" → {"tasks":[{"agent_type":"guest_auth","task_description":"Handle deposit transaction - requires login","depends_on":[]}]}

"my deposits" → {"tasks":[{"agent_type":"guest_auth","task_description":"Handle deposits query - requires login","depends_on":[]}]}
```

---

## User Experience Flow

### 1. Guest Asks Educational Question

**User**: "how does lending work?"

**Router Decision**: → `knowledge` agent (ALLOWED)

**Response**:
```
📚 **How DeFi Lending Works**

DeFi lending lets you earn interest by depositing crypto into lending protocols:

**Supported Protocols:**
- **Aave V3**: Multi-chain, variable + stable rates
- **Compound V3**: USDC markets, efficient capital

**How It Works:**
1. Deposit crypto (USDC, ETH, etc.)
2. Earn APY (annual percentage yield)
3. Withdraw anytime (based on liquidity)

**Benefits:**
✅ Earn passive income on idle crypto
✅ No lock-up periods
✅ Transparent on-chain rates

Want to see current rates? Try: "compare USDC lending rates"
```

### 2. Guest Asks for Rate Data

**User**: "compare USDC lending rates"

**Router Decision**: → `hunter_ai` agent (ALLOWED)

**Response**:
```
💰 **USDC Lending Rates Comparison**

**Aave V3 (Ethereum)**
- Supply APY: 3.45%
- Total Supplied: $2.1B
- Utilization: 82%

**Compound V3 (Base)**
- Supply APY: 4.12%
- Total Supplied: $450M
- Utilization: 76%

**Best Rate**: Compound V3 on Base (4.12% APY)

---

💡 **Ready to start earning?**
Create an account to deposit and earn APY:
👉 https://app.anvil.fi/signup
```

### 3. Guest Tries to Execute Action

**User**: "deposit 100 USDC to Aave"

**Router Decision**: → `guest_auth` agent (BLOCKED)

**Response**:
```
❌ **Lending Requires an Account**

To deposit crypto and earn APY, you need to create a free account.

**What you requested:**
Deposit 100 USDC to Aave V3

**To complete this:**
1. Create your free account
2. Connect your wallet (or create new one)
3. Deposit USDC and start earning 3.45% APY

🚀 **Get Started:**
👉 https://app.anvil.fi/signup

**Already have an account?**
👉 https://app.anvil.fi/login
```

---

## Multi-Language Support

All guest responses support:
- **English**: "can i lend?"
- **Spanish**: "puedo prestar?" / "depositar usdc"
- **Portuguese**: "posso emprestar?" / "depositar usdc"

The `guest_auth` agent provides signup prompts in the user's detected language.

---

## Benefits for Guests

### Discovery & Education (No Barriers)
- ✅ Learn about lending protocols
- ✅ See real-time APY rates
- ✅ Compare Aave vs Compound
- ✅ Understand risks and mechanics
- ✅ Ask "how to" questions
- ✅ Check current market conditions

### Clear Path to Conversion
When guests try actions:
1. ❌ Clear message: "Requires account"
2. 💡 Show what they requested
3. 🚀 Direct signup link
4. 🔑 Quick login link for existing users

---

## Architecture Pattern

### Separation of Concerns

**Guest Supervisor** (`guest_supervisor.py`):
- Handles routing for unauthenticated users
- Allows informational queries
- Blocks execution actions
- Provides conversion prompts

**Authenticated Supervisor** (`authenticated_supervisor.py`):
- Handles routing for authenticated users
- Allows ALL actions (info + execution)
- Routes to workflow agents (lending_workflow, money_market_workflow)
- Accesses real user portfolio data

### No Code Duplication

Both supervisors use the same specialized agents:
- `knowledge` agent: Shared educational content
- `hunter_ai` agent: Shared rate data (but no wallet access for guests)
- `guest_auth` agent: Guest-specific conversion flow

---

## Testing the Configuration

### Test Educational Queries (Should Work)

```bash
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "how does lending work?",
    "language": "en"
  }'
```

**Expected**: Knowledge agent explains lending

### Test Rate Queries (Should Work)

```bash
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "compare USDC lending rates",
    "language": "en"
  }'
```

**Expected**: Hunter AI shows real rate data

### Test Action Requests (Should Block)

```bash
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "deposit 100 USDC to Aave",
    "language": "en"
  }'
```

**Expected**: Guest auth prompts for signup

---

## Success Metrics

✅ **Informational Queries**: Guests can learn and explore without barriers
✅ **Rate Data Access**: Real-time APY comparison available to all guests
✅ **Clear Boundaries**: Action requests clearly communicate signup requirement
✅ **Conversion Flow**: Direct path from "blocked action" to "signup"
✅ **Multi-Language**: Full support for en/es/pt
✅ **No Confusion**: Clear distinction between "can I?" (info) vs "do it" (action)

---

## Summary

**Guest Lending & Money Market Configuration**:

| Feature | Guest Access | Requires Signup |
|---------|-------------|-----------------|
| Learn about lending | ✅ Yes | No |
| View lending rates | ✅ Yes | No |
| Compare protocols | ✅ Yes | No |
| Ask "how to" questions | ✅ Yes | No |
| Deposit crypto | ❌ No | ✅ Yes |
| Withdraw crypto | ❌ No | ✅ Yes |
| View positions | ❌ No | ✅ Yes |
| Execute transactions | ❌ No | ✅ Yes |

**Design Philosophy**:
- **Maximum Discovery**: Let guests explore and learn without barriers
- **Clear Conversion**: When guests want to act, show clear path to signup
- **No Frustration**: Never promise features without authentication
- **Data Access**: Real market data available to everyone (builds trust)

---

**Status**: ✅ PRODUCTION READY
**Updated**: January 28, 2026
**Configuration File**: `src/app/domain/services/agent_squad/guest_supervisor.py`
