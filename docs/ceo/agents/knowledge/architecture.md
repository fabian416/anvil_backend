# Knowledge Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **KNOWLEDGE** agent, providing educational content about DeFi, crypto, blockchain, and Anvil platform features with dynamic knowledge injection.

### Key Components

- **KnowledgeAgent**: Core agent for educational queries
- **KnowledgeInjector**: Dynamic knowledge loading from JSON files
- **KnowledgeCompressor**: Token optimization for large contexts
- **Intent Detection**: Maps queries to knowledge categories

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE AGENT ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   conversations_router   │
                    │  POST /{id}/messages     │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Application Layer      │
                    │   (Supervisor Command)   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Supervisor Coordinator  │
                    │  (Guest / Authenticated) │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     KnowledgeAgent       │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
    │ KnowledgeInject │ │ Knowledge Base│ │    Vertex AI    │
    │ (App Layer)     │ │ (JSON files)  │ │    (LLM)        │
    └─────────────────┘ └───────────────┘ └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    KNOWLEDGE = "knowledge"  # Educational and knowledge queries
```

### Agent Gateway Interface

**File**: `src/app/domain/ports/agent_squad/agent_gateway.py`

```python
class AgentGateway(Protocol):
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse: ...
```

---

## Application Layer

### KnowledgeInjector

**File**: `src/app/application/chat/services/knowledge_injector.py`

```python
class KnowledgeInjector:
    """
    Dynamically selects and injects relevant knowledge into LLM prompts 
    based on user queries and detected intents.
    """
    
    def __init__(self, knowledge_base_path: Path | None = None):
        # Default to project root / anvil_knowledge
        self.knowledge_base_path = knowledge_base_path
        self.features_path = knowledge_base_path / "features"
        self._cache: Dict[str, Dict[str, Any]] = {}  # Cached JSON files
    
    def get_knowledge_for_intent(
        self,
        user_query: str,
        detected_intent: str,
        user_type: str = "user",  # "user" or "investor"
    ) -> Dict[str, Any]:
        """Get relevant knowledge sections based on intent."""
        ...
```

### KnowledgeFile Enum

```python
class KnowledgeFile(str, Enum):
    """Available knowledge base files"""
    OVERVIEW = "overview"
    SWAP = "swap"
    HUNTER_AI = "hunter_ai"
    ULTRA = "ultra"
    SHORTCUTS = "shortcuts"
    PORTFOLIO = "portfolio"
    WALLET = "wallet"
    LENDING_MORPHO = "lending_morpho"
    GAS_OPTIMIZER = "gas_optimizer"
    RISK_ANALYZER = "risk_analyzer"
    MONEY_MARKET = "money_market"
```

### Supervisor Integration

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
"""
6. SWAP INFORMATION (what swaps are available - educational):
   - "what type of swaps can I do" → "knowledge" agent
   - "can I swap ETH" → "knowledge" agent

15. EDUCATIONAL:
    - DeFi explanations → "knowledge"
    - Protocol comparisons → "knowledge"
    - Swap capabilities → "knowledge"
"""
```

---

## Infrastructure Layer

### KnowledgeAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/knowledge_agent.py`

**Lines**: ~587

```python
class KnowledgeAgent:
    """
    Knowledge Anvil Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Educational queries, Anvil knowledge, DeFi/crypto explanations
    
    Capabilities:
    - Answer "what is X?" questions
    - Explain Anvil platform features
    - Provide educational content about DeFi/crypto
    - Access dynamic knowledge base (JSON files)
    - Multi-language support
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.5 (more factual, less creative)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 69-199 | Main entry point |
| `is_available()` | 201-204 | Availability check |
| `_detect_knowledge_intent()` | 206-265 | Intent detection |
| `_format_knowledge_context()` | 267-322 | Format JSON as context |
| `_build_messages()` | 324-375 | Build LLM messages |
| `_get_system_prompt()` | 377-586 | System prompt with rules |

---

## Knowledge Base Structure

### Directory Layout

```
anvil_knowledge/
└── features/
    ├── overview.json        # Anvil platform overview
    ├── swap.json            # Token swap features
    ├── hunter_ai.json       # Hunter AI capabilities
    ├── ultra.json           # ULTRA arbitrage bot
    ├── portfolio.json       # Portfolio management
    ├── wallet.json          # Wallet management
    ├── lending_morpho.json  # Morpho lending
    ├── money_market.json    # Money market rates
    ├── gas_optimizer.json   # Gas optimization
    ├── risk_analyzer.json   # Risk analysis
    └── shortcuts.json       # Command shortcuts
```

### JSON File Structure

```json
{
  "feature_name": "Token Swap",
  "tagline": "Best rates across DEXs",
  "description": "Multi-aggregator swap...",
  "core_capabilities": [...],
  "supported_aggregators": [...],
  "supported_tokens": {...},
  "features": [...],
  "competitive_advantages": [...],
  "getting_started": {
    "for_users": {...},
    "for_investors": {...}
  },
  "common_questions": [...]
}
```

---

## Intent Detection System

### Intent Categories

| Intent | Keywords | Knowledge File |
|--------|----------|----------------|
| `anvil_knowledge` | anvil, what is anvil | overview.json |
| `HUNTER_SENTIMENT` | hunter, sentiment | hunter_ai.json |
| `ULTRA_ARBITRAGE` | ultra, arbitrage, flash loan | ultra.json |
| `SWAP` | swap, exchange, trade | swap.json |
| `PORTFOLIO` | portfolio, balance | portfolio.json |
| `WALLET` | wallet, my wallet | wallet.json |
| `LENDING_MORPHO` | lending, morpho, vault | lending_morpho.json |
| `GAS_OPTIMIZER` | gas, transaction fee | gas_optimizer.json |
| `RISK_ANALYZER` | risk, safe, tvl | risk_analyzer.json |
| `defi_protocol` | aave, compound, vs | (built-in knowledge) |
| `general_question` | defi, yield, staking | (built-in knowledge) |

### Intent Detection Logic

```python
def _detect_knowledge_intent(self, query: str) -> str:
    """Detect knowledge intent from query."""
    query_lower = query.lower()
    
    # Anvil-specific queries
    if any(kw in query_lower for kw in ["anvil", "what is anvil"]):
        return "anvil_knowledge"
    
    # Hunter AI queries
    if any(kw in query_lower for kw in ["hunter", "hunter ai", "sentiment"]):
        return "HUNTER_SENTIMENT"
    
    # ULTRA queries
    if any(kw in query_lower for kw in ["ultra", "arbitrage", "flash loan"]):
        return "ULTRA_ARBITRAGE"
    
    # Swap queries
    if any(kw in query_lower for kw in ["swap", "exchange", "what type of swaps"]):
        return "SWAP"
    
    # Protocol comparisons
    if any(kw in query_lower for kw in ["compare", "vs", "versus"]):
        return "defi_protocol"
    
    # ... more intents
    
    return "general_question"
```

---

## Data Flow

### Execute Method Flow

```python
async def execute(self, conversation_id, message, conversation_context):
    # 1. Load knowledge injector lazily
    if self._knowledge_injector is None:
        from app.application.chat.services.knowledge_injector import KnowledgeInjector
        self._knowledge_injector = KnowledgeInjector()
    
    # 2. Detect intent from query
    detected_intent = self._detect_knowledge_intent(query_lower)
    
    # 3. Get relevant knowledge from JSON files
    knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(
        user_query=message.value,
        detected_intent=detected_intent,
        user_type=user_type,
    )
    
    # 4. Format knowledge as context string
    knowledge_context = self._format_knowledge_context(knowledge_dict)
    
    # 5. Build LLM messages with knowledge
    messages = self._build_messages(message, context, knowledge_context)
    
    # 6. Call LLM
    response = await self._llm_client.chat(
        messages=messages,
        model=self._model,  # gemini-2.0-flash
        temperature=self._temperature,  # 0.5
    )
    
    # 7. Build sources and return
    sources = [
        SourceInfo(source_type=SourceType.LLM, ...),
        SourceInfo(source_type=SourceType.API, source_name="Anvil Knowledge Base", ...),
    ]
    
    return AgentResponse(content=response["content"], sources=sources, ...)
```

---

## System Prompt Design

### Key Sections

1. **Role Definition**: Educational assistant for DeFi/crypto
2. **Knowledge Areas**: Anvil platform, DeFi protocols, crypto tokens
3. **Language Rules**: Match user's language
4. **Terminology Rules**: Use "supply assets" not "préstamos"
5. **Direct Answer Rules**: Never ask for clarification
6. **Off-Topic Handling**: Politely redirect
7. **Examples**: Detailed response examples

### Critical Rules in Prompt

```python
"""
**CRITICAL: ANSWER ONLY THE CURRENT QUESTION**
- Answer ONLY the user's current question
- Do NOT include information about topics from previous messages
- Respond in the SAME language as the question
- Do NOT provide the same answer in multiple languages
- Do NOT duplicate content

**CRITICAL: NEVER ASK FOR CLARIFICATION ON DeFi TOPICS**
- If user says "aave vs compound" → PROVIDE THE COMPARISON directly
- Short queries like "X vs Y" are COMPLETE questions - answer them directly
"""
```

---

## Knowledge Context Formatting

### Format Logic

```python
def _format_knowledge_context(self, knowledge_dict: dict) -> str:
    """Format knowledge dictionary as context string."""
    context_parts = []
    
    if "feature_name" in knowledge_dict:
        context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
    
    if "tagline" in knowledge_dict:
        context_parts.append(f"Tagline: {knowledge_dict['tagline']}")
    
    if "description" in knowledge_dict:
        context_parts.append(f"Description: {knowledge_dict['description']}")
    
    # Format supported aggregators (for swap queries)
    if "supported_aggregators" in knowledge_dict:
        aggregators = knowledge_dict["supported_aggregators"]
        context_parts.append("\n**Supported Aggregators:**")
        for agg in aggregators:
            name = agg.get("name", "")
            desc = agg.get("description", "")
            context_parts.append(f"- {name}: {desc}")
    
    # Format features
    if "features" in knowledge_dict:
        features = knowledge_dict["features"]
        context_parts.append(f"\n**Features:** {', '.join(features[:5])}")
    
    return "\n".join(context_parts)
```

---

## Direct Question Detection

### Logic

```python
def _build_messages(self, message, context, knowledge_context):
    query_lower = message.value.lower().strip()
    
    # Detect direct questions that should be answered immediately
    is_direct_question = (
        query_lower.startswith(("what is", "que es", "qué es", "explain ")) or
        " vs " in query_lower or  # "aave vs compound"
        " versus " in query_lower or
        "difference between" in query_lower or
        "?" in message.value and len(message.value.split()) < 10
    )
    
    # For direct questions, DON'T include conversation history
    if not is_direct_question:
        # Include minimal history (last 1 message only)
        history = conversation_context.last_n_messages(1)
        for msg in history:
            messages.append(msg)
    
    # Add instruction suffix for comparisons
    if " vs " in query_lower or "compare" in query_lower:
        instruction = "\n\nCRITICAL: This is a COMPARISON question. Provide detailed comparison with key differences."
        message.value += instruction
```

---

## Source Attribution

### Sources Built

```python
sources = [
    SourceInfo(
        source_type=SourceType.LLM,
        source_name=model_name,
        citation_text=f"Generated by {model_name} with Anvil knowledge base",
        relevance_score=1.0,
        metadata={"knowledge_base_used": bool(knowledge_context)},
    )
]

# Add knowledge base source if used
if knowledge_context:
    sources.append(
        SourceInfo(
            source_type=SourceType.API,
            source_name="Anvil Knowledge Base",
            citation_text="Anvil platform knowledge and features",
            relevance_score=1.0,
            metadata={"intent": detected_intent, "knowledge_base": True},
        )
    )
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Intent detection | < 5ms | ~2ms |
| Knowledge loading | < 50ms | ~30ms (cached) |
| Context formatting | < 20ms | ~10ms |
| LLM response | < 1s | ~800ms |
| Total | < 1.5s | ~900ms |

### Caching

```python
# KnowledgeInjector caches loaded JSON files
self._cache: Dict[str, Dict[str, Any]] = {}

def _load_json(self, filename: KnowledgeFile) -> Dict[str, Any]:
    if filename not in self._cache:
        file_path = self.features_path / f"{filename.value}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            self._cache[filename] = json.load(f)
    return self._cache[filename]
```

---

## Testing

### Test Cases

```python
# Intent detection
def test_detect_anvil_intent():
    intent = agent._detect_knowledge_intent("what is anvil")
    assert intent == "anvil_knowledge"

def test_detect_protocol_comparison_intent():
    intent = agent._detect_knowledge_intent("aave vs compound")
    assert intent == "defi_protocol"

def test_detect_swap_intent():
    intent = agent._detect_knowledge_intent("what type of swaps can I do")
    assert intent == "SWAP"

# Direct question detection
def test_direct_question_detected():
    # "aave vs compound" should be detected as direct question
    messages = agent._build_messages(...)
    # Should NOT include conversation history for direct questions

# Knowledge formatting
def test_format_knowledge_context():
    knowledge = {"feature_name": "Swap", "description": "Token swap..."}
    context = agent._format_knowledge_context(knowledge)
    assert "Feature: Swap" in context
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added knowledge base integration |
| 2026-01-29 | Added protocol comparison support |
| 2026-01-29 | Added multi-language support |
