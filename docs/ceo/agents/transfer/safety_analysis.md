# Transfer Safety Analysis

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Phase 1+2 Implemented

---

## Overview

The Transfer Workflow includes comprehensive safety analysis to protect users from:

- Sending to unknown smart contracts
- First-time recipient mistakes (typos, phishing)
- Known scam/risky addresses
- Unverified contracts

---

## Implementation Phases

### Phase 1: Basic Safety (✅ Complete)

| Feature | Description | Status |
|---------|-------------|--------|
| EOA vs Contract | Detect if recipient is a wallet or contract | ✅ |
| Known Addresses | Local database of exchanges/protocols | ✅ |
| Blocklist | Known scam/risky addresses | ✅ |
| Safety Score | 0-100 score calculation | ✅ |
| Risk Levels | Low/Medium/High/Critical classification | ✅ |

### Phase 2: Etherscan Integration (✅ Complete)

| Feature | Description | Status |
|---------|-------------|--------|
| Address Labels | Contract names from Etherscan | ✅ |
| Verification Status | Check if contract is verified | ✅ |
| Interaction History | Previous transfers to recipient | ✅ |
| API V2 Support | Unified endpoint for 60+ chains | ✅ |

### Phase 3: Compliance (⏳ Future)

| Feature | Description | Status |
|---------|-------------|--------|
| OFAC Screening | Sanctions list checking | ⏳ |
| AML/KYC Risk | Risk scoring via Chainalysis | ⏳ |
| Mixer Detection | Identify mixer exposure | ⏳ |
| Smart Contract Audit | Security analysis | ⏳ |

---

## Safety Checks Detail

### 1. EOA vs Smart Contract Detection

**Method**: `Web3Client.is_contract()`

```python
async def is_contract(self, address: str) -> bool:
    """Check if address has bytecode (is a contract)."""
    result = await self._call_rpc("eth_getCode", [address, "latest"])
    return result not in ("0x", "0x0", "")
```

**Logic**:
- EOA (regular wallet) has no bytecode → `"0x"`
- Smart Contract has bytecode → `"0x6080604052..."`

**Risk Assessment**:
- EOA: Generally safer for personal transfers
- Known Contract: Check if verified and labeled
- Unknown Contract: Higher risk, warn user

### 2. Known Address Labels

**Sources**:
1. Local database (`KNOWN_CONTRACTS`)
2. Etherscan API V2

**Local Database**:
```python
KNOWN_CONTRACTS = {
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": {
        "name": "Uniswap Universal Router",
        "category": "exchange",
        "safe": True
    },
    # More addresses...
}
```

**Etherscan API**:
```python
# Contract source code lookup
params = {
    "chainid": 8453,  # Base
    "module": "contract",
    "action": "getsourcecode",
    "address": "0x...",
    "apikey": "..."
}
response = await client.get(API_V2_URL, params=params)

# Returns contract name, verification status
```

### 3. Interaction History

**Method**: `EtherscanClient.get_recent_interactions()`

**Purpose**: Check if user has previously sent to this address

**Logic**:
```python
# Get user's transaction history
params = {
    "chainid": 8453,
    "module": "account",
    "action": "txlist",
    "address": user_wallet,
    "sort": "desc",
}
transactions = await client.get(API_V2_URL, params=params)

# Filter for transactions to recipient
previous_interactions = [tx for tx in transactions if tx["to"] == recipient]

if len(previous_interactions) == 0:
    # First-time recipient - add warning
    warnings.append("You haven't sent to this address before")
```

### 4. Contract Verification Status

**Method**: `EtherscanClient.is_contract_verified()`

**Purpose**: Check if contract source code is published

```python
# ABI lookup (only works for verified contracts)
params = {
    "chainid": 8453,
    "module": "contract",
    "action": "getabi",
    "address": "0x...",
}
response = await client.get(API_V2_URL, params=params)

# status "1" = verified, "0" = not verified
is_verified = response["status"] == "1"
```

**Risk Assessment**:
- Verified: Source code is public, auditable (+10 points)
- Not Verified: Source code hidden, higher risk (-5 points)

### 5. Blocklist Check

**Local Database**:
```python
KNOWN_RISKY_ADDRESSES: set[str] = {
    # Known scam addresses
    # Would be populated from external sources in production
}

if recipient_lower in KNOWN_RISKY_ADDRESSES:
    blockers.append("This address has been flagged as risky")
```

**Blockers prevent transfer execution**

---

## Safety Score Calculation

### Formula

```python
def _calculate_safety_score(
    is_contract: bool,
    is_known: bool,
    is_known_safe: bool,
    is_first_time: bool,
    has_blockers: bool,
    is_verified: bool = False,
    previous_interactions: int = 0,
) -> int:
    score = 70  # Base score
    
    # Blockers
    if has_blockers:
        return max(0, score - 50)
    
    # Known address bonuses
    if is_known_safe:
        score += 20
    elif is_known:
        score += 10
    
    # Contract type scoring
    if not is_contract:
        score += 5  # EOA bonus
    else:
        if is_verified:
            score += 10  # Verified contract
        elif not is_known:
            score -= 15  # Unknown contract
        else:
            score -= 5  # Known but unverified
    
    # Interaction history
    if previous_interactions >= 5:
        score += 15  # Frequent recipient
    elif previous_interactions >= 2:
        score += 10  # Multiple interactions
    elif previous_interactions >= 1:
        score += 5   # At least one
    elif is_first_time:
        score -= 10  # Never sent before
    
    return max(0, min(100, score))
```

### Score Breakdown

| Factor | Points | Condition |
|--------|--------|-----------|
| Base score | 70 | Always applied |
| Known safe address | +20 | In local DB with `safe: True` |
| Known address | +10 | In local DB or Etherscan |
| Verified contract | +10 | Etherscan verified |
| EOA (not contract) | +5 | Regular wallet |
| 5+ previous txs | +15 | Frequent recipient |
| 2-4 previous txs | +10 | Multiple interactions |
| 1 previous tx | +5 | At least one |
| First-time recipient | -10 | Never sent before |
| Unverified contract | -5 | Contract not verified |
| Unknown contract | -15 | Contract with no label |
| Blockers | -50 | Flagged as risky |

### Example Calculations

**Scenario 1: Known Exchange (Coinbase)**
```
Base:          70
Known safe:   +20
Verified:     +10
Not first:    +15 (5+ txs)
Total:        115 → 100 (capped)
Risk Level:   🟢 Low
```

**Scenario 2: First-time EOA**
```
Base:          70
EOA bonus:    +5
First-time:  -10
Total:         65
Risk Level:   🟡 Medium
```

**Scenario 3: Unknown Contract**
```
Base:          70
Unknown:     -15
First-time:  -10
Total:         45
Risk Level:   🟠 High
```

**Scenario 4: Known Risky Address**
```
Base:          70
Blocker:     -50
Total:         20
Risk Level:   🔴 Critical (Blocked)
```

---

## Risk Level Classification

| Score Range | Level | Emoji | User Message |
|-------------|-------|-------|--------------|
| 80-100 | Low | 🟢 | "Proceed with confidence" |
| 60-79 | Medium | 🟡 | "Proceed with caution" |
| 40-59 | High | 🟠 | "Review carefully" |
| 0-39 | Critical | 🔴 | "Consider cancelling" |

---

## User Interface

### Safety Section Display

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 **Safety Analysis**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 **Safety Score:** 85/100 (Low Risk)
📄 Smart Contract (Uniswap Universal Router)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Warning Messages

```markdown
**⚠️ Warnings:**
• You haven't sent to this address before
• Sending to an unverified smart contract
```

### Blocked Transfer

```markdown
🚫 **Transfer Blocked - Safety Issue**

The transfer to `0x742d35...f44e` has been blocked for your protection.

**Issues detected:**
• This address has been flagged as potentially risky

**What you can do:**
• Double-check the recipient address
• Contact support if you believe this is an error
• Use a different recipient address
```

---

## Configuration

### Environment Variables

```bash
# Web3 RPC (for contract detection)
ALCHEMY_API_KEY=your-alchemy-key
# or
INFURA_API_KEY=your-infura-key

# Etherscan API V2 (for labels and history)
ETHERSCAN_API_KEY=your-etherscan-key
```

### TOML Configuration

```toml
# config/local/.secrets.toml

[rpc]
ALCHEMY_API_KEY = "..."
INFURA_API_KEY = "..."

[etherscan]
API_KEY = "61NWKRRP7RTFYA56C4SPCKHVZ6TJK9A82E"
```

---

## API Reference

### Etherscan API V2

**Base URL**: `https://api.etherscan.io/v2/api`

**Chain IDs**:
| Chain | ID |
|-------|-----|
| Ethereum | 1 |
| Base | 8453 |
| Arbitrum | 42161 |
| Optimism | 10 |
| Polygon | 137 |

**Endpoints Used**:

1. **Get Contract Source Code**
   ```
   ?chainid=8453&module=contract&action=getsourcecode&address=0x...&apikey=...
   ```

2. **Get Contract ABI**
   ```
   ?chainid=8453&module=contract&action=getabi&address=0x...&apikey=...
   ```

3. **Get Transaction List**
   ```
   ?chainid=8453&module=account&action=txlist&address=0x...&apikey=...
   ```

---

## Future Enhancements (Phase 3)

### Chainalysis Integration

```python
# OFAC Sanctions Check
response = await chainalysis.check_address(recipient)
if response.sanctioned:
    blockers.append("Address is on OFAC sanctions list")

# Risk Score
risk_score = await chainalysis.get_risk_score(recipient)
if risk_score > 70:
    warnings.append(f"High-risk address (score: {risk_score})")
```

### Smart Contract Security

```python
# Integration with SecurityAuditorAgent
audit_result = await security_auditor.analyze_contract(recipient)
if audit_result.has_vulnerabilities:
    warnings.append("Contract has known vulnerabilities")
```

### Mixer Detection

```python
# Check for mixer exposure
exposure = await chainalysis.get_mixer_exposure(recipient)
if exposure.percentage > 10:
    warnings.append(f"Address has {exposure.percentage}% mixer exposure")
```

---

## Testing

### Test Cases

1. **EOA Detection**
   - Regular wallet address → EOA
   - Contract address → Contract

2. **Known Address**
   - Uniswap Router → "Uniswap Universal Router"
   - Random address → Unknown

3. **Interaction History**
   - Previous transfers → Not first-time
   - No history → First-time warning

4. **Safety Score**
   - Known safe EOA with history → 90+
   - Unknown contract, first-time → 45-55

5. **Blocklist**
   - Known scam address → Transfer blocked

---

## Monitoring

### Metrics to Track

- Safety check latency (target: <500ms)
- Etherscan API success rate
- Web3 RPC success rate
- Blocked transfer count
- Warning acknowledgment rate

### Alerts

- Etherscan API errors > 5% → Alert
- Web3 RPC timeout > 10s → Alert
- New blocked address detected → Log

---

## Summary

The Transfer Safety Analysis provides multi-layer protection:

1. **Local Checks**: Known addresses, blocklist
2. **Web3 Checks**: EOA vs Contract detection
3. **Etherscan Checks**: Labels, verification, history
4. **Score Calculation**: 0-100 with risk levels
5. **User Warnings**: Clear, actionable messages
6. **Blockers**: Prevent risky transfers

This system balances security with user experience, providing warnings without blocking legitimate transfers.
