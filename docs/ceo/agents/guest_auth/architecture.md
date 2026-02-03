# Guest Auth Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **GUEST_AUTH** agent, which handles authentication requirements for restricted features when guest users attempt actions that require login.

### Key Components

- **GuestAuthAgent**: Agent Squad implementation
- **KnowledgeInjector**: Context retrieval from knowledge base
- **Translations**: Multi-language message templates
- **LLM Client**: Contextual message generation

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GUEST AUTH ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Guest Supervisor       │
                    │  (Routing for Guests)    │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   GuestAuthAgent         │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  KnowledgeInjector  │ │    Vertex AI    │ │   Translations  │
│  (JSON Knowledge)   │ │  (LLM Context)  │ │   (i18n)        │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    GUEST_AUTH = "guest_auth"  # Guest authentication prompts
```

---

## Infrastructure Layer

### GuestAuthAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/guest_auth_agent.py`
**Lines**: ~346

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

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 59-161 | Main entry point |
| `_detect_knowledge_intent()` | 163-196 | Map query to knowledge intent |
| `_format_knowledge_context()` | 198-228 | Format knowledge for LLM |
| `_generate_contextual_message()` | 230-289 | Generate with LLM |
| `_detect_restricted_feature()` | 291-311 | Fallback feature detection |
| `_get_custom_message()` | 313-341 | Get static template |
| `is_available()` | 343-345 | Availability check |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,           # Consistent responses
    max_tokens: int = 500,              # Short messages
):
    self._knowledge_injector = None     # Lazy loaded
```

---

## Guest Supervisor Integration

### Routing Rules

```python
# From guest_supervisor.py

# ACTION REQUESTS → "guest_auth" agent (REQUIRES LOGIN):
"swap 100 USDC to ETH" → guest_auth (transaction - needs wallet)
"lend 100 USDC" → guest_auth (lending - needs wallet)
"buy crypto" → guest_auth (buying - needs account)
"my balance" → guest_auth (requires wallet)
"my portfolio" → guest_auth (requires wallet)
"my transactions" → guest_auth (requires login)

# Information queries → Can answer directly (other agents)
"what is DeFi?" → knowledge (no login needed)
"BTC price" → hunter_ai (no login needed)
```

### Routing Examples

```python
# Transaction actions
"swap 100 USDC to ETH" → {
    "tasks":[{"agent_type":"guest_auth",
              "task_description":"Handle swap transaction request - requires login",
              "depends_on":[]}]
}

# Wallet queries
"my balance" → {
    "tasks":[{"agent_type":"guest_auth",
              "task_description":"Handle restricted feature - requires login",
              "depends_on":[]}]
}

# Lending actions
"lend 100 usdc" → {
    "tasks":[{"agent_type":"guest_auth",
              "task_description":"Handle lending transaction - requires login",
              "depends_on":[]}]
}
```

---

## Knowledge Integration

### Knowledge Intent Detection

```python
def _detect_knowledge_intent(self, query: str) -> str:
    query_lower = query.lower()
    
    # Lending queries (Morpho) - highest priority
    if any(kw in query_lower for kw in ["lending", "lend", "morpho", "supply", "deposit"]):
        return "LENDING_MORPHO"
    
    # Swap queries
    if any(kw in query_lower for kw in ["swap", "exchange", "trade tokens"]):
        return "SWAP"
    
    # Buy queries
    if any(kw in query_lower for kw in ["buy crypto", "purchase"]):
        return "BUY"
    
    # Send queries
    if any(kw in query_lower for kw in ["send crypto", "transfer"]):
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

### Knowledge Context Formatting

```python
def _format_knowledge_context(self, knowledge_dict: dict) -> str:
    context_parts = []
    
    if "feature_name" in knowledge_dict:
        context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
    
    if "tagline" in knowledge_dict:
        context_parts.append(f"Tagline: {knowledge_dict['tagline']}")
    
    if "description" in knowledge_dict:
        context_parts.append(f"Description: {knowledge_dict['description']}")
    
    if "features" in knowledge_dict:
        features = knowledge_dict["features"][:5]  # First 5
        context_parts.append(f"Features: {', '.join(features)}")
    
    return "\n".join(context_parts)
```

---

## LLM Contextual Generation

### System Prompt

```python
system_prompt = f"""You are a helpful assistant that explains why users need 
to sign up for Anvil to use specific features.

Based on the user's query and the feature information provided, create a 
brief, friendly registration message that:
1. Acknowledges what the user wants to do
2. Explains why they need an account (briefly)
3. Ends with the CTA: "👉 {cta}"

Keep it concise (2-3 sentences max). Be specific about what they'll be able to do.
Respond in {language.upper()} language.

Example for "Supply 1000 USDC to Morpho":
"To supply USDC to Morpho vaults and start earning yield, you'll need to 
create an account. This allows you to securely connect your wallet and 
execute DeFi transactions.

👉 {cta}"
"""
```

### User Prompt

```python
user_prompt = f"""User query: "{user_query}"

Feature information:
{knowledge_context}

Generate a registration message:"""
```

---

## Translation System

### Message Templates

**File**: `src/app/application/guest/i18n/translations.py`

```python
GUEST_REGISTRATION_MESSAGES = {
    "portfolio_access": {
        "en": "💼 **Unlock Your Complete Portfolio Dashboard**...",
        "es": "💼 **Desbloquea Tu Panel de Portafolio Completo**...",
        "pt": "💼 **Desbloqueie Seu Painel Completo de Portfólio**...",
        "zh": "💼 **解锁您的完整投资组合仪表板**...",
    },
    "wallet_access": {
        "en": "🔐 **Wallet Access Required**...",
        "es": "🔐 **Acceso a Billetera Requerido**...",
        "pt": "🔐 **Acesso à Carteira Necessário**...",
        "zh": "🔐 **需要钱包访问权限**...",
    },
    # ... more templates
}
```

### CTA Messages

```python
GUEST_CTA_MESSAGES = {
    "en": "Sign Up Free",
    "es": "Regístrate Gratis",
    "pt": "Cadastre-se Grátis",
    "zh": "免费注册",
}
```

---

## Feature to Template Mapping

```python
feature_to_reason = {
    "balance": "wallet_access",
    "activity": "transaction_history",
    "receive": "wallet_address",
    "buy": "buy_crypto",
    "send": "send_crypto",
    "portfolio": "portfolio_access",
    "lending": "execute_deposit",
    "general": "execute_action",  # Fallback
}
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_guest_auth_agent(self, llm_client: LLMClientGateway) -> GuestAuthAgent:
    """Provide Guest Auth agent for handling authentication requirements."""
    return GuestAuthAgent(llm_client=llm_client)
```

---

## Source Attribution

```python
sources = [
    SourceInfo(
        source_type=SourceType.LLM,
        source_name=self._model,
        citation_text=f"Generated by {self._model}" + 
                      (" with knowledge base" if knowledge_used else ""),
        fetched_at=fetched_at,
        provider="Vertex AI" if "gemini" in self._model.lower() else "DeepInfra",
        metadata={
            "model": self._model,
            "knowledge_used": knowledge_used,
            "contextual": knowledge_used,
        },
    )
]
```

---

## Testing

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
    assert agent._detect_knowledge_intent("Supply 1000 USDC to Morpho") == "LENDING_MORPHO"
    assert agent._detect_knowledge_intent("swap ETH to USDC") == "SWAP"

# Multi-language
def test_multi_language():
    messages = get_registration_message("buy_crypto", "es")
    assert "Cuenta Requerida" in messages["es"]
```

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Context-aware (LLM) | < 500ms | Vertex AI |
| Fallback (static) | < 50ms | Static templates |
| Knowledge loading | < 100ms | JSON files |
| Total | < 600ms | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added knowledge integration |
| 2026-01-29 | Added LLM contextual generation |
| 2026-01-29 | Added multi-language support |
