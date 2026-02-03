# Security Auditor Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **SECURITY_AUDITOR** agent, which provides smart contract security analysis, vulnerability detection, and security best practices validation.

### Key Components

- **SecurityAuditorAgentSlither**: Agent Squad implementation
- **LLM Client**: Vertex AI for security reasoning
- **Source Helpers**: LLM source attribution

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SECURITY AUDITOR ARCHITECTURE                           │
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
                    │ SecurityAuditorSlither   │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Vertex AI          │ │  Slither (TODO) │ │  Mythril (TODO) │
│  (LLM Reasoning)    │ │  Static Analysis│ │  Symbolic Exec  │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Enterprise Agents
    SECURITY_AUDITOR = "security_auditor"  # Smart contract security
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "audit_contract": AgentType.SECURITY_AUDITOR,
    "security_audit": AgentType.SECURITY_AUDITOR,
}
```

---

## Infrastructure Layer

### SecurityAuditorAgentSlither

**File**: `src/app/infrastructure/adapters/agent_squad/agents/security_auditor_agent_slither.py`
**Lines**: ~170

```python
class SecurityAuditorAgentSlither:
    """
    Security Auditor Agent Slither implementation.
    
    Implements: AgentGateway
    
    Purpose: Smart contract security analysis
    
    Capabilities:
    - Smart contract vulnerability detection
    - Security best practices validation
    - Common vulnerability patterns (reentrancy, overflow, etc.)
    - Audit report summaries
    - Security recommendations
    
    Tools: Slither, Mythril (static analysis)
    Model: gemini-2.0-flash (security reasoning)
    Temperature: 0.1 (precision critical)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 35-46 | Initialize with LLM client |
| `agent_type` | 48-51 | Return AgentType.SECURITY_AUDITOR |
| `execute` | 53-123 | Main entry point |
| `is_available` | 125-127 | Availability check |
| `_get_system_prompt` | 129-169 | Security expertise prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,           # Precision critical
    max_tokens: int = 2000,             # Detailed analysis
):
```

---

## System Prompt Design

### Core Expertise Areas

```python
def _get_system_prompt(self) -> str:
    return """You are the Security Auditor, Anvil's smart contract security specialist.

Your expertise:
- Smart contract vulnerability detection
- Security best practices validation
- Common vulnerability patterns:
  - Reentrancy attacks
  - Integer overflow/underflow
  - Access control issues
  - Front-running vulnerabilities
  - Oracle manipulation
  - Flash loan attacks
```

### Security Scoring System

```python
For security analysis, provide:
- Security score (0-100)
  - 90-100: Excellent
  - 70-89: Good
  - 50-69: Moderate concerns
  - 30-49: High risk
  - 0-29: Critical vulnerabilities
- Vulnerability findings (severity: critical, high, medium, low)
- Best practices compliance
- Audit status (if available)
- Recommendations
```

### Analysis Coverage

```python
Analysis includes:
- Known vulnerabilities
- Audit reports (if available)
- Protocol reputation
- Historical exploits
- Upgrade patterns (proxy, timelock)
- Emergency pause mechanisms
```

### Required Output Elements

```python
Always provide:
- Clear severity classifications
- Actionable recommendations
- Links to audit reports
- Risk warnings for unaudited contracts
```

---

## Vulnerability Classification

### Critical Severity

| Vulnerability | Description | Impact |
|---------------|-------------|--------|
| Reentrancy | Recursive call exploitation | Total fund loss |
| Oracle Manipulation | Price feed exploitation | Fund extraction |
| Access Control | Missing permission checks | Unauthorized actions |
| Logic Errors | Flawed business logic | Protocol failure |

### High Severity

| Vulnerability | Description | Impact |
|---------------|-------------|--------|
| Integer Overflow | Arithmetic bounds exceeded | Incorrect calculations |
| Unchecked Returns | Ignored function returns | Silent failures |
| Timestamp Dependence | Block timestamp manipulation | Timing attacks |

### Medium Severity

| Vulnerability | Description | Impact |
|---------------|-------------|--------|
| Front-running | Transaction ordering attacks | Value extraction |
| DOS Attacks | Contract unavailability | Service disruption |
| Centralization | Single admin control | Trust issues |

### Low Severity

| Vulnerability | Description | Impact |
|---------------|-------------|--------|
| Gas Optimization | Inefficient gas usage | Higher costs |
| Code Quality | Readability issues | Maintenance burden |

---

## Source Attribution

### LLM Source

```python
from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
    create_llm_source,
    create_api_source,
)

sources = []
fetched_at = datetime.now(UTC)

# Add LLM source
model_name = response.get("model", "Unknown")
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))
```

### Future Sources (TODO)

```python
# TODO: Add Slither source when integrated
# sources.append(create_api_source(
#     source_name="Slither",
#     citation_text="Static analysis from Slither",
#     fetched_at=fetched_at,
#     provider="Slither Static Analyzer",
# ))

# TODO: Add audit database source when integrated
# sources.append(create_api_source(
#     source_name="Audit Reports",
#     url="https://github.com/trailofbits/publications",
#     citation_text="Security audit reports database",
#     fetched_at=fetched_at,
# ))
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_security_auditor_agent(
    self, llm_client: LLMClientGateway
) -> SecurityAuditorAgentSlither:
    """Provide Security Auditor agent."""
    return SecurityAuditorAgentSlither(llm_client=llm_client)
```

### Agent Registry

```python
# Agent type mapping
AgentType.SECURITY_AUDITOR: security_auditor_agent,
```

---

## Security Analysis Flow

### Current Implementation

```
1. User Query: "Is Aave safe to use?"
   ↓
2. Intent Classification
   → security_audit / audit_contract
   ↓
3. Supervisor Routes to security_auditor
   ↓
4. SecurityAuditorAgentSlither.execute()
   ↓
5. Build LLM Prompt
   - System prompt with security expertise
   - User query
   ↓
6. LLM Analysis (Vertex AI)
   - Vulnerability patterns
   - Security score
   - Recommendations
   ↓
7. Source Attribution
   - LLM source
   ↓
8. Return AgentResponse
```

### Future Enhancement (TODO)

```
1. User Query: "Analyze 0x1234..."
   ↓
2. Contract Address Validation
   → Verify on Etherscan
   ↓
3. Static Analysis
   → Slither vulnerability scan
   ↓
4. Symbolic Execution
   → Mythril deep analysis
   ↓
5. Audit Database Check
   → Query known audits
   ↓
6. LLM Contextualization
   → Explain findings in natural language
   ↓
7. Generate Recommendations
   → Specific, actionable advice
```

---

## Response Structure

```python
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["openai_api"],  # TODO: Add Slither, Mythril
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
    },
)
```

---

## Future Enhancements

### TODO Items

```python
# TODO: Integrate Slither for static analysis
# TODO: Integrate Mythril for symbolic execution
# TODO: Check existing audit reports
```

### Planned Features

1. **Slither Integration**
   - Static analysis of Solidity code
   - Automatic vulnerability detection
   - Code quality checks

2. **Mythril Integration**
   - Symbolic execution
   - Deep vulnerability analysis
   - Exploit path detection

3. **Audit Database**
   - Query Trail of Bits audits
   - OpenZeppelin reports
   - Certora verification results

4. **On-Chain Verification**
   - Etherscan verification status
   - Bytecode analysis
   - Source code comparison

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| LLM reasoning | < 3s | Vertex AI |
| Total | < 3s | All combined |

### Future Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Slither analysis | < 30s | Static analysis |
| Mythril analysis | < 60s | Symbolic execution |
| Audit lookup | < 1s | Database query |
| Total | < 90s | Full analysis |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added system prompt with vulnerability patterns |
| 2026-01-29 | Added source attribution |
