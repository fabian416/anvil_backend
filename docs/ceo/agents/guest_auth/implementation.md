# Guest Auth Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.GUEST_AUTH
│   └── services/
│       └── agent_squad/
│           └── guest_supervisor.py       # Guest routing
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               └── guest_auth_agent.py   # Main agent
│
├── application/
│   ├── guest/
│   │   └── i18n/
│   │       └── translations.py           # Multi-language templates
│   └── chat/
│       └── services/
│           └── knowledge_injector.py     # Knowledge context
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. GuestAuthAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/guest_auth_agent.py`
**Lines**: ~346

#### Class Definition

```python
class GuestAuthAgent:
    """
    Guest Auth Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Handle authentication requirements for restricted features
    
    Capabilities:
    - Detect which restricted feature user is asking about
    - Use knowledge base to understand user's intent
    - Generate context-aware registration messages using LLM
    - Return appropriate custom registration message
    - Support multiple languages
    - Provide clear sign-in instructions
    
    Model: gemini-2.0-flash (fast, cost-effective)
    Temperature: 0.3 (consistent responses)
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 40-52 | Initialize with LLM client |
| `agent_type` | 54-57 | Return AgentType.GUEST_AUTH |
| `execute` | 59-161 | Main entry point |
| `_detect_knowledge_intent` | 163-196 | Map query to knowledge intent |
| `_format_knowledge_context` | 198-228 | Format knowledge dict |
| `_generate_contextual_message` | 230-289 | LLM contextual generation |
| `_detect_restricted_feature` | 291-311 | Fallback feature detection |
| `_get_custom_message` | 313-341 | Get static template |
| `is_available` | 343-345 | Always returns True |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 500,
):
    self._llm_client = llm_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
    self._knowledge_injector = None  # Lazy load
```

---

### 2. Translations

**File**: `src/app/application/guest/i18n/translations.py`
**Lines**: ~299

#### Message Categories

| Category | Purpose |
|----------|---------|
| `GUEST_REGISTRATION_MESSAGES` | Feature-specific auth prompts |
| `GUEST_CTA_MESSAGES` | Call-to-action buttons |
| `GUEST_DEMO_DISCLAIMER` | Demo mode notice |
| `GUEST_RATE_LIMIT_MESSAGES` | Rate limit warning |
| `GUEST_WELCOME_MESSAGES` | Initial welcome |
| `RESTRICTED_INTENT_TO_REASON` | Intent to template mapping |

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_guest_auth_agent(self, llm_client: LLMClientGateway) -> GuestAuthAgent:
    """Provide Guest Auth agent for handling authentication requirements."""
    return GuestAuthAgent(llm_client=llm_client)
```

---

## Execute Method Implementation

### Main Flow

```python
# Lines 59-161
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    start_time = time.time()
    
    # Get language from context
    language = conversation_context.user_metadata.get("language", "en")
    
    custom_message = None
    knowledge_used = False
    tokens_used = 0
```

### Knowledge Loading

```python
# Lines 76-107
try:
    # Load knowledge injector lazily
    if self._knowledge_injector is None:
        from app.application.chat.services.knowledge_injector import KnowledgeInjector
        self._knowledge_injector = KnowledgeInjector()
    
    # Detect intent for knowledge retrieval
    detected_intent = self._detect_knowledge_intent(message.value)
    
    # Get relevant knowledge from knowledge base
    if self._knowledge_injector:
        knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(
            user_query=message.value,
            detected_intent=detected_intent,
            user_type="guest",
        )
        
        if knowledge_dict:
            knowledge_context = self._format_knowledge_context(knowledge_dict)
            knowledge_used = True
```

### Contextual Message Generation

```python
# Lines 109-117
# Generate context-aware message using LLM
if knowledge_context:
    custom_message = await self._generate_contextual_message(
        message.value,
        knowledge_context,
        language,
        conversation_context,
    )
    tokens_used = 100  # Estimate for LLM call
```

### Fallback to Static Message

```python
# Lines 121-124
# Fallback to simple message if LLM generation failed
if not custom_message:
    restricted_feature = self._detect_restricted_feature(message.value)
    custom_message = self._get_custom_message(restricted_feature, conversation_context)
```

---

## Knowledge Intent Detection

```python
# Lines 163-196
def _detect_knowledge_intent(self, query: str) -> str:
    query_lower = query.lower()
    
    # Lending queries (Morpho) - highest priority
    if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault", "supply"]):
        return "LENDING_MORPHO"
    
    # Swap queries
    if any(kw in query_lower for kw in ["swap", "exchange", "trade tokens"]):
        return "SWAP"
    
    # Buy queries
    if any(kw in query_lower for kw in ["buy crypto", "purchase", "on-ramp"]):
        return "BUY"
    
    # Send queries
    if any(kw in query_lower for kw in ["send crypto", "transfer tokens"]):
        return "SEND"
    
    # Portfolio queries
    if any(kw in query_lower for kw in ["portfolio", "balance", "holdings"]):
        return "PORTFOLIO"
    
    # Wallet queries
    if any(kw in query_lower for kw in ["wallet", "address", "receive"]):
        return "WALLET"
    
    # Activity queries
    if any(kw in query_lower for kw in ["transactions", "activity", "history"]):
        return "ACTIVITY"
    
    return "execute_action"  # Default
```

---

## LLM Contextual Generation

```python
# Lines 230-289
async def _generate_contextual_message(
    self,
    user_query: str,
    knowledge_context: str,
    language: str,
    conversation_context: ConversationContext,
) -> str:
    # Get CTA message
    from app.application.guest.i18n.translations import get_cta_message
    cta = get_cta_message(language)
    
    # Build prompt for LLM
    system_prompt = f"""You are a helpful assistant that explains why users 
need to sign up for Anvil to use specific features.

Based on the user's query and the feature information provided, create a 
brief, friendly registration message that:
1. Acknowledges what the user wants to do
2. Explains why they need an account (briefly)
3. Ends with the CTA: "👉 {cta}"

Keep it concise (2-3 sentences max). Be specific about what they'll be able to do.
Respond in {language.upper()} language.
"""
    
    user_prompt = f"""User query: "{user_query}"

Feature information:
{knowledge_context}

Generate a registration message:"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = await self._llm_client.chat(
        messages=messages,
        model=self._model,
        temperature=self._temperature,
        max_tokens=self._max_tokens,
    )
    
    return response.strip() if response else None
```

---

## Feature Detection (Fallback)

```python
# Lines 291-311
def _detect_restricted_feature(self, message: str) -> str:
    message_lower = message.lower()
    
    if any(kw in message_lower for kw in ["my balance", "wallet balance"]):
        return "balance"
    elif any(kw in message_lower for kw in ["my transactions", "transaction history"]):
        return "activity"
    elif any(kw in message_lower for kw in ["my address", "wallet address"]):
        return "receive"
    elif any(kw in message_lower for kw in ["buy crypto", "purchase bitcoin"]):
        return "buy"
    elif any(kw in message_lower for kw in ["send crypto", "transfer tokens"]):
        return "send"
    elif any(kw in message_lower for kw in ["my portfolio", "my holdings"]):
        return "portfolio"
    elif any(kw in message_lower for kw in ["lending", "lend", "morpho"]):
        return "lending"
    else:
        return "general"
```

---

## Static Message Template

```python
# Lines 313-341
def _get_custom_message(self, feature: str, context: ConversationContext) -> str:
    language = context.user_metadata.get("language", "en")
    
    from app.application.guest.i18n.translations import get_registration_message
    
    feature_to_reason = {
        "balance": "wallet_access",
        "activity": "transaction_history",
        "receive": "wallet_address",
        "buy": "buy_crypto",
        "send": "send_crypto",
        "portfolio": "portfolio_access",
        "lending": "execute_deposit",
        "general": "execute_action",
    }
    
    reason = feature_to_reason.get(feature, "execute_action")
    messages = get_registration_message(reason, language)
    message = messages.get(language, messages.get("en", ""))
    
    # Add CTA
    from app.application.guest.i18n.translations import get_cta_message
    cta = get_cta_message(language)
    
    return f"{message}\n\n👉 {cta}"
```

---

## Response Structure

### AgentResponse

```python
# Lines 149-161
return AgentResponse(
    content=custom_message,
    agent_type=self.agent_type,
    tools_used=["auth_detection", "knowledge_base"] if knowledge_used else ["auth_detection"],
    sources=sources,
    metadata={
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
        "model": self._model,
        "knowledge_used": knowledge_used,
        "provider": "vertex_ai" if "gemini" in self._model.lower() else "deepinfra",
    },
)
```

---

## Translation Helper Functions

```python
# From translations.py

def get_registration_message(reason: str, language: str = "en") -> dict[str, str]:
    """Get registration required message with all languages."""
    return GUEST_REGISTRATION_MESSAGES.get(
        reason, GUEST_REGISTRATION_MESSAGES["execute_action"]
    )

def get_cta_message(language: str = "en") -> str:
    """Get call-to-action message for specified language."""
    return GUEST_CTA_MESSAGES.get(language, GUEST_CTA_MESSAGES["en"])

def get_reason_for_intent(intent: str) -> str:
    """Get registration reason for a restricted intent."""
    return RESTRICTED_INTENT_TO_REASON.get(intent.upper(), "execute_action")
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_guest_auth_agent.py -v

# All guest auth tests
pytest tests/ -k guest_auth -v
```

### Test Cases

```python
# Feature detection
def test_feature_detection():
    agent = GuestAuthAgent(mock_llm)
    assert agent._detect_restricted_feature("my portfolio") == "portfolio"
    assert agent._detect_restricted_feature("lend 100 USDC") == "lending"
    assert agent._detect_restricted_feature("buy crypto") == "buy"

# Knowledge intent
def test_knowledge_intent():
    assert agent._detect_knowledge_intent("Supply USDC to Morpho") == "LENDING_MORPHO"
    assert agent._detect_knowledge_intent("swap ETH") == "SWAP"
    assert agent._detect_knowledge_intent("my balance") == "PORTFOLIO"

# Multi-language CTA
def test_cta_messages():
    assert get_cta_message("en") == "Sign Up Free"
    assert get_cta_message("es") == "Regístrate Gratis"
    assert get_cta_message("pt") == "Cadastre-se Grátis"
    assert get_cta_message("zh") == "免费注册"

# Template retrieval
def test_template_retrieval():
    messages = get_registration_message("portfolio_access", "en")
    assert "Portfolio Dashboard" in messages["en"]
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Knowledge loading | < 100ms | JSON files |
| Contextual (LLM) | < 500ms | Vertex AI |
| Fallback (static) | < 50ms | Dict lookup |
| Total | < 600ms | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added knowledge integration |
| 2026-01-29 | Added LLM contextual generation |
| 2026-01-29 | Added multi-language support |
