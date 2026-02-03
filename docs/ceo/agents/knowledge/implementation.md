# Knowledge Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.KNOWLEDGE
│   ├── ports/
│   │   └── agent_squad/
│   │       └── agent_gateway.py          # AgentGateway interface
│   └── services/
│       └── agent_squad/
│           ├── authenticated_supervisor.py  # Auth routing
│           └── guest_supervisor.py          # Guest routing
│
├── application/
│   └── chat/
│       └── services/
│           ├── knowledge_injector.py     # Knowledge loading
│           └── knowledge_compressor.py   # Token optimization
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               └── knowledge_agent.py    # Main agent
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration

anvil_knowledge/
└── features/
    ├── overview.json                     # Anvil overview
    ├── swap.json                         # Swap features
    ├── hunter_ai.json                    # Hunter AI
    ├── ultra.json                        # ULTRA arbitrage
    ├── portfolio.json                    # Portfolio
    ├── wallet.json                       # Wallet
    ├── lending_morpho.json               # Lending
    ├── money_market.json                 # Money market
    ├── gas_optimizer.json                # Gas optimizer
    ├── risk_analyzer.json                # Risk analyzer
    └── shortcuts.json                    # Shortcuts
```

---

## Core Files

### 1. KnowledgeAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/knowledge_agent.py`
**Lines**: ~587

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 42-62 | Initialize with LLM client |
| `agent_type` | 64-67 | Return AgentType.KNOWLEDGE |
| `execute` | 69-199 | Main entry point |
| `is_available` | 201-204 | Availability check |
| `_detect_knowledge_intent` | 206-265 | Intent detection |
| `_format_knowledge_context` | 267-322 | Format JSON as context |
| `_build_messages` | 324-375 | Build LLM messages |
| `_get_system_prompt` | 377-586 | System prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.5,  # Lower for factual responses
    max_tokens: int = 1500,    # More for detailed explanations
):
    self._llm_client = llm_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
    self._knowledge_injector = None  # Lazy load
```

---

### 2. KnowledgeInjector

**File**: `src/app/application/chat/services/knowledge_injector.py`
**Lines**: ~655

#### Class Definition

```python
class KnowledgeInjector:
    """
    Dynamically selects and injects relevant knowledge into LLM prompts
    based on user queries and detected intents.
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 35-55 | Initialize with knowledge base path |
| `_load_json` | 57-72 | Load JSON file with caching |
| `get_knowledge_for_intent` | 74-138 | Get relevant knowledge |
| `_get_overview_knowledge` | 140-162 | Overview knowledge |
| `_get_hunter_ai_knowledge` | 164-208 | Hunter AI knowledge |
| `_get_ultra_knowledge` | 210-256 | ULTRA knowledge |
| `_get_swap_knowledge` | 258-294 | Swap knowledge |
| `_get_shortcuts_knowledge` | 296-307 | Shortcuts knowledge |
| `_get_portfolio_knowledge` | 309-326 | Portfolio knowledge |
| `_get_wallet_knowledge` | 328-345 | Wallet knowledge |
| `_get_lending_morpho_knowledge` | 347-365 | Lending knowledge |
| `_get_gas_optimizer_knowledge` | 367-384 | Gas optimizer knowledge |
| `_get_risk_analyzer_knowledge` | 386-403 | Risk analyzer knowledge |
| `_get_money_market_knowledge` | 405-432 | Money market knowledge |
| `augment_system_prompt` | 434-513 | Enhanced system prompt |
| `_format_knowledge` | 515-540 | Format as text |
| `clear_cache` | 576-578 | Clear JSON cache |

#### Constructor

```python
def __init__(self, knowledge_base_path: Optional[Path] = None):
    if knowledge_base_path is None:
        # Default to project root / anvil_knowledge
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent.parent
        knowledge_base_path = project_root / "anvil_knowledge"
    
    self.knowledge_base_path = knowledge_base_path
    self.features_path = knowledge_base_path / "features"
    self._cache: Dict[str, Dict[str, Any]] = {}  # Cached JSON files
```

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_knowledge_agent(self, llm_client: LLMClientGateway) -> KnowledgeAgent:
    """Provide Knowledge Anvil agent for educational queries and Anvil knowledge."""
    return KnowledgeAgent(llm_client=llm_client)
```

---

## Intent Detection Implementation

### Implementation

```python
# Lines 206-265
def _detect_knowledge_intent(self, query: str) -> str:
    """Detect knowledge intent from query."""
    query_lower = query.lower()
    
    # Anvil-specific queries
    if any(kw in query_lower for kw in ["anvil", "what is anvil", "how does anvil"]):
        return "anvil_knowledge"
    
    # Hunter AI queries
    if any(kw in query_lower for kw in ["hunter", "hunter ai", "sentiment", "price prediction"]):
        return "HUNTER_SENTIMENT"
    
    # ULTRA queries
    if any(kw in query_lower for kw in ["ultra", "arbitrage", "flash loan", "mev"]):
        return "ULTRA_ARBITRAGE"
    
    # Swap queries
    if any(kw in query_lower for kw in ["swap", "exchange", "trade tokens", "what type of swaps"]):
        return "SWAP"
    
    # Portfolio queries
    if any(kw in query_lower for kw in ["portfolio", "balance", "holdings", "my assets"]):
        return "PORTFOLIO"
    
    # Wallet queries
    if any(kw in query_lower for kw in ["wallet", "wallets", "my wallet", "export wallet"]):
        return "WALLET"
    
    # DeFi Protocol comparisons
    defi_protocols = [
        "aave", "compound", "maker", "makerdao", "morpho", "spark",
        "uniswap", "sushiswap", "curve", "balancer", "pancakeswap",
        "yearn", "convex", "beefy", "lido", "rocket pool",
    ]
    if any(protocol in query_lower for protocol in defi_protocols):
        return "defi_protocol"
    
    # Protocol comparison queries
    if any(kw in query_lower for kw in ["compare", "vs", "versus", "difference between"]):
        return "defi_protocol"
    
    # Lending queries
    if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault", "supply"]):
        return "LENDING_MORPHO"
    
    # Gas optimizer queries
    if any(kw in query_lower for kw in ["gas", "gas price", "transaction fee"]):
        return "GAS_OPTIMIZER"
    
    # Risk analyzer queries
    if any(kw in query_lower for kw in ["risk", "safe", "safety", "protocol risk"]):
        return "RISK_ANALYZER"
    
    # General DeFi/crypto
    if any(kw in query_lower for kw in ["defi", "yield", "staking"]):
        return "general_question"
    
    # Default
    return "general_question"
```

---

## Knowledge Loading Implementation

### Get Knowledge for Intent

```python
# Lines 74-138
def get_knowledge_for_intent(
    self,
    user_query: str,
    detected_intent: str,
    user_type: str = "user"  # "user" or "investor"
) -> Dict[str, Any]:
    """Get relevant knowledge sections based on intent and user type."""
    query_lower = user_query.lower()
    
    # Overview queries - "what can you do?"
    if any(kw in query_lower for kw in ["what can you do", "capabilities", "what is anvil"]):
        return self._get_overview_knowledge(user_type)
    
    # Hunter AI intents
    if detected_intent.startswith("HUNTER_"):
        return self._get_hunter_ai_knowledge(detected_intent, query_lower, user_type)
    
    # ULTRA intents
    if detected_intent.startswith("ULTRA_"):
        return self._get_ultra_knowledge(detected_intent, query_lower, user_type)
    
    # Swap intent
    if detected_intent == "SWAP":
        return self._get_swap_knowledge(query_lower, user_type)
    
    # Command help / shortcuts
    if any(kw in query_lower for kw in ["command", "how do i", "how to", "syntax"]):
        return self._get_shortcuts_knowledge(detected_intent)
    
    # Portfolio queries
    if any(kw in query_lower for kw in ["portfolio", "balance", "holdings"]):
        return self._get_portfolio_knowledge(user_type)
    
    # Wallet queries
    if any(kw in query_lower for kw in ["wallet", "wallets", "my wallet"]):
        return self._get_wallet_knowledge(user_type)
    
    # Lending queries
    if any(kw in query_lower for kw in ["lending", "lend", "morpho", "vault"]):
        return self._get_lending_morpho_knowledge(user_type)
    
    # Gas optimizer queries
    if any(kw in query_lower for kw in ["gas", "gas price", "transaction fee"]):
        return self._get_gas_optimizer_knowledge(user_type)
    
    # Risk analyzer queries
    if any(kw in query_lower for kw in ["risk", "safe", "safety"]):
        return self._get_risk_analyzer_knowledge(user_type)
    
    # Money market queries
    if any(kw in query_lower for kw in ["money market", "lending rate", "apy comparison"]):
        return self._get_money_market_knowledge(user_type)
    
    # Default to overview
    return self._get_overview_knowledge(user_type)
```

### JSON File Loading

```python
# Lines 57-72
def _load_json(self, filename: KnowledgeFile) -> Dict[str, Any]:
    """
    Load JSON file from features directory with caching.
    """
    if filename not in self._cache:
        file_path = self.features_path / f"{filename.value}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            self._cache[filename] = json.load(f)
    
    return self._cache[filename]
```

---

## Message Building Implementation

### Direct Question Detection

```python
# Lines 324-375
def _build_messages(
    self,
    message: MessageContent,
    conversation_context: ConversationContext,
    knowledge_context: str = "",
) -> list[dict]:
    """Build messages for LLM API."""
    messages = [
        {
            "role": "system",
            "content": self._get_system_prompt(knowledge_context),
        }
    ]
    
    query_lower = message.value.lower().strip()
    
    # Detect direct questions that should be answered immediately
    is_direct_question = (
        query_lower.startswith(("what is", "que es", "qué es", "what are", "explain ")) or
        " vs " in query_lower or  # "aave vs compound"
        " versus " in query_lower or
        "difference between" in query_lower or
        "?" in message.value and len(message.value.split()) < 10
    )
    
    # For direct questions, DON'T include conversation history
    if not is_direct_question:
        # For complex questions, include minimal history (last 1 message only)
        history = conversation_context.last_n_messages(1)
        for msg in history:
            msg_content = msg.get("content", "")
            if msg_content and len(msg_content) > 0:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg_content,
                })
    
    # Add instruction suffix for comparisons
    instruction_suffix = ""
    if " vs " in query_lower or " versus " in query_lower or "compare" in query_lower:
        instruction_suffix = "\n\nCRITICAL: This is a COMPARISON question. Provide a detailed comparison with key differences, pros/cons, and use cases."
    elif is_direct_question:
        instruction_suffix = "\n\nCRITICAL: Answer ONLY this question. Do NOT include information about other topics. Respond in the SAME language as the question."
    
    messages.append({
        "role": "user",
        "content": message.value + instruction_suffix,
    })
    
    return messages
```

---

## Knowledge Context Formatting

### Implementation

```python
# Lines 267-322
def _format_knowledge_context(self, knowledge_dict: dict) -> str:
    """Format knowledge dictionary as context string."""
    context_parts = []
    
    if "feature_name" in knowledge_dict:
        context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
    
    if "tagline" in knowledge_dict:
        context_parts.append(f"Tagline: {knowledge_dict['tagline']}")
    
    if "description" in knowledge_dict:
        context_parts.append(f"Description: {knowledge_dict['description']}")
    
    if "capability" in knowledge_dict:
        if isinstance(knowledge_dict["capability"], dict):
            cap = knowledge_dict["capability"]
            context_parts.append(f"Capability: {cap.get('name', '')} - {cap.get('description', '')}")
    
    # Format supported aggregators (for swap queries)
    if "supported_aggregators" in knowledge_dict:
        aggregators = knowledge_dict["supported_aggregators"]
        if isinstance(aggregators, list):
            context_parts.append("\n**Supported Aggregators:**")
            for agg in aggregators:
                if isinstance(agg, dict):
                    name = agg.get("name", "")
                    desc = agg.get("description", "")
                    chains = agg.get("supported_chains", [])
                    if chains:
                        chains_str = ", ".join(chains) if isinstance(chains, list) else str(chains)
                        context_parts.append(f"- {name}: {desc} (Chains: {chains_str})")
                    else:
                        context_parts.append(f"- {name}: {desc}")
    
    # Format supported tokens
    if "supported_tokens" in knowledge_dict:
        tokens = knowledge_dict["supported_tokens"]
        if isinstance(tokens, dict):
            context_parts.append("\n**Supported Tokens:**")
            if "major_tokens" in tokens:
                context_parts.append(f"Major tokens: {', '.join(tokens['major_tokens'])}")
            if "total_supported" in tokens:
                context_parts.append(f"Total: {tokens['total_supported']}")
    
    # Format features
    if "features" in knowledge_dict:
        features = knowledge_dict["features"]
        if isinstance(features, list):
            context_parts.append(f"\n**Features:** {', '.join(features[:5])}")
    
    if "competitive_advantages" in knowledge_dict:
        advantages = knowledge_dict["competitive_advantages"]
        if isinstance(advantages, list):
            context_parts.append(f"\n**Competitive Advantages:** {', '.join(advantages[:3])}")
    
    return "\n".join(context_parts) if context_parts else ""
```

---

## System Prompt

### Key Sections

The system prompt (~200 lines) includes:

1. **Role Definition**: Educational assistant for DeFi/crypto
2. **Knowledge Areas**: Anvil platform, DeFi protocols, crypto tokens
3. **Swap Limitations**: Hyperliquid Spot meme tokens only
4. **Lending Terminology**: Supply assets, not préstamos
5. **Response Style**: Clear, educational, concise
6. **Direct Answer Rules**: Never ask for clarification
7. **Off-Topic Handling**: Politely redirect
8. **Examples**: Detailed response examples

---

## Source Attribution

### Building Sources

```python
# Lines 146-183
from app.domain.value_objects.chat.source_info import SourceInfo, SourceType

sources = [
    SourceInfo(
        source_type=SourceType.LLM,
        source_name=model_name,
        citation_text=f"Generated by {model_name} with Anvil knowledge base",
        fetched_at=fetched_at,
        provider=provider,
        relevance_score=1.0,
        metadata={
            "model": model_name,
            "knowledge_base_used": bool(knowledge_context),
            "intent": detected_intent,
        },
    )
]

# Add knowledge base source if used
if knowledge_context:
    sources.append(
        SourceInfo(
            source_type=SourceType.API,
            source_name="Anvil Knowledge Base",
            citation_text="Anvil platform knowledge and features",
            fetched_at=fetched_at,
            provider="Anvil",
            relevance_score=1.0,
            metadata={"intent": detected_intent, "knowledge_base": True},
        )
    )
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_knowledge_agent.py -v

# Integration tests
pytest tests/integration/test_knowledge_agent.py -v

# All knowledge tests
pytest tests/ -k knowledge -v
```

### Test Cases

```python
# Intent detection
def test_detect_anvil_intent():
    intent = agent._detect_knowledge_intent("what is anvil")
    assert intent == "anvil_knowledge"

def test_detect_protocol_intent():
    intent = agent._detect_knowledge_intent("aave vs compound")
    assert intent == "defi_protocol"

def test_detect_swap_intent():
    intent = agent._detect_knowledge_intent("what type of swaps can I do")
    assert intent == "SWAP"

# Knowledge injection
def test_get_overview_knowledge():
    knowledge = injector.get_knowledge_for_intent(
        "what is anvil",
        "anvil_knowledge",
        "user"
    )
    assert "feature_name" in knowledge

# Context formatting
def test_format_knowledge_context():
    knowledge = {"feature_name": "Swap", "description": "Token swap..."}
    context = agent._format_knowledge_context(knowledge)
    assert "Feature: Swap" in context

# Direct question detection
def test_direct_question_vs_query():
    # "aave vs compound" should be detected as direct question
    query = "aave vs compound"
    is_direct = " vs " in query.lower()
    assert is_direct == True
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Intent detection | < 5ms | String matching |
| Knowledge loading | < 50ms | JSON with caching |
| Context formatting | < 20ms | String concatenation |
| LLM response | < 1s | Vertex AI |
| Total | < 1.5s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added knowledge base integration |
| 2026-01-29 | Added protocol comparison support |
| 2026-01-29 | Added multi-language support |
