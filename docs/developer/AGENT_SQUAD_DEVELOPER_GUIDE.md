# Agent Squad Developer Guide

**Document**: AgentSquad-DeveloperGuide  
**Date**: December 1, 2025  
**Version**: 1.0  
**Audience**: Developers

---

## 🏗️ Architecture Overview

Agent Squad follows **Hexagonal Architecture** (Clean Architecture) with strict layer separation.

### Layer Structure

```
┌─────────────────────────────────────────────┐
│         Presentation Layer (HTTP)           │
│   Controllers, Request/Response Schemas     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Application Layer (Use Cases)       │
│    Interactors, Commands, Queries           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Domain Layer (Business Logic)       │
│  Entities, Services, Value Objects, Ports   │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│      Infrastructure Layer (Adapters)        │
│  Agents, Database, External APIs, Redis     │
└─────────────────────────────────────────────┘
```

**Dependencies**: Domain ← Infrastructure (Dependency Inversion)

---

## 📂 Project Structure

```
src/app/
├── domain/
│   ├── entities/agent_squad/         # Domain entities
│   │   ├── agent_telemetry.py
│   │   ├── compliance_screening_log.py
│   │   ├── multisig_proposal.py
│   │   └── crisis_event.py
│   ├── services/agent_squad/         # Domain services
│   │   ├── agent_orchestrator.py
│   │   ├── intent_classifier.py
│   │   ├── context_manager.py
│   │   └── supervisor_coordinator.py
│   ├── ports/agent_squad/            # Interfaces
│   │   ├── agent_gateway.py
│   │   ├── intent_classifier_gateway.py
│   │   └── ... (5 ports)
│   ├── value_objects/agent_squad/    # Value objects
│   │   ├── agent_squad_config.py
│   │   └── conversation_context.py
│   └── enums/
│       └── agent_type.py             # AgentType enum (18)
├── infrastructure/
│   ├── adapters/agent_squad/         # Infrastructure adapters
│   │   ├── agents/                   # Agent implementations
│   │   │   ├── chat_agent_openai.py
│   │   │   ├── hunter_ai_agent_openai.py
│   │   │   ├── ... (10 core agents)
│   │   │   ├── enterprise/           # Enterprise agents
│   │   │   │   ├── compliance_monitor_agent_chainalysis.py
│   │   │   │   └── ... (4 agents)
│   │   │   └── advanced/             # Advanced agents
│   │   │       ├── bridge_crosschain_agent_axelar.py
│   │   │       └── ... (4 agents)
│   │   ├── llm_client_openai.py
│   │   ├── context_storage_redis.py
│   │   └── feature_flags_config.py
│   └── persistence_sqla/
│       └── migrations/versions/
│           └── 20251201_004_add_agent_squad_tables.py
└── presentation/http/
    ├── controllers/chat/
    │   └── router.py                 # API endpoints
    └── schemas/
        └── chat.py                   # Request/response schemas
```

---

## 🔧 Adding a New Agent

### Step 1: Define Agent Type (Domain)

```python
# src/app/domain/enums/agent_type.py

class AgentType(Enum):
    # ... existing agents ...
    MY_NEW_AGENT = "my_new_agent"
```

### Step 2: Create Agent Implementation (Infrastructure)

```python
# src/app/infrastructure/adapters/agent_squad/agents/my_new_agent.py

from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse

class MyNewAgent:
    """
    My New Agent implementation.
    
    Implements: AgentGateway
    """
    
    def __init__(self, llm_client: LLMClientOpenAI):
        self._llm_client = llm_client
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.MY_NEW_AGENT
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        # Your agent logic here
        pass
    
    async def is_available(self) -> bool:
        return True
```

### Step 3: Add Intent Mapping (Domain)

```python
# src/app/domain/services/agent_squad/intent_classifier.py

INTENT_AGENT_MAP = {
    # ... existing intents ...
    "my_new_intent": AgentType.MY_NEW_AGENT,
}
```

### Step 4: Add Configuration (Config)

```toml
# config/local/config.toml

[agent_squad.agents.my_new_agent]
enabled = true
model = "gpt-4o"
temperature = 0.5
max_tokens = 1500
```

### Step 5: Register in DI Container

```python
# src/app/setup/ioc/infrastructure.py

@provide
def get_my_new_agent(
    llm_client: LLMClientOpenAI,
) -> MyNewAgent:
    return MyNewAgent(llm_client=llm_client)
```

---

## 🧪 Testing Your Agent

```python
# tests/integration/agent_squad/test_my_new_agent.py

import pytest
from app.infrastructure.adapters.agent_squad.agents.my_new_agent import MyNewAgent

@pytest.mark.asyncio
async def test_my_new_agent_execution(mock_llm_client):
    agent = MyNewAgent(llm_client=mock_llm_client)
    
    response = await agent.execute(
        conversation_id=ConversationId(uuid4()),
        message=MessageContent("Test message"),
        context=ConversationContext(),
    )
    
    assert response.agent_type == AgentType.MY_NEW_AGENT
    assert response.content is not None
```

---

## 🎨 Agent Design Patterns

### Pattern 1: Simple LLM Agent

```python
async def execute(self, conversation_id, message, context):
    start_time = time.time()
    
    # Build messages
    messages = [
        {"role": "system", "content": self._get_system_prompt()},
        {"role": "user", "content": message.value},
    ]
    
    # Call LLM
    response = await self._llm_client.chat(
        messages=messages,
        model=self._model,
        temperature=self._temperature,
        max_tokens=self._max_tokens,
    )
    
    # Return response
    return AgentResponse(
        content=response["content"],
        agent_type=self.agent_type,
        tools_used=["openai_api"],
        metadata={
            "latency_ms": int((time.time() - start_time) * 1000),
            "tokens_used": response.get("tokens_used"),
        },
    )
```

### Pattern 2: Multi-Tool Agent (External APIs)

```python
async def execute(self, conversation_id, message, context):
    start_time = time.time()
    
    # Step 1: Parse intent
    intent = await self._parse_intent(message)
    
    # Step 2: Call external API
    data = await self._external_api_call(intent)
    
    # Step 3: Format response
    formatted = await self._format_response(data)
    
    return AgentResponse(
        content=formatted,
        agent_type=self.agent_type,
        tools_used=["openai_api", "external_api"],
        metadata={
            "latency_ms": int((time.time() - start_time) * 1000),
            "api_data": data,
        },
    )
```

### Pattern 3: Transaction Agent

```python
async def execute(self, conversation_id, message, context):
    start_time = time.time()
    
    # Step 1: Parse transaction intent
    tx_intent = await self._parse_transaction(message)
    
    # Step 2: Validate (limits, balance)
    validation = await self._validate_transaction(tx_intent)
    
    # Step 3: Get quote
    quote = await self._get_quote(tx_intent)
    
    # Step 4: Request user confirmation
    confirmation_message = self._build_confirmation_request(quote)
    
    # NOTE: Actual execution happens in separate endpoint
    # after user confirms
    
    return AgentResponse(
        content=confirmation_message,
        agent_type=self.agent_type,
        tools_used=["privy_wallet", "1inch_api"],
        metadata={
            "latency_ms": int((time.time() - start_time) * 1000),
            "requires_confirmation": True,
            "transaction_intent": tx_intent,
        },
    )
```

---

## 🔌 External Integrations

### OpenAI Integration

```python
# Already implemented: LLMClientOpenAI

from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI

llm_client = LLMClientOpenAI(api_key="sk-...")

response = await llm_client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4o-mini",
    temperature=0.7,
)
```

### Chainalysis Integration (TODO)

```python
# Example: ChainalysisClient

class ChainalysisClient:
    async def screen_wallet(self, address: str) -> dict:
        # Call Chainalysis API
        pass
```

### Gnosis Safe Integration (TODO)

```python
# Example: GnosisSafeClient

class GnosisSafeClient:
    async def create_proposal(self, safe_address: str, tx_data: dict) -> str:
        # Call Gnosis Safe API
        pass
```

---

## 📊 Telemetry & Monitoring

### Agent Telemetry

Every agent execution is tracked:

```python
# Automatically logged to agent_telemetry table

{
    "agent_type": "chat",
    "conversation_id": "uuid",
    "latency_ms": 450,
    "tokens_used": 150,
    "tools_used": ["openai_api"],
    "success": true,
    "intent_classification": "general_chat",
    "intent_confidence": 0.95,
}
```

### Performance Monitoring

```python
# Track agent performance

from app.domain.entities.agent_squad.agent_telemetry import AgentTelemetry

telemetry = AgentTelemetry.create(
    agent_type=AgentType.CHAT,
    conversation_id=conversation_id,
    latency_ms=450,
    tokens_used=150,
    tools_used=["openai_api"],
    success=True,
)

await telemetry_repository.save(telemetry)
```

---

## 🔧 Configuration

### Agent Configuration

```toml
# config/local/config.toml

[agent_squad.agents.my_new_agent]
enabled = true              # Enable/disable agent
model = "gpt-4o"           # LLM model
temperature = 0.5          # Sampling temperature
max_tokens = 1500          # Max response tokens
api_key = "${API_KEY}"     # External API key (optional)
```

### Environment Variables

```bash
# .env

OPENAI_API_KEY=sk-...
CHAINALYSIS_API_KEY=...
GNOSIS_SAFE_API_KEY=...
```

---

## 🚀 Deployment

### Local Development

```bash
# 1. Install dependencies
uv pip install -e '.[dev,test]'

# 2. Start database
make up.db

# 3. Run migrations
alembic upgrade head

# 4. Start Redis
make up.redis

# 5. Start server
make start
```

### Production Deployment

```bash
# 1. Build Docker image
docker build -t agent-squad:latest .

# 2. Deploy to AWS ECS/EKS
# (See deployment guide)

# 3. Configure monitoring
# - Sentry (error tracking)
# - Datadog (performance)
# - CloudWatch (infrastructure)
```

---

## 🧪 Testing

### Run All Tests

```bash
make code.test
```

### Run Specific Test Suite

```bash
# Unit tests
pytest tests/unit/agent_squad/

# Integration tests
pytest tests/integration/agent_squad/

# E2E tests
pytest tests/e2e/agent_squad/

# Load tests
pytest tests/load/agent_squad/ -m load
```

---

## 📚 Additional Resources

### Documentation
- User Guide: `docs/user/AGENT_SQUAD_USER_GUIDE.md`
- Security Audit: `docs/security/AGENT_SQUAD_SECURITY_AUDIT.md`
- Performance Benchmarks: `docs/performance/AGENT_SQUAD_BENCHMARKS.md`

### Implementation Plans
- Full Plan: `docs/plans/AGENT_SQUAD_18_IMPLEMENTATION_PLAN.md`
- Progress Summary: `docs/specs/AGENT_SQUAD_PROGRESS_SUMMARY.md`

### Specifications
- Integration Spec: `docs/specs/integrations/AGENT_SQUAD_INTEGRATION_SPEC.md`
- Use Cases: `docs/USE_CASES_EXAMPLES.md`

---

## 🆘 Troubleshooting

### Agent Not Responding

1. Check agent is enabled in config
2. Verify API keys are set
3. Check logs for errors
4. Verify database connection

### Intent Classification Issues

1. Check confidence threshold (default: 0.85)
2. Review conversation context
3. Check LLM model configuration
4. Verify intent categories mapping

### Performance Issues

1. Check database indexes
2. Verify Redis connection
3. Monitor LLM token usage
4. Check concurrent request count

---

**Need help?** Contact the development team or open an issue on GitHub.

---
