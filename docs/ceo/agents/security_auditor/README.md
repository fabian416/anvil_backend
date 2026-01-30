# Security Auditor Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Implemented (Enhancement Planned)
**Agent Type**: Enterprise Agent
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **SECURITY_AUDITOR** agent provides smart contract security analysis, vulnerability detection, and security best practices validation. It helps users assess the security posture of DeFi protocols and smart contracts before interacting with them.

### Key Differentiators

- **Vulnerability Detection**: Identify common attack patterns
- **Security Scoring**: 0-100 score with severity classifications
- **Best Practices**: Compliance with security standards
- **Audit Status**: Check existing audit reports
- **Risk Assessment**: Historical exploits and reputation

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and vulnerability types |

---

## Quick Start

### For Users

**Security Analysis Queries:**
```
• "Is Aave safe to use?"
• "Audit status of Uniswap V3"
• "Check security of 0x1234..."
• "Has this protocol been exploited?"
• "What vulnerabilities should I know about?"
• "Is this contract upgradeable?"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for vulnerability patterns

---

## Key Features

### 1. Vulnerability Detection

| Vulnerability Type | Severity | Description |
|-------------------|----------|-------------|
| **Reentrancy** | Critical | Recursive call exploitation |
| **Integer Overflow** | High | Arithmetic overflow/underflow |
| **Access Control** | Critical | Unauthorized function access |
| **Front-running** | Medium | Transaction ordering attacks |
| **Oracle Manipulation** | Critical | Price feed exploitation |
| **Flash Loan Attacks** | Critical | Uncollateralized loan exploits |

### 2. Security Scoring

| Score Range | Rating | Description |
|-------------|--------|-------------|
| 90-100 | Excellent | Minimal risk, well-audited |
| 70-89 | Good | Low risk, minor concerns |
| 50-69 | Moderate | Some vulnerabilities present |
| 30-49 | High Risk | Significant security issues |
| 0-29 | Critical | Major vulnerabilities, avoid |

### 3. Analysis Coverage

- **Known Vulnerabilities**: Common attack patterns
- **Audit Reports**: Third-party security audits
- **Protocol Reputation**: Historical performance
- **Historical Exploits**: Past security incidents
- **Upgrade Patterns**: Proxy, timelock mechanisms
- **Emergency Controls**: Pause mechanisms

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Routing)
Infrastructure Layer → SecurityAuditorAgentSlither
    ↓
External Systems
    - Vertex AI (LLM reasoning)
    - Slither (TODO: Static analysis)
    - Mythril (TODO: Symbolic execution)
    - Audit Database (TODO)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 SECURITY AUDITOR FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Is Aave safe to use?"                               │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │   Supervisor            │                               │
│  │   Detects: security     │                               │
│  │   → routes to auditor   │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   SecurityAuditor       │                               │
│  │                         │                               │
│  │  1. Check audit status  │ → Known audits               │
│  │  2. Analyze contract    │ → Vulnerability patterns     │
│  │  3. Generate score      │ → 0-100 rating               │
│  │  4. Provide advice      │ → Recommendations            │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  Response: Security assessment with recommendations          │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Detection

```python
# From intent_classifier.py
intent_to_agent = {
    "audit_contract": AgentType.SECURITY_AUDITOR,
    "security_audit": AgentType.SECURITY_AUDITOR,
}
```

### Agent Classification

```
- security_auditor: Smart contract security
```

### Routing Rules

```
14. RISK/SECURITY:
    - Protocol risk → "risk_analyzer"
    - Security audit → "security_auditor"
```

---

## Vulnerability Types

### Critical Vulnerabilities

| Type | Description | Example |
|------|-------------|---------|
| **Reentrancy** | Recursive call before state update | DAO Hack (2016) |
| **Access Control** | Missing permission checks | Parity Wallet Freeze |
| **Oracle Manipulation** | Price feed exploitation | bZx Flash Loan |
| **Logic Errors** | Flawed business logic | Compound cToken Bug |

### High Severity

| Type | Description | Mitigation |
|------|-------------|------------|
| **Integer Overflow** | Arithmetic bounds exceeded | Use SafeMath |
| **Unchecked Returns** | Ignored function returns | Check all returns |
| **Timestamp Dependence** | Block timestamp manipulation | Use block.number |

### Medium Severity

| Type | Description | Mitigation |
|------|-------------|------------|
| **Front-running** | Transaction ordering attacks | Commit-reveal |
| **DOS Attacks** | Contract unavailability | Gas limits |
| **Centralization** | Single admin control | Multi-sig |

### Low Severity

| Type | Description | Mitigation |
|------|-------------|------------|
| **Gas Optimization** | Inefficient gas usage | Optimize loops |
| **Code Quality** | Readability issues | Code standards |

---

## Configuration

### Default Parameters

```python
# From security_auditor_agent_slither.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.1           # Precision critical
max_tokens = 2000           # Detailed analysis
```

### Response Structure

```python
AgentResponse(
    content="Security analysis with score and recommendations...",
    agent_type=AgentType.SECURITY_AUDITOR,
    tools_used=["openai_api"],  # TODO: Add Slither, Mythril
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated by gemini-2.0-flash"),
    ],
    metadata={
        "tokens_used": 800,
        "latency_ms": 1500,
        "model": "gemini-2.0-flash",
    },
)
```

---

## Future Enhancements (TODO)

### 1. Slither Integration

```python
# TODO: Integrate Slither for static analysis
# sources.append(create_api_source(
#     source_name="Slither",
#     citation_text="Static analysis from Slither",
#     provider="Slither Static Analyzer",
# ))
```

### 2. Mythril Integration

```python
# TODO: Integrate Mythril for symbolic execution
```

### 3. Audit Database

```python
# TODO: Add audit database source
# sources.append(create_api_source(
#     source_name="Audit Reports",
#     url="https://github.com/trailofbits/publications",
#     citation_text="Security audit reports database",
# ))
```

### 4. Real-Time Analysis

- On-chain contract verification
- Bytecode analysis
- Source code scanning

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

**Security Features:**
- ✅ Emergency pause mechanism
- ✅ Timelock for governance
- ✅ Multi-sig admin controls
- ✅ Formal verification of core contracts

**Historical Record:**
- No major exploits since launch
- $10B+ TVL safely secured
- Active bug bounty program ($250k max)

**Recommendations:**
- Safe for use with standard DeFi risks
- Monitor governance proposals
- Use isolated collateral mode for new assets

📌 *This is a security assessment, not financial advice.*
```

### Contract Address Check

```
User: "Check security of 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

Agent:
🔒 **Security Analysis: Contract**

**Contract Identified:** Uniswap V2 Router

**Security Score: 92/100** ✅ Excellent

**Audit Status:**
- ✅ Audited by dapp.org
- ✅ Formal security review completed
- ✅ Battle-tested since 2020

**Contract Details:**
- Type: DEX Router (non-upgradeable)
- Verified on Etherscan
- Open source

**Security Features:**
- ✅ No admin functions
- ✅ Immutable contract
- ✅ No pause mechanism (by design)

**Known Considerations:**
- ⚠️ Front-running possible (inherent to AMMs)
- ⚠️ Slippage protection user responsibility

📌 *This is a security assessment, not financial advice.*
```

---

## Security Best Practices

### For Users

1. **Check Audit Status**: Always verify third-party audits
2. **Review TVL History**: Higher TVL = more battle-tested
3. **Monitor Governance**: Watch for suspicious proposals
4. **Use Tested Protocols**: Prefer established protocols
5. **Start Small**: Test with small amounts first

### For Developers

1. **Get Multiple Audits**: Different auditors find different issues
2. **Formal Verification**: Use for critical contracts
3. **Bug Bounty Program**: Incentivize security researchers
4. **Upgrade Carefully**: Use timelock for upgrades
5. **Emergency Pause**: Implement circuit breakers

---

## Testing Checklist

### Unit Tests
- [ ] Vulnerability pattern detection
- [ ] Security scoring logic
- [ ] Audit status checking

### Integration Tests
- [ ] LLM response generation
- [ ] Source attribution
- [ ] Slither integration (TODO)

### E2E Tests
- [ ] Complete security analysis flow
- [ ] Multi-protocol comparison
- [ ] Historical exploit lookup

---

## Related Documentation

- **Risk Analyzer Agent**: `/docs/ceo/agents/risk_analyzer/` (protocol risk)
- **Research Agent**: `/docs/ceo/agents/research/` (deep analysis)
- **Execution Agent**: `/docs/ceo/agents/execution/` (safe execution)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Security Auditor Agent Specification**
