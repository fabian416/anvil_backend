# Compliance Monitor Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, compliance checks, and example responses for the **COMPLIANCE_MONITOR** agent.

---

## Query Patterns

### Wallet Screening

| Query | Intent | Description |
|-------|--------|-------------|
| "Screen wallet 0x1234..." | screen_wallet | Full compliance check |
| "Check compliance for 0xABC..." | check_compliance | Same as screening |
| "Is this address sanctioned?" | check_compliance | OFAC check |
| "Run AML check on 0x..." | check_compliance | AML screening |

### Risk Assessment

| Query | Intent | Description |
|-------|--------|-------------|
| "What's the risk score for 0x...?" | check_compliance | Risk score query |
| "Is 0x... safe to transact with?" | check_compliance | Safety check |
| "Check if 0x... is a mixer" | check_compliance | Mixer detection |
| "PEP check for 0x..." | check_compliance | Political exposure |

### Compliance Status

| Query | Intent | Description |
|-------|--------|-------------|
| "Show my compliance status" | check_compliance | User's own status |
| "Am I cleared for transactions?" | check_compliance | Approval status |
| "Why was my transaction blocked?" | check_compliance | Block reason |

---

## Compliance Check Types

### OFAC Sanctions

| Check | Description | Source |
|-------|-------------|--------|
| **SDN List** | Specially Designated Nationals | US Treasury |
| **Consolidated List** | Combined sanctions | OFAC |
| **Country Sanctions** | Iran, North Korea, etc. | OFAC |

### PEP Screening

| Check | Description | Source |
|-------|-------------|--------|
| **Politician** | Current/former officials | Chainalysis |
| **Government Official** | Civil servants | Chainalysis |
| **Family Members** | Close relatives of PEPs | Chainalysis |
| **Close Associates** | Business partners of PEPs | Chainalysis |

### Risk Indicators

| Indicator | Risk Weight | Description |
|-----------|-------------|-------------|
| **Mixer Exposure** | High | Tornado Cash, etc. |
| **Darknet Markets** | Critical | Known marketplaces |
| **Ransomware** | Critical | Ransomware addresses |
| **Scam Addresses** | High | Known scam wallets |
| **High-Risk Exchanges** | Medium | Unregulated exchanges |

---

## Example Conversations

### Approved Wallet

```
User: "Screen wallet 0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

Agent:
🔍 **WALLET SCREENING COMPLETE**

**Wallet**: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`
**Screening ID**: SCR-0x742d35
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

*This screening is for informational purposes and does not constitute
legal or financial advice. Consult compliance professionals for
regulatory guidance.*
```

### Manual Review Required

```
User: "Check compliance for 0xSuspiciousAddress..."

Agent:
🔍 **WALLET SCREENING COMPLETE**

**Wallet**: `0xSuspiciousAddress...`
**Screening ID**: SCR-0xSusp

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**RISK ASSESSMENT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌────────────────────────────────────────────┐
│ Check Type        Status      Risk Score   │
├────────────────────────────────────────────┤
│ OFAC Sanctions    ✅ CLEAR       0/100      │
│ PEP Check         ✅ CLEAR       0/100      │
│ Mixer Exposure    ⚠️ Detected   35/100      │
│ High Risk Source  ⚠️ Detected   30/100      │
└────────────────────────────────────────────┘

**OVERALL RISK**: 🟠 HIGH (65/100)
**Decision**: ⚠️ **MANUAL_REVIEW**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ MANUAL REVIEW REQUIRED**

This wallet requires manual review by our compliance team before
transactions can proceed.

**Next Steps**:
- Compliance review typically takes 2-4 hours
- You will be notified via email when review is complete
- High-priority cases can be expedited (contact support)

**Estimated Resolution**: 2-4 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Flagged Issues**:
- 5% of funds traced to mixer services
- Interaction with known high-risk exchange

**Recommendation**: Provide additional KYC documentation to expedite review.
```

### Blocked Wallet

```
User: "Is 0xSanctionedAddress... safe to transact with?"

Agent:
🔍 **WALLET SCREENING COMPLETE**

**Wallet**: `0xSanctionedAddress...`
**Screening ID**: SCR-0xSanc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**RISK ASSESSMENT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌────────────────────────────────────────────┐
│ Check Type        Status      Risk Score   │
├────────────────────────────────────────────┤
│ OFAC Sanctions    ⛔ HIT        50/100      │
│ PEP Check         ✅ CLEAR       0/100      │
│ Mixer Exposure    ⛔ High       30/100      │
│ High Risk Source  ⛔ Multiple   20/100      │
└────────────────────────────────────────────┘

**OVERALL RISK**: 🔴 CRITICAL (95/100)
**Decision**: ⛔ **BLOCKED**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⛔ TRANSACTION BLOCKED**

This wallet has been flagged for high-risk activity and transactions
are automatically blocked pending investigation.

**OFAC Sanctions Hit**:
- **List**: SDN (Specially Designated Nationals)
- **Reason**: Designated by OFAC for sanctions violations
- **Effective Date**: 2023-08-08

**Next Steps**:
- Review is required by compliance team
- Contact support if you believe this is an error
- Provide KYC documentation for whitelist consideration

**Compliance Note**: This decision is final and cannot be overridden
without manual compliance approval.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Warning**: Transacting with sanctioned addresses may result in legal
consequences. Do not proceed with this address.
```

### No Address Found

```
User: "Check compliance"

Agent:
No wallet address found in message. Please provide a valid wallet address to screen.

**Example Queries**:
- "Screen wallet 0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
- "Check compliance for 0xABC..."
- "Is 0x... sanctioned?"

**Supported Formats**:
- Ethereum addresses (0x...)
- ENS names (example.eth) - coming soon
```

---

## API Response Examples

### Approved Screening

```json
{
  "agent_message": {
    "content": "🔍 **WALLET SCREENING COMPLETE**\n\n**Wallet**: `0x1234...`...",
    "role": "assistant",
    "agent_type": "compliance_monitor"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 50},
      {"agent_type": "compliance_monitor", "duration_ms": 800}
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Chainalysis",
        "url": "https://www.chainalysis.com/",
        "citation_text": "Compliance screening for wallet 0x1234...",
        "provider": "Chainalysis API",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "OFAC",
        "url": "https://ofac.treasury.gov/",
        "citation_text": "OFAC sanctions list check",
        "provider": "US Treasury OFAC",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  },
  "metadata": {
    "wallet_address": "0x1234...",
    "risk_score": 25,
    "decision": "APPROVED",
    "screening_id": "SCR-0x1234..."
  }
}
```

### Blocked Screening

```json
{
  "agent_message": {
    "content": "🔍 **WALLET SCREENING COMPLETE**\n\n⛔ **BLOCKED**...",
    "role": "assistant",
    "agent_type": "compliance_monitor"
  },
  "metadata": {
    "wallet_address": "0xSanctioned...",
    "risk_score": 95,
    "decision": "BLOCKED",
    "screening_id": "SCR-0xSanct..."
  }
}
```

---

## Risk Score Reference

### Score Thresholds

| Score | Level | Decision | Color |
|-------|-------|----------|-------|
| 0-29 | LOW | APPROVED | 🟢 |
| 30-59 | MEDIUM | APPROVED (monitored) | 🟡 |
| 60-79 | HIGH | MANUAL_REVIEW | 🟠 |
| 80-100 | CRITICAL | BLOCKED | 🔴 |

### Risk Factors

| Factor | Max Score | Description |
|--------|-----------|-------------|
| OFAC Sanctions | 50 | SDN list match |
| PEP Status | 40 | Political exposure |
| Mixer Exposure | 30 | % of funds from mixers |
| Darknet Markets | 30 | Known marketplace interaction |
| Ransomware | 30 | Ransomware address link |
| High-Risk Exchanges | 20 | Unregulated exchange usage |

---

## Regulatory Compliance

### Supported Frameworks

| Framework | Jurisdiction | Requirements |
|-----------|--------------|--------------|
| **FinCEN** | US | BSA reporting, CTRs, SARs |
| **OFAC** | US | SDN screening, sanctions |
| **MiCA** | EU | Travel Rule, licensing |
| **AMLD6** | EU | AML/CFT compliance |
| **FCA MLR** | UK | Enhanced due diligence |

### Audit Trail

- **Storage Duration**: 7 years
- **Format**: Immutable logs
- **Access**: Compliance team only
- **Retention**: Per regulatory requirements

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Compliance Monitor Agent Shortcuts**
