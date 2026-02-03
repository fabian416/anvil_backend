# Security Auditor Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, vulnerability types, and example responses for the **SECURITY_AUDITOR** agent.

---

## Query Patterns

### Protocol Safety Checks

| Query | Intent | Description |
|-------|--------|-------------|
| "Is Aave safe to use?" | security_audit | Protocol safety assessment |
| "Is Uniswap V3 secure?" | security_audit | DEX security check |
| "Should I trust Compound?" | security_audit | Protocol trust evaluation |
| "Is this protocol safe?" | security_audit | General safety query |

### Audit Status Queries

| Query | Intent | Description |
|-------|--------|-------------|
| "Has Aave been audited?" | audit_contract | Audit status check |
| "Who audited Uniswap?" | audit_contract | Auditor information |
| "Show me audit reports for Compound" | audit_contract | Audit report lookup |
| "Audit status of Morpho" | audit_contract | Audit verification |

### Contract Address Analysis

| Query | Intent | Description |
|-------|--------|-------------|
| "Check security of 0x1234..." | audit_contract | Contract analysis |
| "Is this contract safe: 0x..." | security_audit | Contract verification |
| "Analyze this contract address" | audit_contract | Address security |

### Vulnerability Queries

| Query | Intent | Description |
|-------|--------|-------------|
| "What is reentrancy?" | security_audit | Vulnerability explanation |
| "How do flash loan attacks work?" | security_audit | Attack mechanism |
| "What vulnerabilities should I know about?" | security_audit | Common vulnerabilities |
| "Has this been exploited before?" | security_audit | Historical exploits |

### Best Practices

| Query | Intent | Description |
|-------|--------|-------------|
| "How to stay safe in DeFi?" | security_audit | Safety best practices |
| "What makes a contract secure?" | security_audit | Security standards |
| "Security checklist for DeFi" | security_audit | Safety guidelines |

---

## Example Conversations

### Protocol Safety Check

```
User: "Is Aave V3 safe to use?"

Agent:
🔒 **Security Analysis: Aave V3**

**Security Score: 95/100** ✅ Excellent

**Audit Status:**
- ✅ Audited by Trail of Bits (2022)
- ✅ Audited by OpenZeppelin (2022)
- ✅ Audited by Certora (Formal Verification)
- ✅ Audited by SigmaPrime (2022)

**Security Features:**
- ✅ Emergency pause mechanism (Guardian)
- ✅ Timelock for governance (2-day delay)
- ✅ Multi-sig admin controls
- ✅ Formal verification of core contracts
- ✅ Isolation mode for risky assets

**Historical Record:**
- No major exploits since V3 launch
- $10B+ TVL safely secured
- Active bug bounty program ($250k max)
- Quick response to vulnerability disclosures

**Upgrade Patterns:**
- Transparent proxy pattern
- Governance-controlled upgrades
- Time-locked changes

**Recommendations:**
- ✅ Safe for use with standard DeFi risks
- ⚠️ Monitor governance proposals for changes
- ⚠️ Use isolation mode for volatile assets
- ⚠️ Set health factor buffer (recommended: >1.5)

📌 *This is a security assessment, not financial advice.*
```

### Contract Address Analysis

```
User: "Check security of 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

Agent:
🔒 **Security Analysis: Contract Address**

**Contract Identified:** Uniswap V2 Router02

**Security Score: 92/100** ✅ Excellent

**Contract Details:**
- **Type:** DEX Router
- **Deployed:** May 2020
- **Verified:** ✅ Yes (Etherscan)
- **Open Source:** ✅ Yes

**Audit Status:**
- ✅ Audited by dapp.org
- ✅ Formal security review completed
- ✅ Battle-tested for 4+ years

**Security Features:**
- ✅ No admin functions (immutable)
- ✅ No pause mechanism (by design)
- ✅ No upgrade capability (immutable)
- ✅ Simple, well-tested logic

**Known Considerations:**
- ⚠️ Front-running possible (inherent to AMMs)
- ⚠️ Slippage protection is user responsibility
- ⚠️ No MEV protection built-in

**Historical Record:**
- No direct exploits on router contract
- Individual pool vulnerabilities possible
- Billions in trading volume processed

**Recommendations:**
- ✅ Safe to interact with
- ⚠️ Always set slippage tolerance
- ⚠️ Use deadline parameter
- ⚠️ Consider MEV protection (Flashbots)

📌 *This is a security assessment, not financial advice.*
```

### Vulnerability Explanation

```
User: "What is reentrancy?"

Agent:
🔒 **Vulnerability Explained: Reentrancy Attack**

**Severity:** 🔴 Critical

**What is it?**
A reentrancy attack occurs when a malicious contract calls back into the 
vulnerable contract before the first function execution is complete, 
allowing the attacker to repeatedly withdraw funds.

**How it works:**
```
1. Attacker calls withdraw(100 ETH)
2. Contract sends 100 ETH to attacker
3. Attacker's fallback() calls withdraw() again
4. Contract still shows balance = 100 ETH (not updated yet)
5. Contract sends another 100 ETH
6. Repeat until drained
```

**Famous Example: The DAO Hack (2016)**
- $60 million worth of ETH stolen
- Led to Ethereum hard fork
- Created Ethereum Classic

**Vulnerable Pattern:**
```solidity
// ❌ VULNERABLE
function withdraw(uint amount) external {
    require(balances[msg.sender] >= amount);
    (bool success,) = msg.sender.call{value: amount}("");  // External call
    require(success);
    balances[msg.sender] -= amount;  // State updated AFTER call
}
```

**Secure Pattern:**
```solidity
// ✅ SECURE (Checks-Effects-Interactions)
function withdraw(uint amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;  // State updated BEFORE call
    (bool success,) = msg.sender.call{value: amount}("");
    require(success);
}

// ✅ SECURE (ReentrancyGuard)
function withdraw(uint amount) external nonReentrant {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    (bool success,) = msg.sender.call{value: amount}("");
    require(success);
}
```

**How to Protect Yourself:**
1. Check if protocol follows Checks-Effects-Interactions pattern
2. Look for ReentrancyGuard usage
3. Prefer protocols with formal verification
4. Check audit reports for reentrancy findings

📌 *Understanding vulnerabilities helps you make safer DeFi choices.*
```

### Historical Exploits

```
User: "Has Curve been exploited?"

Agent:
🔒 **Security History: Curve Finance**

**Current Security Score: 82/100** ✅ Good

**Exploit History:**

**July 2023 - Vyper Compiler Bug**
- **Impact:** ~$70M stolen from multiple pools
- **Root Cause:** Vyper 0.2.15-0.2.16 reentrancy vulnerability
- **Affected Pools:** pETH/ETH, msETH/ETH, alETH/ETH
- **Resolution:** Partial fund recovery, bug bounty paid
- **Status:** Fixed, affected pools redeployed

**Response & Recovery:**
- ✅ Quick incident response
- ✅ Coordinated disclosure
- ✅ Community fund recovery efforts
- ✅ Increased bug bounty
- ✅ Compiler upgrade to Vyper 0.3.10+

**Current Security Measures:**
- ✅ Multiple audits completed
- ✅ Bug bounty program ($250k max)
- ✅ Vyper compiler updated
- ✅ Active security monitoring

**Recommendations:**
- ⚠️ Use newer pools (post-2023)
- ⚠️ Check pool deployment date
- ⚠️ Verify Vyper version used
- ✅ Main CRV token and core pools remain secure

**TVL History:**
- Pre-exploit: $4.5B
- Post-exploit: $2.2B
- Current: Recovering

📌 *Historical exploits don't necessarily mean current risk, but warrant caution.*
```

### Security Best Practices

```
User: "How to stay safe in DeFi?"

Agent:
🔒 **DeFi Security Best Practices**

**Before Using Any Protocol:**

1. **Check Audit Status**
   - ✅ Multiple reputable auditors (Trail of Bits, OpenZeppelin, Certora)
   - ✅ Recent audits (within last year)
   - ✅ Formal verification for critical contracts

2. **Verify Smart Contracts**
   - ✅ Verified on Etherscan
   - ✅ Open source code
   - ✅ Match deployed bytecode

3. **Assess Protocol Reputation**
   - ✅ Time in production (>1 year preferred)
   - ✅ TVL history (higher = more battle-tested)
   - ✅ Team reputation and transparency

4. **Check for Security Features**
   - ✅ Emergency pause mechanism
   - ✅ Timelock on upgrades
   - ✅ Multi-sig governance
   - ✅ Bug bounty program

**When Using Protocols:**

5. **Start Small**
   - Test with small amounts first
   - Gradually increase exposure

6. **Set Protection Parameters**
   - Use slippage tolerance
   - Set transaction deadlines
   - Monitor health factors

7. **Diversify**
   - Don't put all funds in one protocol
   - Use multiple chains/protocols

8. **Stay Informed**
   - Follow protocol announcements
   - Join Discord/Telegram for alerts
   - Monitor governance proposals

**Red Flags to Watch:**

❌ No audit reports
❌ Anonymous team with no track record
❌ Unusually high yields (too good to be true)
❌ No multi-sig or timelock
❌ Recent fork with minimal changes
❌ No bug bounty program

**Security Tools:**

- **DeFi Safety** - Protocol safety ratings
- **Etherscan** - Contract verification
- **Revoke.cash** - Approval management
- **Tenderly** - Transaction simulation

📌 *Security is your responsibility. Always DYOR (Do Your Own Research).*
```

---

## Vulnerability Quick Reference

### Critical Vulnerabilities

| Type | Description | Detection |
|------|-------------|-----------|
| **Reentrancy** | Recursive call before state update | Checks-Effects-Interactions pattern |
| **Oracle Manipulation** | Price feed exploitation | TWAP vs spot price |
| **Access Control** | Missing permission checks | Modifier usage |
| **Logic Errors** | Flawed business logic | Formal verification |

### High Severity

| Type | Description | Mitigation |
|------|-------------|------------|
| **Integer Overflow** | Arithmetic bounds exceeded | SafeMath, Solidity 0.8+ |
| **Unchecked Returns** | Ignored function returns | Check all returns |
| **Timestamp Dependence** | Block timestamp manipulation | Use block.number |

### Medium Severity

| Type | Description | Mitigation |
|------|-------------|------------|
| **Front-running** | Transaction ordering attacks | Commit-reveal, Flashbots |
| **DOS Attacks** | Contract unavailability | Gas limits, pull payments |
| **Centralization** | Single admin control | Multi-sig, timelock |

---

## API Response Examples

### Protocol Security Query

```json
{
  "agent_message": {
    "content": "🔒 **Security Analysis: Aave V3**\n\n**Security Score: 95/100** ✅ Excellent...",
    "role": "assistant",
    "agent_type": "security_auditor"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "security_auditor", "duration_ms": 2500}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

---

## Security Scoring Criteria

### Score Breakdown

| Factor | Weight | Criteria |
|--------|--------|----------|
| **Audit Status** | 30% | Multiple audits, reputable firms |
| **TVL & Track Record** | 25% | Time in production, no exploits |
| **Security Features** | 20% | Pause, timelock, multi-sig |
| **Code Quality** | 15% | Verified, open source |
| **Upgrade Safety** | 10% | Proxy pattern, governance |

### Score Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | Safe to use with standard caution |
| 70-89 | Good | Generally safe, minor concerns |
| 50-69 | Moderate | Proceed with extra caution |
| 30-49 | High Risk | Consider alternatives |
| 0-29 | Critical | Avoid until issues resolved |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Security Auditor Agent Shortcuts**
