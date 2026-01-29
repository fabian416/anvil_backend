# Transfer Workflow Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── workflows/
│       │           └── transfer_workflow_agent.py    # Main workflow agent
│       └── external/
│           ├── web3_client.py                        # Web3 RPC client
│           └── etherscan_client.py                   # Etherscan API client
├── domain/
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py           # Supervisor (workflow routing)
├── setup/
│   └── ioc/
│       └── agent_squad_infrastructure.py             # Dependency injection
└── presentation/
    └── http/
        └── controllers/
            └── chat/
                └── conversations_router.py           # Chat endpoints
```

---

## Core Files

### 1. Transfer Workflow Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/transfer_workflow_agent.py`

**Lines**: ~1,500

**Key Classes**:
- `SafetyCheck` - Individual safety check result
- `RecipientSafetyAnalysis` - Complete safety analysis
- `TransferWorkflowAgent` - Main workflow agent

**Key Methods**:
| Method | Description |
|--------|-------------|
| `process_step()` | Route to appropriate step handler |
| `_handle_parse_request()` | Extract parameters from message |
| `_handle_validate()` | Validate address + safety analysis |
| `_handle_confirm()` | Wait for user confirmation |
| `_handle_execute()` | Generate execute_data |
| `_analyze_recipient_safety()` | Perform all safety checks |
| `_calculate_safety_score()` | Calculate 0-100 score |
| `_format_transfer_review()` | Format confirmation message |
| `_format_safety_section()` | Format safety display |

### 2. Web3 Client

**File**: `src/app/infrastructure/adapters/external/web3_client.py`

**Lines**: ~550

**Key Methods**:
| Method | Description |
|--------|-------------|
| `is_contract()` | Check if address is a smart contract |
| `get_transaction_count()` | Get address nonce |
| `get_balance()` | Get ETH balance |
| `get_token_balance()` | Get ERC20 balance |
| `get_gas_price()` | Get current gas prices |

### 3. Etherscan Client

**File**: `src/app/infrastructure/adapters/external/etherscan_client.py`

**Lines**: ~450

**Key Methods**:
| Method | Description |
|--------|-------------|
| `get_address_label()` | Get label/name for address |
| `get_transaction_count()` | Get transaction count |
| `get_recent_interactions()` | Get txs between addresses |
| `is_contract_verified()` | Check verification status |

**Key Classes**:
- `AddressType` - Enum for address types (EOA, contract, exchange, etc.)
- `AddressLabel` - Label information dataclass
- `TransactionInfo` - Transaction data dataclass

### 4. Authenticated Supervisor

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

**Key Method**: `_is_workflow_continuation()`

**Purpose**: Recognize wallet addresses as valid workflow parameters

```python
# Added pattern for wallet addresses
is_parameter_like = (
    # ... existing patterns ...
    # EVM wallet addresses
    re.match(r'^0x[a-fA-F0-9]{40}$', user_msg_original) or
    # Solana wallet addresses
    re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', user_msg_original)
)
```

### 5. Dependency Injection

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

**Key Providers**:

```python
@provide(scope=Scope.APP)
def provide_web3_client(self, settings: AgentSquadSettings) -> Web3ClientProtocol | None:
    """Provide Web3Client for contract detection."""

@provide(scope=Scope.APP)
def provide_etherscan_client(self, settings: AgentSquadSettings) -> Any:
    """Provide Etherscan client for labels and history."""

@provide
def provide_transfer_workflow_agent(
    self,
    llm_client: LLMClientGateway,
    web3_client: Web3ClientProtocol | None,
    etherscan_client: Any,
) -> TransferWorkflowAgent:
    """Provide Transfer Workflow Agent with safety integrations."""
```

---

## Configuration

### Environment Variables

```bash
# Required for Web3 contract detection
ALCHEMY_API_KEY=your-alchemy-key
# or
RPC_ALCHEMY_API_KEY=your-alchemy-key
# or
INFURA_API_KEY=your-infura-key

# Required for Etherscan labels and history
ETHERSCAN_API_KEY=your-etherscan-key
```

### TOML Secrets

**File**: `config/local/.secrets.toml`

```toml
[rpc]
ALCHEMY_API_KEY = "your-alchemy-key"
INFURA_API_KEY = "your-infura-key"

[etherscan]
API_KEY = "61NWKRRP7RTFYA56C4SPCKHVZ6TJK9A82E"
```

---

## API Endpoints

### Send Message (includes transfer workflow)

```
POST /api/v1/conversations/{conversation_id}/messages
```

**Request**:
```json
{
  "content": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "language": "en"
}
```

**Response** (with execute_data):
```json
{
  "conversation_id": "...",
  "message_id": "...",
  "agent_message": {
    "content": "🔍 **Review Your Transfer**\n...",
    "sources": [...]
  },
  "execute": {
    "action_type": "transfer",
    "provider": "privy",
    "chain": "base",
    "from_token": "USDC",
    "amount": "100",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "slippage": 0.5
  }
}
```

---

## Workflow State

### State Structure

```python
@dataclass
class WorkflowState:
    data: dict = field(default_factory=dict)
    step: str = WorkflowStep.PARSE_REQUEST.value
    error: str | None = None
    cancelled: bool = False
    confirmed: bool = False
    execute_data: dict | None = None
```

### State Data Fields

```python
state.data = {
    "token": "USDC",           # Token symbol
    "amount": "100",           # Amount to transfer
    "recipient": "0x742d...",  # Recipient address
    "chain": "base",           # Blockchain network
    "network": "ethereum",     # Detected network type
    "safety_analysis": {
        "score": 65,
        "risk_level": "medium",
        "address_type": "eoa",
        "is_first_time": True,
        "warnings": ["You haven't sent to this address before"],
        "blockers": [],
    }
}
```

---

## Error Handling

### Exception Hierarchy

```python
# Base workflow error
class WorkflowError(Exception):
    pass

# Specific errors
class InvalidAddressError(WorkflowError):
    """Invalid address format."""

class SafetyBlockedError(WorkflowError):
    """Transfer blocked due to safety issues."""

class InsufficientBalanceError(WorkflowError):
    """User doesn't have enough tokens."""
```

### Recovery Strategies

| Error | Recovery |
|-------|----------|
| Invalid address | Ask for correct address |
| Safety blocked | Explain reason, suggest alternatives |
| Insufficient balance | Suggest buying tokens |
| API timeout | Use fallback (local DB) |
| LLM extraction failed | Use regex fallback |

---

## Multi-Language Support

### Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `pt` | Portuguese |
| `zh` | Chinese |

### Message Templates

```python
msgs = {
    "en": "📤 **Sending:** {amount} {token} {emoji}",
    "es": "📤 **Enviando:** {amount} {token} {emoji}",
    "pt": "📤 **Enviando:** {amount} {token} {emoji}",
    "zh": "📤 **发送:** {amount} {token} {emoji}",
}
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/workflows/test_transfer_workflow.py

# Integration tests
pytest tests/integration/test_transfer_safety.py

# All tests
make code.test
```

### Test Files

- `tests/unit/agents/workflows/test_transfer_workflow.py`
- `tests/unit/adapters/test_web3_client.py`
- `tests/unit/adapters/test_etherscan_client.py`
- `tests/integration/test_transfer_safety.py`

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger("app.infrastructure.adapters.agent_squad.agents.workflows.transfer_workflow_agent").setLevel(logging.DEBUG)
```

### Log Messages

```
[TransferWorkflow] Processing step=parse_request, message=send 100 USDC...
[TransferWorkflow] Extracted recipient from user input: 0x742d35...
[TransferWorkflow] Safety score: 65, risk_level: medium
[TransferWorkflow] Completed step=confirm, has_execute_data=True
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Safety check timeout | Etherscan API slow | Increase timeout, add fallback |
| Address not recognized | Supervisor not continuing workflow | Check `is_parameter_like` patterns |
| NoneType error | Missing recipient in state | Check state extraction logic |

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Safety analysis | <500ms | ~400ms |
| Etherscan API call | <2s | ~1s |
| Web3 contract check | <1s | ~500ms |
| Total workflow step | <3s | ~2s |

### Caching

```python
# Etherscan client caches address labels
self._cache: dict[str, AddressLabel] = {}  # In-memory cache

# Check cache before API call
if address in self._cache:
    return self._cache[address]
```

---

## Deployment Checklist

- [ ] Set `ALCHEMY_API_KEY` or `INFURA_API_KEY`
- [ ] Set `ETHERSCAN_API_KEY`
- [ ] Verify Web3 client connectivity
- [ ] Verify Etherscan API V2 access
- [ ] Test with known addresses
- [ ] Test with unknown addresses
- [ ] Test multi-language support
- [ ] Monitor safety check latency

---

## Related Files

### Supervisor
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/services/agent_squad/guest_supervisor.py`

### Other Workflow Agents
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`

### Base Classes
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py`

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Phase 1: EOA detection, safety score |
| 2026-01-29 | Phase 2: Etherscan API V2 integration |
| 2026-01-29 | Fix: Address input handling |
| 2026-01-29 | Fix: Supervisor wallet address recognition |
