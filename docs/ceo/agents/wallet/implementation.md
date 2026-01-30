# Wallet Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.WALLET
│   ├── ports/
│   │   └── agent_squad/
│   │       └── agent_gateway.py          # AgentGateway interface
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py  # Routing rules
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               └── wallet_agent.py       # Main agent
│
├── application/
│   └── chat/
│       ├── commands/
│       │   └── send_message_with_supervisor.py  # Entry point
│       └── services/
│           └── user_data_service.py      # Wallet data
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. WalletAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/wallet_agent.py`
**Lines**: ~337

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 52-71 | Initialize with LLM client |
| `agent_type` | 73-76 | Return AgentType.WALLET |
| `execute` | 78-188 | Main entry point |
| `is_available` | 190-192 | Availability check |
| `_extract_user_context` | 194-225 | Get wallet from context |
| `_build_wallet_context` | 227-271 | Format wallet string |
| `_create_auth_required_response` | 273-304 | Guest user response |
| `_get_system_prompt` | 306-336 | LLM system prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 1500,
):
    self._llm_client = llm_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_wallet_agent(
    self, llm_client: LLMClientGateway
) -> WalletAgent:
    """
    Provide Wallet Agent for authenticated users.
    
    This agent handles wallet queries:
    - List connected wallets
    - Show balances
    - Wallet status and provider info
    """
    return WalletAgent(llm_client=llm_client)
```

---

### 3. Supervisor Routing

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
# Lines 969-971
"""
2. WALLET QUERIES (authenticated - REAL data):
   - "my wallets", "connected wallets", "wallet address" → "wallet" agent
   - "wallet info", "list wallets", "show wallets" → "wallet" agent
"""

# Example mappings
"my wallets" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show user's connected wallets"}}]}}
"show my wallet address" → {{"tasks":[{{"agent_type":"wallet","task_description":"Display user's wallet addresses"}}]}}
```

---

## User Context Extraction

### Implementation

```python
# Lines 194-225
def _extract_user_context(self, conversation_context: ConversationContext) -> dict | None:
    """Extract user context from conversation metadata."""
    if not conversation_context.user_metadata:
        return None
    
    # Check for user_context or direct wallet data
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
    
    return None
```

---

## Wallet Context Building

### Implementation

```python
# Lines 227-271
def _build_wallet_context(self, user_context: dict) -> str:
    """Build wallet context string from user data."""
    lines = []
    
    wallets = user_context.get("wallets", [])
    primary_wallet = user_context.get("primary_wallet")
    
    if not wallets:
        return """**Your Wallet is Being Set Up! 🔐**

Your Anvil wallet is being configured. This usually takes just a moment.

**What you can do:**
• **Refresh the page** if this persists
• **Check your account settings** to verify wallet status
• **Contact support** if you need help
"""
    
    lines.append(f"**Connected Wallets: {len(wallets)}**\n")
    
    for i, wallet in enumerate(wallets, 1):
        is_primary = (primary_wallet and 
                     wallet.get("address") == primary_wallet.get("address"))
        
        address = wallet.get("address", "Unknown")
        
        primary_marker = " (PRIMARY)" if is_primary else ""
        provider = wallet.get("provider")
        chain = wallet.get("chain_type")
        
        lines.append(f"**Wallet {i}{primary_marker}:**")
        # ALWAYS show the FULL address - users need the complete address
        lines.append(f"  - Address: `{address}`")
        # Only show provider and chain if they have valid values
        if provider and provider.lower() not in ("unknown", "none", ""):
            lines.append(f"  - Provider: {provider}")
        if chain and chain.lower() not in ("unknown", "none", ""):
            lines.append(f"  - Chain: {chain}")
        lines.append("")
    
    return "\n".join(lines)
```

---

## Balance-Aware Suggestions

### Implementation

```python
# Lines 103-121
# Get portfolio balance for context-aware suggestions
portfolio_summary = user_context.get("portfolio_summary", {})
total_balance = float(portfolio_summary.get("total_value_usd", 0) or 0)

# Build suggestions based on balance
if total_balance == 0:
    suggestions = """
**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay
• 📥 Transfer crypto from another wallet to the address above"""
else:
    suggestions = f"""
**💰 Balance:** ${total_balance:,.2f}

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for detailed holdings"""
```

---

## System Prompt

### Implementation

```python
# Lines 306-336
def _get_system_prompt(self) -> str:
    """Get system prompt for wallet agent."""
    return """You are the Wallet Agent, Anvil's wallet management specialist.

**YOUR ROLE:**
Show the user's connected wallet addresses. Keep it simple and concise.

**CRITICAL - SHOW FULL ADDRESS:**
ALWAYS show the COMPLETE wallet address (e.g., `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`)
NEVER truncate or shorten addresses (do NOT use `0x742d...f44e` format)
Users NEED the full address to receive funds!

**IMPORTANT RULES:**
1. ONLY show wallet addresses from the provided context
2. Show the FULL address - never truncate!
3. DO NOT mention balances - that's handled by the Portfolio agent
4. DO NOT suggest using external tools like Etherscan
5. Keep responses SHORT (3-5 lines max)
6. If asked about balances, just show the wallet and say "For balances, ask 'my portfolio'"

**RESPONSE FORMAT:**
Show wallet info in this format:
- **Your Wallet:** `0xFULL_ADDRESS_HERE`
- That's it! No extra commentary needed.

**DO NOT:**
- Truncate wallet addresses
- Mention balance information
- Suggest external block explorers
- Give long explanations
- Add unnecessary "next steps" """
```

---

## Auth Required Response

### Implementation

```python
# Lines 273-304
def _create_auth_required_response(self, start_time: float) -> AgentResponse:
    """Create response for unauthenticated users."""
    latency_ms = int((time.time() - start_time) * 1000)
    
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

Would you like me to help you with something else, or are you ready to sign in?"""
    
    from datetime import datetime, UTC
    from app.infrastructure.adapters.agent_squad.agents.source_helpers import create_llm_source
    
    return AgentResponse(
        content=content,
        agent_type=self.agent_type,
        tools_used=[],
        sources=[create_llm_source(model=self._model, fetched_at=datetime.now(UTC))],
        metadata={
            "latency_ms": latency_ms,
            "auth_required": True,
        },
    )
```

---

## Source Attribution

### Building Sources

```python
# Lines 150-172
from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
    create_llm_source,
    create_database_source,
)

sources = []
fetched_at = datetime.now(UTC)

# Add database source (wallet data)
sources.append(create_database_source(
    citation_text="Your wallet data from Anvil",
    fetched_at=fetched_at,
    metadata={"query_type": "wallet_info"},
))

# Add LLM source
model_name = response.get("model", self._model)
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))
```

---

## Response Building

### AgentResponse Structure

```python
# Lines 176-188
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["llm_gateway", "wallet_repository"],
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": model_name,
        "provider": provider_info,
        "wallet_count": len(user_context.get("wallets", [])) if user_context else 0,
    },
)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_wallet_agent.py -v

# Integration tests
pytest tests/integration/test_wallet_agent.py -v

# All wallet tests
pytest tests/ -k wallet -v
```

### Test Cases

```python
# User context extraction
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

# Full address display
def test_build_wallet_context_full_address():
    full_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    user_context = {
        "wallets": [{"address": full_address}]
    }
    result = agent._build_wallet_context(user_context)
    # Full address must be present
    assert full_address in result
    # Truncated format must NOT be present
    assert "..." not in result

# Multi-wallet
def test_build_wallet_context_multi_wallet():
    user_context = {
        "wallets": [
            {"address": "0x111...", "is_primary": True},
            {"address": "0x222...", "is_primary": False},
        ],
        "primary_wallet": {"address": "0x111..."},
    }
    result = agent._build_wallet_context(user_context)
    assert "Connected Wallets: 2" in result
    assert "(PRIMARY)" in result

# Auth required
def test_create_auth_required_response():
    response = agent._create_auth_required_response(time.time())
    assert response.metadata.get("auth_required") == True
    assert "Authentication" in response.content
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Context extraction | < 10ms | Dict lookup |
| Context building | < 20ms | String formatting |
| LLM response | < 800ms | Vertex AI |
| Total | < 1s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added full address requirement |
| 2026-01-29 | Added balance-aware suggestions |
| 2026-01-29 | Added source attribution |
