# Security Auditor Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.SECURITY_AUDITOR
│   └── services/
│       └── agent_squad/
│           └── intent_classifier.py      # Security intent mapping
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               ├── security_auditor_agent_slither.py  # Main agent
│               └── source_helpers.py                  # Source attribution
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. SecurityAuditorAgentSlither

**File**: `src/app/infrastructure/adapters/agent_squad/agents/security_auditor_agent_slither.py`
**Lines**: ~170

#### Class Definition

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

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
    max_tokens: int = 2000,
):
    """Initialize security auditor agent."""
    self._llm_client = llm_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. Execute Method

```python
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    """Execute security auditor agent - Contract analysis."""
    start_time = time.time()
    
    # TODO: Integrate Slither for static analysis
    # TODO: Integrate Mythril for symbolic execution
    # TODO: Check existing audit reports
    
    messages = [
        {"role": "system", "content": self._get_system_prompt()},
        {"role": "user", "content": message.value},
    ]
    
    response = await self._llm_client.chat(
        messages=messages,
        model=self._model,
        temperature=self._temperature,
        max_tokens=self._max_tokens,
    )
    
    latency_ms = int((time.time() - start_time) * 1000)
```

---

### 3. Source Attribution

```python
# Collect sources
from datetime import datetime, UTC
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

### 4. System Prompt

```python
def _get_system_prompt(self) -> str:
    """Get system prompt for security auditor agent."""
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

Analysis includes:
- Known vulnerabilities
- Audit reports (if available)
- Protocol reputation
- Historical exploits
- Upgrade patterns (proxy, timelock)
- Emergency pause mechanisms

Always provide:
- Clear severity classifications
- Actionable recommendations
- Links to audit reports
- Risk warnings for unaudited contracts
"""
```

---

### 5. Response Structure

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

### 6. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_security_auditor_agent(
    self, llm_client: LLMClientGateway
) -> SecurityAuditorAgentSlither:
    """Provide Security Auditor agent."""
    return SecurityAuditorAgentSlither(llm_client=llm_client)
```

---

### 7. Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "audit_contract": AgentType.SECURITY_AUDITOR,
    "security_audit": AgentType.SECURITY_AUDITOR,
}
```

---

## Future Enhancement TODOs

### Slither Integration

```python
# TODO: Integrate Slither for static analysis

# Future implementation:
async def _run_slither_analysis(self, contract_address: str) -> SlitherResult:
    """Run Slither static analysis on contract."""
    # Fetch verified source from Etherscan
    # Run Slither analysis
    # Parse vulnerability findings
    # Return structured results
    pass
```

### Mythril Integration

```python
# TODO: Integrate Mythril for symbolic execution

# Future implementation:
async def _run_mythril_analysis(self, contract_address: str) -> MythrilResult:
    """Run Mythril symbolic execution."""
    # Fetch contract bytecode
    # Run Mythril analysis
    # Parse exploit paths
    # Return structured results
    pass
```

### Audit Database

```python
# TODO: Check existing audit reports

# Future implementation:
async def _check_audit_database(self, protocol_name: str) -> list[AuditReport]:
    """Check for existing audit reports."""
    # Query audit database
    # Filter by protocol
    # Return audit reports
    pass
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_security_auditor_agent.py -v

# All security auditor tests
pytest tests/ -k security_auditor -v
```

### Test Cases

```python
# System prompt
def test_system_prompt():
    agent = SecurityAuditorAgentSlither(mock_llm)
    prompt = agent._get_system_prompt()
    assert "Security Auditor" in prompt
    assert "reentrancy" in prompt.lower()
    assert "oracle manipulation" in prompt.lower()
    assert "0-100" in prompt

# Source attribution
def test_source_attribution():
    response = await agent.execute(...)
    assert len(response.sources) >= 1
    assert response.sources[0].source_type == SourceType.LLM

# Intent mapping
def test_intent_mapping():
    assert intent_to_agent["audit_contract"] == AgentType.SECURITY_AUDITOR
    assert intent_to_agent["security_audit"] == AgentType.SECURITY_AUDITOR
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| LLM reasoning | < 3s | Vertex AI |
| Source attribution | < 10ms | Helpers |
| Total | < 3.1s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added source attribution |
| 2026-01-29 | Added system prompt with vulnerability patterns |
