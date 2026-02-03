# Activity/Transaction History Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **Activity/Transaction History** feature, providing authenticated users with comprehensive transaction viewing and analytics.

### Key Features

- **Real-time Transaction Data**: Fetched from blockchain and indexed
- **Balance-Aware Responses**: Different messages based on user's portfolio state
- **Multi-Language Support**: English, Spanish, Portuguese, Chinese
- **Transaction Analytics**: Volume, chain activity, status tracking
- **Agent-Based Design**: Specialized TransactionHistoryAgent

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ACTIVITY/TRANSACTION ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│  Chat         │    │   Shortcuts       │    │   Guest Chat    │
│  Endpoints    │    │   Endpoint        │    │   Endpoint      │
└───────┬───────┘    └──────────┬────────┘    └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Application Layer   │
                    │  (Supervisor + Agent)│
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Authenticated│    │  Transaction     │    │   User Data     │
│  Supervisor   │    │  History Agent   │    │   Service       │
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │    Domain Layer      │
                    │  (Transaction Data)  │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Transaction  │    │  Transaction     │    │   User Context  │
│  Summary      │    │  Details         │    │                 │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Data Structures

#### TransactionSummary

```python
@dataclass
class TransactionSummary:
    """Aggregate transaction data for a user."""
    total_count: int                    # Total number of transactions
    volume_last_30_days: float          # 30-day USD volume
    most_active_chain: str | None       # Most frequently used chain
    recent_transactions: list[dict]     # Last N transactions
```

#### Transaction Details

```python
{
    "tx_hash": str,          # Transaction hash
    "type": str,             # SWAP, TRANSFER, APPROVE, DEPOSIT, etc.
    "status": str,           # success, pending, failed
    "chain": str,            # Base, Ethereum, Polygon, etc.
    "amount": str,           # Human-readable amount
    "created_at": str,       # ISO timestamp
}
```

---

## Application Layer

### TransactionHistoryAgent

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/transaction_history_agent.py`

```python
class TransactionHistoryAgent:
    """
    Transaction History Agent for authenticated users.
    
    Capabilities:
    - View recent transactions with details
    - Filter by chain, type, date range
    - Transaction volume analytics (30-day)
    - Most active chain identification
    - Transaction status tracking
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute transaction history agent."""
        # Extract user context
        user_context = self._extract_user_context(conversation_context)
        
        if not user_context:
            return self._create_auth_required_response(start_time)
        
        # Build transaction context
        tx_context = self._build_transaction_context(user_context)
        
        # Generate response with LLM
        response = await self._llm_client.chat(...)
        
        return AgentResponse(
            content=response["content"],
            agent_type=AgentType.TRANSACTION_HISTORY,
            sources=sources,
            ...
        )
```

### Key Methods

#### `_build_transaction_context()`

Builds the context string from user transaction data:

```python
def _build_transaction_context(self, user_context: dict[str, Any]) -> str:
    """Build transaction context string from user data."""
    tx_data = user_context.get("transactions", {})
    
    if not tx_data:
        # Get user balance for context-aware message
        portfolio_summary = user_context.get("portfolio_summary", {})
        total_balance = float(portfolio_summary.get("total_value_usd", 0) or 0)
        
        if total_balance < 1:
            # Empty balance - recommend buying first
            return """Your balance: $0.00

• 💳 **Buy crypto** - Say "buy crypto" to purchase USDC with card/Apple Pay/Google Pay
• 📥 **Receive crypto** - Transfer tokens from another wallet (ask "my wallet address" for your address)"""
        else:
            # Has balance but no transactions yet
            return f"""Your balance: ~${total_balance:,.2f}

No transaction history yet - you're ready to start! Try:

• 🔄 **Swap tokens** - Say "swap USDC to ETH" to trade
• 💰 **Earn yield** - Say "deposit 100 USDC" to start earning
• 📤 **Send tokens** - Say "send 10 USDC to 0x..." to transfer

Your transactions will appear here automatically! 🚀"""
    
    # Build transaction summary and list...
```

---

## Infrastructure Layer

### User Data Service Integration

The TransactionHistoryAgent receives user data from the `UserDataService`:

```python
# In AuthenticatedSupervisorCoordinator
user_data = await self._user_data_service.get_user_data(user_id)

# User data includes:
{
    "user_id": str,
    "wallet_address": str,
    "is_authenticated": True,
    "transactions": TransactionSummary,
    "portfolio_summary": PortfolioSummary,
    ...
}
```

### Source Attribution

The agent provides proper source attribution:

```python
sources = []

# Database source (transaction data)
sources.append(create_database_source(
    citation_text="Your transaction history from Anvil",
    fetched_at=fetched_at,
    metadata={"query_type": "transaction_history"},
))

# LLM source
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))
```

---

## Presentation Layer

### Chat Endpoint Integration

The transaction history is accessed through the standard chat endpoint:

```python
# conversations_router.py

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    ...
) -> ChatResponse:
    """Send message and route to appropriate handler."""
    
    # Authenticated users use supervisor
    if is_authenticated:
        # Supervisor routes to transaction_history agent
        result = await supervisor.execute_workflow(...)
```

---

## Supervisor Routing

### Routing Rules

```python
# In authenticated_supervisor.py

"""
3. TRANSACTION HISTORY (authenticated - REAL data):
   - "my transactions", "transaction history", "recent activity" → "transaction_history" agent
   - "show transactions", "past swaps", "activity summary" → "transaction_history" agent
   - "my activity", "show activity", "what have I done" → "transaction_history" agent
"""
```

### Example Mappings

```python
"my transactions" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's transaction history","depends_on":[]}}]}}
"recent activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show recent transaction activity","depends_on":[]}}]}}
"my activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's activity and transactions","depends_on":[]}}]}}
```

---

## Multi-Language Support

### Supported Languages

| Code | Language | Example Query |
|------|----------|---------------|
| `en` | English | "my activity" |
| `es` | Spanish | "mi actividad" |
| `pt` | Portuguese | "minha atividade" |
| `zh` | Chinese | "我的活动" |

### Response Templates

The agent uses language-aware responses through the LLM, which adapts based on the conversation language context.

---

## Error Handling

### Authentication Required

```python
def _create_auth_required_response(self, start_time: float) -> AgentResponse:
    """Create response for unauthenticated users."""
    content = """**Transaction History Requires Authentication**

To view your transaction history, you need to sign in to your Anvil account.

**Once signed in, you can:**
- View all your past transactions
- Filter by chain (Ethereum, Polygon, Arbitrum, etc.)
- Filter by type (Swap, Transfer, Approve, etc.)
- See transaction status (Success, Pending, Failed)
- View 30-day volume analytics
- Track gas costs and fees

**How to Sign In:**
1. Click "Sign In" or "Connect Wallet"
2. Choose your preferred method
3. Return here to view your history
"""
    return AgentResponse(content=content, ...)
```

---

## Testing Strategy

### Unit Tests

```python
def test_empty_balance_message():
    """Test empty balance response."""
    agent = TransactionHistoryAgent(...)
    context = {"portfolio_summary": {"total_value_usd": 0}, "transactions": {}}
    
    result = agent._build_transaction_context(context)
    
    assert "Your balance: $0.00" in result
    assert "Buy crypto" in result

def test_funded_no_transactions_message():
    """Test funded wallet with no transactions."""
    agent = TransactionHistoryAgent(...)
    context = {"portfolio_summary": {"total_value_usd": 500}, "transactions": {}}
    
    result = agent._build_transaction_context(context)
    
    assert "$500.00" in result
    assert "Swap tokens" in result
```

### Integration Tests

```python
async def test_supervisor_routes_to_transaction_history():
    """Test supervisor correctly routes activity queries."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan("my activity", ...)
    
    assert plan.tasks[0].agent_type == AgentType.TRANSACTION_HISTORY
```

---

## Summary

The Activity/Transaction History feature implements:

1. **Hexagonal Architecture**: Clean separation of layers
2. **Balance-Aware Responses**: Different messages based on user state
3. **Multi-Language Support**: 4 languages
4. **Supervisor Integration**: Correct routing for activity queries
5. **Source Attribution**: Proper database and LLM sources
6. **Authentication**: Required for viewing transaction data

All implementations follow established codebase patterns and integrate with existing infrastructure.
