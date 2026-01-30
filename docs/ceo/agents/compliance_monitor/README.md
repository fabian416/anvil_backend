# Compliance Monitor Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Implemented (Enhancement Planned)
**Agent Type**: Enterprise Agent
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **COMPLIANCE_MONITOR** agent provides AML/KYC compliance and regulatory screening using Chainalysis blockchain analytics. It screens wallet addresses for sanctions, PEP status, and suspicious activity patterns.

### Key Differentiators

- **Real-Time Screening**: Instant wallet compliance checks
- **OFAC Sanctions**: Automatic SDN list verification
- **PEP Detection**: Politically Exposed Person screening
- **Risk Scoring**: 0-100 scale with automatic decisions
- **Multi-Jurisdiction**: US (FinCEN), EU (MiCA), UK compliance

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and compliance checks |

---

## Quick Start

### For Users

**Compliance Queries:**
```
• "Screen wallet 0x1234..."
• "Check compliance for 0xABC..."
• "Is this address sanctioned?"
• "Run AML check on 0x..."
• "What's the risk score for 0x...?"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for compliance types

---

## Key Features

### 1. Compliance Checks

| Check Type | Description | Source |
|------------|-------------|--------|
| **OFAC Sanctions** | SDN list verification | US Treasury |
| **PEP Check** | Politically Exposed Persons | Chainalysis |
| **Mixer Exposure** | Tornado Cash, etc. | Chainalysis |
| **High-Risk Sources** | Known bad actors | Chainalysis |

### 2. Risk Scoring

| Score Range | Level | Action |
|-------------|-------|--------|
| 0-29 | 🟢 LOW | Approved automatically |
| 30-59 | 🟡 MEDIUM | Approved with monitoring |
| 60-79 | 🟠 HIGH | Manual review required |
| 80-100 | 🔴 CRITICAL | Blocked automatically |

### 3. Compliance Features

| Feature | Description |
|---------|-------------|
| **Auto-Blocking** | Risk score > 80 = automatic block |
| **Manual Review** | Risk score 60-80 = compliance team review |
| **Whitelisting** | Approved addresses bypass checks |
| **False Positive Handling** | Appeal process for blocked addresses |
| **Multi-Jurisdiction** | US, EU, UK regulatory frameworks |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Routing)
Infrastructure Layer → ComplianceMonitorAgentChainalysis
    ↓
External Systems
    - Chainalysis (Blockchain analytics)
    - OFAC (Sanctions lists)
    - Vertex AI (LLM reasoning)
```

### Compliance Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  COMPLIANCE SCREENING FLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User requests wallet screening                          │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │  Compliance Monitor     │                               │
│  │                         │                               │
│  │  2. Extract address     │ → LLM parsing                 │
│  │  3. Chainalysis API     │ → Risk analysis               │
│  │  4. OFAC check          │ → Sanctions verification      │
│  │  5. PEP check           │ → Political exposure          │
│  │  6. Calculate score     │ → 0-100 risk score            │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  7. Decision: APPROVED / REVIEW / BLOCKED                   │
│              ↓                                              │
│  8. Log to compliance_screening_logs                        │
│              ↓                                              │
│  9. Return compliance report                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Detection

```python
# From intent_classifier.py
intent_to_agent = {
    "check_compliance": AgentType.COMPLIANCE_MONITOR,
    "screen_wallet": AgentType.COMPLIANCE_MONITOR,
}
```

### Agent Classification

```
- compliance_monitor: AML/KYC (enterprise)
```

### Keyword Detection

```python
# From keyword_intent_detection_adapter.py
keywords = ["compliance", "aml", "kyc", "regulatory", "chainalysis"]
```

---

## Configuration

### Default Parameters

```python
# From compliance_monitor_agent_chainalysis.py

model = "gemini-2.0-flash"           # Vertex AI
temperature = 0.1                     # Precision critical
max_tokens = 2000                     # Detailed reports
risk_threshold_block = 80             # Auto-block threshold
risk_threshold_review = 60            # Manual review threshold
```

### Response Structure

```python
AgentResponse(
    content="Compliance screening report...",
    agent_type=AgentType.COMPLIANCE_MONITOR,
    tools_used=["chainalysis_api", "ofac_api", "openai_api"],
    sources=[
        SourceInfo(source_type="api", source_name="Chainalysis",
                   citation_text="Compliance screening for wallet 0x1234..."),
        SourceInfo(source_type="api", source_name="OFAC",
                   citation_text="OFAC sanctions list check"),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated by gemini-2.0-flash"),
    ],
    metadata={
        "latency_ms": 800,
        "wallet_address": "0x1234...",
        "risk_score": 25,
        "decision": "APPROVED",
        "screening_id": "SCR-0x1234...",
    },
)
```

---

## Screening Report Example

### Approved Wallet

```
🔍 **WALLET SCREENING COMPLETE**

**Wallet**: `0x1234567890abcdef...`
**Screening ID**: SCR-0x123456
**Analysis Time**: 0.8s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**RISK ASSESSMENT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌────────────────────────────────────────────┐
│ Check Type        Status      Risk Score   │
├────────────────────────────────────────────┤
│ OFAC Sanctions    ✅ CLEAR       0/100      │
│ PEP Check         ✅ CLEAR       0/100      │
│ Mixer Exposure    ✅ None        0/100      │
│ High Risk Source  ✅ None        0/100      │
└────────────────────────────────────────────┘

**OVERALL RISK**: 🟢 LOW (25/100)
**Decision**: ✅ **APPROVED**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**✅ TRANSACTION APPROVED**

This wallet has been cleared for transactions. No compliance issues
detected.

**Valid For**: 24 hours (re-screening required after)
**Transaction Limits**: Standard limits apply
**Next Screening**: Automatic (on next transaction after 24h)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Compliance Framework**: Multi-jurisdictional (US, EU, UK)
**Powered By**: Chainalysis
**Audit Trail**: Immutable (stored for 7 years)
```

### Blocked Wallet

```
🔍 **WALLET SCREENING COMPLETE**

**Wallet**: `0xSanctionedAddress...`
**Screening ID**: SCR-0xSanct

**OVERALL RISK**: 🔴 CRITICAL (95/100)
**Decision**: ⛔ **BLOCKED**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⛔ TRANSACTION BLOCKED**

This wallet has been flagged for high-risk activity and transactions
are automatically blocked pending investigation.

**Next Steps**:
- Review is required by compliance team
- Contact support if you believe this is an error
- Provide KYC documentation for whitelist consideration

**Compliance Note**: This decision is final and cannot be overridden
without manual compliance approval.
```

---

## Regulatory Frameworks

### Supported Jurisdictions

| Jurisdiction | Framework | Requirements |
|--------------|-----------|--------------|
| **US** | FinCEN, OFAC | BSA compliance, SDN list |
| **EU** | MiCA, AMLD6 | Travel Rule, beneficial ownership |
| **UK** | FCA, MLR 2017 | Enhanced due diligence |

### Reporting Capabilities

- **FinCEN SARs**: Suspicious Activity Reports
- **SEC Filings**: Securities-related compliance
- **EU MiCA**: Crypto asset service provider rules
- **Audit Trails**: 7-year immutable storage

---

## Future Enhancements (TODO)

### 1. Real Chainalysis API Integration

```python
# TODO: Implement real Chainalysis API integration
async def _screen_wallet(self, wallet_address: WalletAddress) -> dict:
    # Query Chainalysis KYT API
    # Get real-time risk assessment
    # Return structured screening result
    pass
```

### 2. Transaction Monitoring

- Continuous transaction monitoring
- Automatic re-screening on large transactions
- Pattern detection for suspicious activity

### 3. Enhanced PEP Database

- Real-time PEP database updates
- Family member screening
- Political position tracking

---

## Testing Checklist

### Unit Tests
- [ ] Address extraction logic
- [ ] Risk score calculation
- [ ] Decision thresholds
- [ ] Report generation

### Integration Tests
- [ ] Chainalysis API integration
- [ ] OFAC API integration
- [ ] Source attribution

### E2E Tests
- [ ] Complete screening flow
- [ ] Multi-jurisdiction compliance
- [ ] Audit trail logging

---

## Related Documentation

- **Security Auditor Agent**: `/docs/ceo/agents/security_auditor/` (contract security)
- **Alert Monitoring Agent**: `/docs/ceo/agents/alert_monitoring/` (real-time alerts)
- **Crisis Manager Agent**: `/docs/ceo/agents/crisis_manager/` (emergency response)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Compliance Monitor Agent Specification**
