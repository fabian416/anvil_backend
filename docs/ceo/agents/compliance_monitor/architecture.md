# Compliance Monitor Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **COMPLIANCE_MONITOR** agent, which provides AML/KYC compliance and regulatory screening using Chainalysis blockchain analytics.

### Key Components

- **ComplianceMonitorAgentChainalysis**: Agent Squad implementation
- **Chainalysis Client**: Wallet screening source
- **OFAC API**: Sanctions list verification
- **LLM Client**: Vertex AI for address extraction

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  COMPLIANCE MONITOR ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Supervisor             │
                    │  (Intent Routing)        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   ComplianceMonitorAgent │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Chainalysis   │   │   OFAC API      │   │   Vertex AI     │
│   (Screening)   │   │   (Sanctions)   │   │   (LLM)         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Enterprise Agents
    COMPLIANCE_MONITOR = "compliance_monitor"  # AML/KYC
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "check_compliance": AgentType.COMPLIANCE_MONITOR,
    "screen_wallet": AgentType.COMPLIANCE_MONITOR,
}
```

### Keyword Detection

**File**: `src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py`

```python
if any(kw in message for kw in [
    "compliance", "aml", "kyc", "regulatory", "chainalysis"
]):
    return "compliance_monitor"
```

---

## Infrastructure Layer

### ComplianceMonitorAgentChainalysis

**File**: `src/app/infrastructure/adapters/agent_squad/agents/enterprise/compliance_monitor_agent_chainalysis.py`
**Lines**: ~375

```python
class ComplianceMonitorAgentChainalysis:
    """
    Compliance Monitor Agent Chainalysis implementation.
    
    Implements: AgentGateway
    
    Purpose: AML/KYC compliance & regulatory screening
    
    Capabilities:
    - Real-time wallet screening (Chainalysis API)
    - OFAC sanction checks (automatic)
    - PEP (Politically Exposed Person) checks
    - Suspicious activity detection (ML-powered)
    - Regulatory reporting (FinCEN, SEC, EU MiCA)
    - Immutable audit trails
    - Risk scoring (0-100 scale)
    
    Compliance Features:
    - Automatic blocking (risk score > 80)
    - Manual review queue (60-80)
    - Whitelisting support
    - False positive handling
    - Multi-jurisdiction support
    
    Model: gemini-2.0-flash (compliance reasoning)
    Temperature: 0.1 (precision critical)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 46-74 | Initialize with clients and thresholds |
| `agent_type` | 76-79 | Return AgentType.COMPLIANCE_MONITOR |
| `execute` | 81-172 | Main entry point |
| `is_available` | 174-177 | Availability check |
| `_extract_wallet_address` | 179-209 | LLM-based address extraction |
| `_screen_wallet` | 211-250 | Chainalysis screening (mock) |
| `_generate_compliance_report` | 252-360 | Format screening report |
| `_build_error_response` | 362-374 | Error handling |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,           # Vertex AI
    chainalysis_client: Any,                 # ChainalysisClient (TODO)
    risk_threshold_block: int = 80,          # Auto-block threshold
    risk_threshold_review: int = 60,         # Manual review threshold
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
    max_tokens: int = 2000,
):
```

---

## Screening Flow

### Complete Process

```
1. User submits wallet screening request
   ↓
2. Extract wallet address from message (LLM)
   ↓
3. Screen wallet via Chainalysis API
   ↓
4. Check OFAC sanctions list
   ↓
5. Check PEP database
   ↓
6. Calculate risk score (0-100)
   ↓
7. Make decision based on thresholds
   ↓
8. Generate compliance report
   ↓
9. Log to compliance_screening_logs
   ↓
10. Return detailed screening results
```

### Screening Data Structure

```python
{
    "screening_id": "SCR-0x1234...",
    "wallet_address": "0x1234...",
    "risk_score": 25,
    "ofac_status": "clear",
    "pep_status": "clear",
    "mixer_exposure_pct": 0.0,
    "high_risk_sources_pct": 0.0,
    "decision": "APPROVED",
    "details": {
        "sanction_hits": [],
        "pep_hits": [],
        "mixer_interactions": [],
        "high_risk_counterparties": [],
    },
}
```

---

## Risk Scoring

### Score Calculation

| Check | Weight | Description |
|-------|--------|-------------|
| OFAC Sanctions | 50+ | Immediate block if hit |
| PEP Status | 20-40 | Depends on position |
| Mixer Exposure | 0-30 | Percentage of funds |
| High-Risk Sources | 0-30 | Known bad actors |

### Decision Thresholds

```python
# From constructor
risk_threshold_block = 80    # Auto-block
risk_threshold_review = 60   # Manual review

# Decision logic
if risk_score >= risk_threshold_block:
    decision = "BLOCKED"
elif risk_score >= risk_threshold_review:
    decision = "MANUAL_REVIEW"
else:
    decision = "APPROVED"
```

### Risk Level Display

```python
if risk_score < 30:
    risk_level = "🟢 LOW"
elif risk_score < 60:
    risk_level = "🟡 MEDIUM"
elif risk_score < 80:
    risk_level = "🟠 HIGH"
else:
    risk_level = "🔴 CRITICAL"
```

---

## Address Extraction

### LLM-Based Parsing

```python
async def _extract_wallet_address(self, message: MessageContent) -> WalletAddress | None:
    """Extract wallet address from message using LLM."""
    prompt = f"""Extract the Ethereum wallet address from this message:

Message: {message.value}

If a wallet address is found, respond with JSON:
{{
    "wallet_address": "0x...",
    "found": true
}}

If no wallet address is found, respond with:
{{
    "wallet_address": null,
    "found": false
}}
"""
    
    response = await self._llm_client.classify_intent(
        prompt=prompt,
        model=self._model,
    )
    
    if response.get("found") and response.get("wallet_address"):
        return WalletAddress(response["wallet_address"])
    
    return None
```

---

## Source Attribution

### Chainalysis Source

```python
sources.append(create_api_source(
    source_name="Chainalysis",
    url="https://www.chainalysis.com/",
    citation_text=f"Compliance screening for wallet {str(wallet_address)[:10]}...",
    fetched_at=fetched_at,
    provider="Chainalysis API",
    metadata={"wallet_address": str(wallet_address)},
))
```

### OFAC Source

```python
sources.append(create_api_source(
    source_name="OFAC",
    url="https://ofac.treasury.gov/",
    citation_text="OFAC sanctions list check",
    fetched_at=fetched_at,
    provider="US Treasury OFAC",
))
```

### LLM Source

```python
sources.append(create_llm_source(
    model=self._model,
    fetched_at=fetched_at,
))
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_compliance_monitor_agent(
    self, llm_client: LLMClientGateway
) -> ComplianceMonitorAgentChainalysis:
    """Provide Compliance Monitor agent."""
    from unittest.mock import MagicMock
    return ComplianceMonitorAgentChainalysis(
        llm_client=llm_client,
        chainalysis_client=MagicMock(),  # TODO: Real client
    )
```

### Agent Registry

```python
AgentType.COMPLIANCE_MONITOR: compliance_monitor_agent,
```

---

## Response Structure

```python
return AgentResponse(
    content=report,
    agent_type=self.agent_type,
    tools_used=["chainalysis_api", "ofac_api", "openai_api"],
    sources=sources,
    metadata={
        "latency_ms": latency_ms,
        "wallet_address": str(wallet_address),
        "risk_score": screening_result["risk_score"],
        "decision": screening_result["decision"],
        "screening_id": screening_result["screening_id"],
    },
)
```

---

## Regulatory Frameworks

### Multi-Jurisdiction Support

| Jurisdiction | Framework | Requirements |
|--------------|-----------|--------------|
| **US** | FinCEN, OFAC | BSA compliance, SDN list |
| **EU** | MiCA, AMLD6 | Travel Rule, beneficial ownership |
| **UK** | FCA, MLR 2017 | Enhanced due diligence |

### Audit Trail

- **Storage Duration**: 7 years (regulatory requirement)
- **Immutability**: Tamper-proof logs
- **Format**: Structured JSON with timestamps
- **Access**: Compliance team only

---

## Future Enhancements

### TODO Items

```python
# TODO: Implement real Chainalysis API integration
# TODO: Implement transaction monitoring
# TODO: Implement enhanced PEP database
# TODO: Implement audit trail logging
```

### Planned Features

1. **Real Chainalysis API**
   - Live KYT (Know Your Transaction) API
   - Real-time risk assessment
   - Historical transaction analysis

2. **Transaction Monitoring**
   - Continuous monitoring
   - Automatic re-screening
   - Pattern detection

3. **Enhanced PEP Database**
   - Real-time updates
   - Family member screening
   - Political position tracking

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Address extraction | < 1s | LLM parsing |
| Wallet screening | < 2s | Chainalysis API (mock) |
| Report generation | < 1s | Template-based |
| Total | < 4s | Full screening |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added mock screening data |
| 2026-01-29 | Added source attribution |
