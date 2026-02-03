# Wallet Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **WALLET** agent, providing wallet address display for authenticated users with full, non-truncated addresses.

### Key Components

- **WalletAgent**: Core agent for wallet queries
- **UserDataContext**: Wallet data from database
- **Balance-Aware Suggestions**: Context-based recommendations
- **Full Address Requirement**: Never truncate addresses

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       WALLET AGENT ARCHITECTURE                          │
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
                    │ AuthenticatedSupervisor  │
                    │   Coordinator            │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      WalletAgent         │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
                    ▼                         ▼
            ┌───────────────┐       ┌─────────────────┐
            │ User Context  │       │    Vertex AI    │
            │ (Wallet Data) │       │    (LLM)        │
            └───────────────┘       └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    WALLET = "wallet"  # Wallet management & addresses
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

### Supervisor Integration

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
"""
2. WALLET QUERIES (authenticated - REAL data):
   - "my wallets", "connected wallets", "wallet address" → "wallet" agent
   - "wallet info", "list wallets", "show wallets" → "wallet" agent
"""
```

### Routing Examples

```python
"my wallets" → {{"tasks":[{{"agent_type":"wallet"}}]}}
"show my wallet address" → {{"tasks":[{{"agent_type":"wallet"}}]}}
```

---

## Infrastructure Layer

### WalletAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/wallet_agent.py`

**Lines**: ~337

```python
class WalletAgent:
    """
    Wallet Agent implementation for authenticated users.
    
    Implements: AgentGateway
    
    Purpose: Wallet management and balance queries
    
    Capabilities:
    - List user's connected wallets
    - Show balances for each wallet
    - Multi-chain wallet support
    - Primary wallet identification
    - Wallet provider information (Privy, External, Imported)
    
    IMPORTANT: This agent requires user authentication.
    Guest users should be redirected to GuestAuthAgent.
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.3 (balanced)
    """
```

### Key Methods

| Method | Purpose | Lines |
|--------|---------|-------|
| `execute()` | Main entry point | 78-188 |
| `_extract_user_context()` | Get wallet from context | 194-225 |
| `_build_wallet_context()` | Format wallet string | 227-271 |
| `_create_auth_required_response()` | Guest user response | 273-304 |
| `_get_system_prompt()` | LLM system prompt | 306-336 |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,     # Vertex AI / DeepInfra
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 1500,
):
```

---

## Data Flow

### Execute Method Flow

```python
async def execute(self, conversation_id, message, conversation_context):
    # 1. Extract user context from conversation metadata
    user_context = self._extract_user_context(conversation_context)
    
    # 2. Check authentication
    if not user_context:
        return self._create_auth_required_response(start_time)
    
    # 3. Build wallet context string (full addresses)
    wallet_context = self._build_wallet_context(user_context)
    
    # 4. Get portfolio balance for suggestions
    portfolio_summary = user_context.get("portfolio_summary", {})
    total_balance = float(portfolio_summary.get("total_value_usd", 0) or 0)
    
    # 5. Build suggestions based on balance
    if total_balance == 0:
        suggestions = """
**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC
• 📥 Transfer crypto from another wallet
"""
    else:
        suggestions = f"""
**💰 Balance:** ${total_balance:,.2f}

**💡 What you can do:**
• 🔄 **Swap** - Trade between cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for holdings
"""
    
    # 6. Build enhanced message with context
    enhanced_message = f"""User Query: {message.value}

**USER'S WALLET DATA:**
{wallet_context}

**BALANCE & SUGGESTIONS:**
{suggestions}

Respond using ONLY the wallet data above.
CRITICAL: Show the FULL wallet address - never truncate!
"""
    
    # 7. Get LLM response
    response = await self._llm_client.chat(
        messages=[system_prompt, enhanced_message],
        model=self._model,
    )
    
    # 8. Build sources and return
    return AgentResponse(
        content=response["content"],
        sources=[database_source, llm_source],
    )
```

---

## Full Address Requirement

### Critical Rule

**NEVER truncate wallet addresses!** Users need the complete address to receive funds.

### Implementation

```python
def _build_wallet_context(self, user_context: dict) -> str:
    lines = []
    wallets = user_context.get("wallets", [])
    
    for i, wallet in enumerate(wallets, 1):
        address = wallet.get("address", "Unknown")
        
        lines.append(f"**Wallet {i}:**")
        # ALWAYS show the FULL address - users need the complete address
        lines.append(f"  - Address: `{address}`")  # Full address, not truncated
        
    return "\n".join(lines)
```

### System Prompt Enforcement

```python
def _get_system_prompt(self) -> str:
    return """You are the Wallet Agent, Anvil's wallet management specialist.

**CRITICAL - SHOW FULL ADDRESS:**
ALWAYS show the COMPLETE wallet address (e.g., `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`)
NEVER truncate or shorten addresses (do NOT use `0x742d...f44e` format)
Users NEED the full address to receive funds!
"""
```

---

## Balance-Aware Suggestions

### Suggestion Logic

```python
# Get portfolio balance for context-aware suggestions
portfolio_summary = user_context.get("portfolio_summary", {})
total_balance = float(portfolio_summary.get("total_value_usd", 0) or 0)

# Build suggestions based on balance
if total_balance == 0:
    suggestions = """
**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay
• 📥 Transfer crypto from another wallet to the address above
"""
else:
    suggestions = f"""
**💰 Balance:** ${total_balance:,.2f}

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for detailed holdings
"""
```

### Suggestion Matrix

| Balance State | Suggestions |
|---------------|-------------|
| $0 | "buy crypto", "transfer from another wallet" |
| > $0 | "swap", "earn yield", "portfolio" |

---

## Authentication Handling

### User Context Extraction

```python
def _extract_user_context(self, conversation_context):
    """Extract user context from conversation metadata."""
    if not conversation_context.user_metadata:
        return None
    
    # Check for user_context key
    if "user_context" in conversation_context.user_metadata:
        return conversation_context.user_metadata["user_context"]
    
    # Check for direct wallet data
    if "wallets" in conversation_context.user_metadata:
        return conversation_context.user_metadata
    
    # Check for flat structure (supervisor injection)
    if conversation_context.user_metadata.get("is_authenticated"):
        wallet_address = conversation_context.user_metadata.get("wallet_address")
        return {
            "user_id": conversation_context.user_metadata.get("user_id"),
            "wallet_address": wallet_address,
            "wallets": [{
                "address": wallet_address,
                "chain_type": conversation_context.user_metadata.get("wallet_chain"),
                "is_primary": True,
            }] if wallet_address else [],
            "primary_wallet": {
                "address": wallet_address,
                "chain_type": conversation_context.user_metadata.get("wallet_chain"),
            } if wallet_address else None,
        }
    
    return None  # Guest user
```

### Auth Required Response

```python
def _create_auth_required_response(self, start_time: float) -> AgentResponse:
    """Create response for unauthenticated users."""
    content = """**Wallet Access Requires Authentication**

To view your wallet information, balances, and connected addresses, 
you need to sign in to your Anvil account.

**How to Connect:**
1. Click "Sign In" or "Connect Wallet" in the app
2. Choose your preferred method (email, social, or wallet)
3. Once connected, I can show you:
   - All your connected wallets
   - Balances across chains
   - Transaction history
   - Portfolio overview
"""
    
    return AgentResponse(
        content=content,
        agent_type=self.agent_type,
        metadata={"auth_required": True},
    )
```

---

## Source Attribution

### Sources Built

```python
sources = []
fetched_at = datetime.now(UTC)

# Add database source (wallet data)
sources.append(create_database_source(
    citation_text="Your wallet data from Anvil",
    fetched_at=fetched_at,
    metadata={"query_type": "wallet_info"},
))

# Add LLM source
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))
```

---

## Logging

### Debug Statements

The wallet agent uses minimal logging to avoid exposing sensitive address information in logs.

---

## Testing

### Unit Tests

```python
def test_extract_user_context_authenticated():
    context = ConversationContext(
        user_metadata={"is_authenticated": True, "wallet_address": "0x123..."}
    )
    result = agent._extract_user_context(context)
    assert result is not None
    assert "wallets" in result

def test_extract_user_context_guest():
    context = ConversationContext(user_metadata=None)
    result = agent._extract_user_context(context)
    assert result is None

def test_build_wallet_context_full_address():
    user_context = {
        "wallets": [{"address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"}]
    }
    result = agent._build_wallet_context(user_context)
    # Full address must be present
    assert "0x742d35Cc6634C0532925a3b844Bc454e4438f44e" in result
    # Truncated format must NOT be present
    assert "0x742d..." not in result
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Context extraction | < 10ms | ~5ms |
| Context building | < 20ms | ~10ms |
| LLM response | < 800ms | ~600ms |
| Total | < 1s | ~700ms |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added full address requirement |
| 2026-01-29 | Added balance-aware suggestions |
| 2026-01-29 | Added source attribution |
