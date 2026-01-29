# Transfer Workflow Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **Transfer Workflow** feature, supporting secure token transfers with advanced safety analysis.

### Key Features

- **Multi-Step Workflow**: Parse → Validate → Safety Check → Confirm → Execute
- **Safety Analysis**: EOA detection, Etherscan labels, interaction history
- **Multi-Language Support**: English, Spanish, Portuguese, Chinese
- **Address Validation**: EVM (Ethereum, Base, Polygon) and Solana
- **Known Address Database**: Exchanges, DeFi protocols, risky addresses

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TRANSFER ARCHITECTURE                             │
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
│  Authenticated│    │  TransferWorkflow │    │   Workflow      │
│  Supervisor   │    │  Agent           │    │   State Manager │
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │    Domain Layer      │
                    │  (Safety Analysis)   │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  SafetyCheck  │    │  RecipientSafety │    │   WorkflowState │
│  (Dataclass)  │    │  Analysis        │    │                 │
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │ Infrastructure Layer │
                    │    (Adapters)        │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Web3Client   │    │  EtherscanClient │    │  Known Address  │
│  (Contract    │    │  (Labels, History)│    │  Database       │
│   Detection)  │    │                  │    │                 │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Data Structures

#### 1. `SafetyCheck` Dataclass

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/transfer_workflow_agent.py`

```python
@dataclass
class SafetyCheck:
    """Result of a single safety check."""
    name: str           # Check name (e.g., "Address Type")
    status: str         # "pass", "warn", "fail"
    emoji: str          # Display emoji
    details: str | None # Additional details
```

#### 2. `RecipientSafetyAnalysis` Dataclass

```python
@dataclass
class RecipientSafetyAnalysis:
    """Complete safety analysis for a recipient address."""
    address: str            # Recipient address
    safety_score: int       # 0-100
    risk_level: str         # "low", "medium", "high", "critical"
    address_type: str       # "eoa", "contract", "unknown"
    is_first_time: bool     # First-time recipient
    checks: list[SafetyCheck]    # Individual check results
    warnings: list[str]     # Warning messages
    blockers: list[str]     # Blocking issues (prevents transfer)
    
    @property
    def risk_emoji(self) -> str:
        """Get emoji for risk level."""
        return {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(self.risk_level, "⚪")
    
    @property
    def is_safe(self) -> bool:
        """Check if transfer should be allowed."""
        return len(self.blockers) == 0
```

### Workflow States

```python
class WorkflowStep(str, Enum):
    """Workflow step states."""
    PARSE_REQUEST = "parse_request"   # Extract parameters
    FETCH_DATA = "fetch_data"         # Validate address, safety check
    CONFIRM = "confirm"               # Wait for user confirmation
    EXECUTE = "execute"               # Generate execute_data
    COMPLETED = "completed"           # Transfer complete
    CANCELLED = "cancelled"           # User cancelled
```

### Known Address Database

```python
# Known contract labels (exchanges, protocols, etc.)
KNOWN_CONTRACTS = {
    # Exchanges (Base chain)
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": {
        "name": "Uniswap Universal Router",
        "category": "exchange",
        "safe": True
    },
    "0x2626664c2603336e57b271c5c0b26f421741e481": {
        "name": "Uniswap V3 Router",
        "category": "exchange",
        "safe": True
    },
    "0x6131b5fae19ea4f9d964eac0408e4408b66337b5": {
        "name": "Hyperliquid Bridge",
        "category": "bridge",
        "safe": True
    },
    "0xcdac0d6c6c59727a65f871236188350531885c43": {
        "name": "Coinbase Commerce",
        "category": "exchange",
        "safe": True
    },
}

# Known scam/risky addresses
KNOWN_RISKY_ADDRESSES: set[str] = set()
```

---

## Application Layer

### TransferWorkflowAgent

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/transfer_workflow_agent.py`

```python
class TransferWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step token transfer workflow agent.
    
    Steps:
    1. parse_request: Extract token, amount, recipient
    2. validate: Validate address format and perform safety analysis
    3. confirm: Show transfer details with safety info
    4. execute: Generate execute_data for frontend
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway | None = None,
        web3_client: Web3Client | None = None,
        etherscan_client: EtherscanClient | None = None,
    ):
        super().__init__(llm_client=llm_client)
        self._web3_client = web3_client
        self._etherscan_client = etherscan_client
```

### Step Handlers

#### 1. Parse Request Handler

```python
async def _handle_parse_request(
    self,
    message: MessageContent,
    state: WorkflowState,
    user_context: UserContext,
) -> tuple[str, WorkflowState]:
    """Extract token, amount, recipient from user message."""
    
    # Try LLM extraction
    params = await self._extract_params_with_llm(
        message=text,
        param_schema={
            "token": "string (Token symbol: ETH, USDC, etc.)",
            "amount": "number (Amount to transfer)",
            "recipient": "string (Wallet address 0x... or Solana)",
            "chain": "string (Blockchain network)",
        },
        examples=[...]
    )
    
    # Store in state
    state.data["token"] = token.upper()
    state.data["amount"] = amount
    state.data["recipient"] = recipient
```

#### 2. Validate Handler (with Safety Analysis)

```python
async def _handle_validate(
    self,
    message: MessageContent,
    state: WorkflowState,
    user_context: UserContext,
) -> tuple[str, WorkflowState]:
    """Validate recipient address and perform safety checks."""
    
    # Validate address format
    validation = self._validate_address(recipient)
    
    if not validation["valid"]:
        return self._format_invalid_address(recipient, language), state
    
    # Perform safety analysis
    safety_analysis = await self._analyze_recipient_safety(
        recipient=recipient,
        user_context=user_context,
    )
    
    # Store in state
    state.data["safety_analysis"] = {
        "score": safety_analysis.safety_score,
        "risk_level": safety_analysis.risk_level,
        ...
    }
    
    # Check for blockers
    if not safety_analysis.is_safe:
        return self._format_blocked_transfer(safety_analysis, language), state
    
    # Build execute_data and confirm
    state.execute_data = self._build_transfer_execute_data(...)
    return self._format_transfer_review(state.data, language), state
```

#### 3. Safety Analysis Method

```python
async def _analyze_recipient_safety(
    self,
    recipient: str,
    user_context: UserContext,
) -> RecipientSafetyAnalysis:
    """
    Analyze recipient wallet safety (Phase 2 - Enhanced).
    
    Checks:
    1. EOA vs Smart Contract detection (web3)
    2. Known address labels - local + Etherscan API
    3. First-time recipient detection via Etherscan
    4. Known risky addresses (local blocklist)
    5. Contract verification status (Etherscan)
    """
    
    checks: list[SafetyCheck] = []
    warnings: list[str] = []
    blockers: list[str] = []
    
    # Check 1: Known addresses (local database)
    known_info = KNOWN_CONTRACTS.get(recipient_lower)
    
    # Check 2: Etherscan API label lookup
    if self._etherscan_client and not known_info:
        label_info = await self._etherscan_client.get_address_label(recipient)
    
    # Check 3: Known risky/scam addresses
    if recipient_lower in KNOWN_RISKY_ADDRESSES:
        blockers.append("This address has been flagged as risky")
    
    # Check 4: EOA vs Contract detection
    if self._web3_client:
        is_contract = await self._web3_client.is_contract(recipient)
    
    # Check 5: Interaction history
    if self._etherscan_client and user_wallet:
        interactions = await self._etherscan_client.get_recent_interactions(
            from_address=user_wallet,
            to_address=recipient,
        )
        is_first_time = len(interactions) == 0
    
    # Calculate score and return
    safety_score = self._calculate_safety_score(...)
    return RecipientSafetyAnalysis(...)
```

---

## Infrastructure Layer

### Web3Client

**Location**: `src/app/infrastructure/adapters/external/web3_client.py`

```python
class Web3Client:
    """Web3 client for blockchain interactions."""
    
    async def is_contract(self, address: str) -> bool:
        """
        Check if address is a smart contract or EOA.
        
        Uses eth_getCode to check for bytecode.
        """
        result = await self._call_rpc("eth_getCode", [address, "latest"])
        return result not in ("0x", "0x0", "")
    
    async def get_transaction_count(self, address: str) -> int:
        """Get nonce (number of transactions sent)."""
        result = await self._call_rpc("eth_getTransactionCount", [address, "latest"])
        return int(result, 16)
```

### EtherscanClient

**Location**: `src/app/infrastructure/adapters/external/etherscan_client.py`

```python
class EtherscanClient:
    """
    Etherscan API V2 client for address labels and transaction history.
    
    Uses unified endpoint with chainid parameter.
    """
    
    API_V2_BASE_URL = "https://api.etherscan.io/v2/api"
    
    CHAIN_IDS = {
        "ethereum": 1,
        "base": 8453,
        "arbitrum": 42161,
        "optimism": 10,
        "polygon": 137,
    }
    
    async def get_address_label(self, address: str) -> AddressLabel:
        """Get label information for an address."""
        
        # Check local known addresses first
        label = self._check_known_addresses(address)
        if label:
            return label
        
        # Try Etherscan API
        params = self._build_params({
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
        })
        response = await self._client.get(self._base_url, params=params)
        return self._parse_label_response(response)
    
    async def get_recent_interactions(
        self,
        from_address: str,
        to_address: str,
        limit: int = 5,
    ) -> list[TransactionInfo]:
        """Get recent transactions between two addresses."""
        
        params = self._build_params({
            "module": "account",
            "action": "txlist",
            "address": from_address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
        })
        response = await self._client.get(self._base_url, params=params)
        
        # Filter for transactions to recipient
        return [tx for tx in response if tx["to"] == to_address][:limit]
```

---

## Presentation Layer

### Chat Endpoint Integration

The transfer workflow integrates with the existing chat system:

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
        result = await supervisor.execute_workflow(...)
    
    # Transfer workflow handled by supervisor
    # Returns execute_data for frontend modal
```

### Execute Data Structure

```python
{
    "action_type": "transfer",
    "provider": "privy",
    "chain": "base",
    "from_token": "USDC",
    "amount": "100",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "slippage": 0.5,
}
```

---

## Dependency Injection

### IoC Configuration

**Location**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide(scope=Scope.APP)
def provide_web3_client(self, settings: AgentSquadSettings) -> Web3ClientProtocol | None:
    """Provide Web3Client for blockchain queries."""
    alchemy_key = os.getenv("ALCHEMY_API_KEY")
    return Web3Client(alchemy_api_key=alchemy_key, chain=Chain.BASE)

@provide(scope=Scope.APP)
def provide_etherscan_client(self, settings: AgentSquadSettings) -> Any:
    """Provide Etherscan client for address labels."""
    api_key = os.getenv("ETHERSCAN_API_KEY")
    return EtherscanClient(api_key=api_key, network="base", use_v2_api=True)

@provide
def provide_transfer_workflow_agent(
    self,
    llm_client: LLMClientGateway,
    web3_client: Web3ClientProtocol | None,
    etherscan_client: Any,
) -> TransferWorkflowAgent:
    """Provide Transfer Workflow Agent with safety integrations."""
    return TransferWorkflowAgent(
        llm_client=llm_client,
        web3_client=web3_client,
        etherscan_client=etherscan_client,
    )
```

---

## Error Handling

### Workflow Errors

| Error | Cause | User Message |
|-------|-------|--------------|
| `InvalidAddressError` | Address format invalid | "Invalid address format" |
| `SafetyBlockedError` | Address flagged as risky | "Transfer blocked for safety" |
| `InsufficientBalanceError` | Not enough tokens | "Insufficient balance" |
| `WorkflowCancelledError` | User cancelled | "Transfer cancelled" |

### Recovery Strategies

1. **Invalid Address**: Ask user to provide correct address
2. **Safety Blocked**: Explain reason, suggest alternatives
3. **Insufficient Balance**: Suggest buying tokens
4. **API Errors**: Fall back to local known addresses

---

## Testing Strategy

### Unit Tests

```python
def test_safety_score_calculation():
    """Test safety score calculation."""
    agent = TransferWorkflowAgent()
    
    # Known safe address
    score = agent._calculate_safety_score(
        is_contract=True,
        is_known=True,
        is_known_safe=True,
        is_first_time=False,
        has_blockers=False,
        is_verified=True,
        previous_interactions=5,
    )
    assert score >= 90  # High trust

def test_address_validation():
    """Test address format validation."""
    agent = TransferWorkflowAgent()
    
    # Valid EVM address
    result = agent._validate_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    assert result["valid"] is True
    assert result["network"] == "ethereum"
    
    # Invalid address
    result = agent._validate_address("not-an-address")
    assert result["valid"] is False
```

### Integration Tests

```python
async def test_etherscan_label_lookup():
    """Test Etherscan API integration."""
    client = EtherscanClient(api_key="...", network="base")
    
    # Known contract (Uniswap)
    label = await client.get_address_label("0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad")
    assert label.label == "Uniswap Universal Router"
    assert label.is_verified is True

async def test_interaction_history():
    """Test interaction history lookup."""
    client = EtherscanClient(api_key="...", network="base")
    
    interactions = await client.get_recent_interactions(
        from_address="0xSender...",
        to_address="0xRecipient...",
    )
    # Returns list of previous transactions
```

### E2E Tests

```python
async def test_complete_transfer_flow():
    """Test complete transfer workflow."""
    # 1. User initiates transfer
    response1 = await send_message("send 100 USDC to 0x742d...")
    assert "Review Your Transfer" in response1.content
    
    # 2. User confirms
    response2 = await send_message("yes")
    assert response2.execute is not None
    assert response2.execute["action_type"] == "transfer"
```

---

## Summary

The Transfer Workflow implements:

1. **Hexagonal Architecture**: Clean separation of layers
2. **Multi-Step Workflow**: Structured state machine
3. **Safety Analysis**: Multi-layer security checks
4. **External Integrations**: Web3 RPC + Etherscan API V2
5. **Multi-Language Support**: 4 languages
6. **Dependency Injection**: Dishka framework
7. **Error Handling**: Graceful recovery

All implementations follow established codebase patterns and integrate with existing infrastructure.
