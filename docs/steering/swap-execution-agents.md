# Swap Execution via Agents - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de ejecución de swaps vía agentes proporciona:

1. **Multi-Aggregator Support**: 1inch (single-chain), LiFi (cross-chain), Hyperliquid (perps)
2. **AI Agent Integration**: SwapAgent, ExecutionAgent, TradingAgent
3. **Two-Step Execution**: Simulation → Confirmación → Ejecución
4. **Security Controls**: Límites de transacción, simulación pre-vuelo, aprobación OWASP LLM08
5. **Multi-Language Support**: EN, ES, FR, ZH, PT
6. **Chat Integration**: Ejecución desde conversaciones de chat

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         SWAP EXECUTION VIA AGENTS                                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   User (Chat)   │
                                    │  "swap 1 ETH    │
                                    │   for USDC"     │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │    Intent Detection      │
                              │  (LLM/Keyword Parsing)   │
                              └──────────┬───────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│   SwapAgent   │              │ ExecutionAgent  │              │  TradingAgent   │
│ (Quote/Info)  │              │(Privy Execute)  │              │  (MCP Tools)    │
└───────┬───────┘              └────────┬────────┘              └────────┬────────┘
        │                               │                                │
        └───────────────────────────────┼────────────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────────┐
                              │     SwapHandler          │
                              │  (Quote Aggregation)     │
                              └──────────┬───────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
           ▼                             ▼                             ▼
   ┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
   │    1inch      │           │      LiFi       │           │   Hyperliquid   │
   │ (Single-Chain)│           │ (Cross-Chain)   │           │    (Perps)      │
   └───────────────┘           └─────────────────┘           └─────────────────┘
           │                             │                             │
           └─────────────────────────────┼─────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────────┐
                              │  ExecuteActionCommand    │
                              │   (Two-Step Flow)        │
                              └──────────┬───────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
           │  Simulation   │    │ Confirmation  │    │  Execution    │
           │  (Pre-flight) │    │  (User OK)    │    │  (Privy Tx)   │
           └───────────────┘    └───────────────┘    └───────────────┘
```

---

## Components

### 1. SwapHandler

**Location**: `src/app/application/chat/handlers/swap_handler.py`

Maneja quotes de swap desde el chat, seleccionando automáticamente el mejor agregador.

```python
class SwapHandler:
    """
    Swap routing per CEO spec:
    - Same-chain: Uses 1inch (best rates)
    - Cross-chain: Uses LiFi
    - Perps: Uses Hyperliquid
    """
    
    def __init__(
        self,
        oneinch_client: Optional[OneInchClient] = None,
        lifi_client: Optional[LiFiClient] = None,
        hyperliquid_client: Optional[HyperliquidClient] = None,
    ):
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._hyperliquid = hyperliquid_client
    
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_chain: str = "base",
        to_chain: Optional[str] = None,
        slippage: float = 1.0,
    ) -> SwapHandlerResult:
        """
        Automatically selects best aggregator:
        - Cross-chain: LiFi
        - Same-chain: 1inch (or LiFi fallback)
        """
```

**SwapHandlerResult**:

```python
@dataclass
class SwapHandlerResult:
    content: str           # Formatted response for chat
    quote: Optional[dict]  # Raw quote data
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    price_impact: float
    chain: str
    aggregator: str        # "1inch", "lifi", "hyperliquid"
    latency_ms: int
    language: str = "en"
```

### 2. ExecuteActionCommand

**Location**: `src/app/application/chat/commands/execute_action.py`

Orquesta la ejecución de acciones DeFi desde el chat.

```python
class ExecuteActionCommand:
    """
    Execute recommended actions from chat.
    
    Supported Actions:
    - swap: Token swaps (1inch, LiFi)
    - deposit: Morpho, Aave, Compound
    - withdraw: Morpho, Aave, Compound
    - transfer: Token transfers
    - approve: Token approvals
    - bridge: Cross-chain bridges
    
    Safety Limits:
    - MAX_SWAP_VALUE_USD = $50,000
    - MAX_DEPOSIT_VALUE_USD = $100,000
    - MAX_TRANSFER_VALUE_USD = $10,000
    - CONFIRMATION_EXPIRY = 5 minutes
    """
```

**ActionResult**:

```python
@dataclass
class ActionResult:
    action_id: UUID
    action_type: str              # "swap", "deposit", "withdraw", etc.
    status: str                   # "awaiting_confirmation", "pending", "success"
    requires_confirmation: bool
    confirmation_message: Optional[str]  # Localized message
    simulation: Optional[dict]    # Gas, output amount, warnings
    transaction: Optional[dict]   # Hash, chain, addresses
    summary: str
    enrichment: Optional[dict]    # Action-specific data
    created_at: datetime
    expires_at: Optional[datetime]
```

### 3. SwapAgent

**Location**: `src/app/infrastructure/agents/swap_agent.py`

Agente especializado en operaciones de swap.

```python
class SwapAgent(BaseDeFiAgent):
    """
    Specialized agent for DeFi token swaps.
    
    Tools:
    - get_swap_quote: Get quote from 1inch
    - explain_swap: Explain swap mechanics
    - get_token_info: Token information
    - compare_dex_routes: Compare DEX routes
    - estimate_price_impact: Price impact estimation
    - suggest_optimal_swap_time: Timing suggestions
    """
    
    def get_intent_types(self) -> List[str]:
        return ["trade_swap"]
```

### 4. ExecutionAgentPrivy

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/execution_agent_privy.py`

Agente de ejecución con integración Privy.

```python
class ExecutionAgentPrivy:
    """
    Execution Agent with Privy embedded wallets.
    
    Process:
    1. Parse transaction intent (LLM)
    2. Get user wallet (Privy)
    3. Validate transaction (limits, balance)
    4. Get quote (1inch, Uniswap)
    5. Simulate transaction (pre-flight)
    6. Request user confirmation
    7. Build transaction
    8. Sign via Privy
    9. Submit transaction
    10. Return transaction hash
    
    Safety:
    - Max $10,000 transaction limit
    - 2FA requirement
    - User confirmation required
    - Simulation before execution
    """
```

### 5. TradingAgent

**Location**: `src/app/infrastructure/agno/trading_agent.py`

Agente de trading usando MCP servers.

```python
class TradingAgent(BaseAgent):
    """
    Trading agent using 1inch and Curve MCP tools.
    
    MCP Servers: ["1inch", "curve"]
    
    Capabilities:
    - Best swap prices across DEXes
    - Stablecoin optimizations via Curve
    - Liquidity analysis
    """
```

---

## API Endpoints

### Execute Action

**Endpoint**: `POST /api/v1/user/chat/conversations/{conversation_id}/execute`

**Two-Step Flow**:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Step 1:       │     │   Step 2:       │     │   Step 3:       │
│   Simulate      │ ──▶ │   Confirm       │ ──▶ │   Execute       │
│ confirmed=false │     │ confirmed=true  │     │   (Pending)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Step 1 - Simulation Request**:

```json
POST /api/v1/user/chat/conversations/{id}/execute
{
  "action_type": "swap",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "0.5",
  "chain": "base",
  "confirmed": false
}
```

**Step 1 - Simulation Response**:

```json
{
  "action_id": "uuid",
  "action_type": "swap",
  "status": "awaiting_confirmation",
  "requires_confirmation": true,
  "confirmation_message": "Swap 0.5 ETH → USDC on BASE?",
  "simulation": {
    "success": true,
    "estimated_gas": 200000,
    "estimated_gas_usd": 0.50,
    "output_amount": "1500.00",
    "price_impact": 0.1,
    "warnings": [],
    "errors": []
  },
  "enrichment": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "0.5",
    "chain": "base",
    "output_amount": "1500.00",
    "aggregator": "1inch"
  },
  "expires_at": "2026-01-02T12:05:00Z"
}
```

**Step 2 - Confirmation Request**:

```json
POST /api/v1/user/chat/conversations/{id}/execute
{
  "action_type": "swap",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "0.5",
  "chain": "base",
  "confirmed": true
}
```

**Step 2 - Execution Response**:

```json
{
  "action_id": "uuid",
  "action_type": "swap",
  "status": "pending",
  "requires_confirmation": false,
  "transaction": {
    "hash": "0x...",
    "chain": "base",
    "from_address": "0xUser...",
    "to_address": "0xRouter...",
    "status": "pending"
  },
  "summary": "Executing swap: 0.5 ETH → USDC"
}
```

### Request Schema

```python
class ExecuteActionRequest(BaseModel):
    action_type: ActionType  # swap, deposit, withdraw, approve, transfer, bridge
    chain: str = "base"
    from_token: Optional[str]
    to_token: Optional[str]
    amount: Optional[str]
    protocol: Optional[str]       # For deposits: morpho, aave, compound
    vault_address: Optional[str]  # For Morpho deposits
    recipient: Optional[str]      # For transfers
    slippage: float = 1.0         # 0.1 - 50.0
    to_chain: Optional[str]       # For cross-chain/bridge
    confirmed: bool = False
    reference_message_id: Optional[UUID]
    language: str = "en"
```

### Response Schema

```python
class ExecuteActionResponse(BaseModel):
    action_id: UUID
    action_type: ActionType
    status: ActionStatus
    requires_confirmation: bool
    confirmation_message: Optional[str]
    simulation: Optional[SimulationResult]
    transaction: Optional[TransactionDetails]
    summary: str
    enrichment: Optional[dict]
    created_at: datetime
    expires_at: Optional[datetime]
```

---

## Supported Actions

### 1. Swap

Single-chain or cross-chain token swaps.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Source token (ETH, USDC, etc.) | Yes |
| `to_token` | Destination token | Yes |
| `amount` | Amount to swap | Yes |
| `chain` | Source chain | Yes |
| `to_chain` | Destination chain (cross-chain) | No |
| `slippage` | Slippage tolerance % | No (default 1%) |

**Aggregator Selection**:
- Same-chain: **1inch** (best rates)
- Cross-chain: **LiFi** (bridge aggregator)

### 2. Deposit

Deposit into DeFi protocols.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Token to deposit | Yes |
| `amount` | Amount to deposit | Yes |
| `protocol` | Protocol (morpho, aave, compound) | Yes |
| `vault_address` | Vault address (Morpho) | For Morpho |
| `chain` | Chain | Yes |

### 3. Withdraw

Withdraw from DeFi protocols.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Token to withdraw | Yes |
| `amount` | Amount to withdraw | Yes |
| `protocol` | Protocol | Yes |
| `vault_address` | Vault address | For Morpho |
| `chain` | Chain | Yes |

### 4. Transfer

Transfer tokens to another address.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Token to transfer | Yes |
| `amount` | Amount | Yes |
| `recipient` | Recipient address | Yes |
| `chain` | Chain | Yes |

### 5. Approve

Approve token spending.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Token to approve | Yes |
| `recipient` | Spender address | Yes |
| `amount` | Amount (null = unlimited) | No |
| `chain` | Chain | Yes |

### 6. Bridge

Cross-chain bridge.

| Parameter | Description | Required |
|-----------|-------------|----------|
| `from_token` | Token to bridge | Yes |
| `amount` | Amount | Yes |
| `chain` | Source chain | Yes |
| `to_chain` | Destination chain | Yes |

---

## Aggregator Clients

### 1inch Client

**Location**: `src/app/infrastructure/adapters/external/oneinch_client.py`

```python
class OneInchClient:
    """Single-chain DEX aggregator."""
    
    CHAINS = {
        "ethereum": 1,
        "bsc": 56,
        "polygon": 137,
        "optimism": 10,
        "arbitrum": 42161,
        "base": 8453,
    }
    
    async def get_swap_quote(...) -> SwapQuote
    async def get_swap_data(...) -> SwapTransaction
    async def get_tokens() -> list[Token]
    async def get_token_price(...) -> float
```

### LiFi Client

**Location**: `src/app/infrastructure/adapters/external/lifi_client.py`

```python
class LiFiClient:
    """Cross-chain swap and bridge aggregator."""
    
    CHAINS = {
        "ethereum": 1,
        "polygon": 137,
        "arbitrum": 42161,
        "optimism": 10,
        "base": 8453,
        "bsc": 56,
        "avalanche": 43114,
        "zksync": 324,
    }
    
    async def get_quote(...) -> LiFiQuote
    async def get_routes(...) -> list[LiFiRoute]
    async def get_chains() -> list[dict]
    async def get_tokens(...) -> list[dict]
```

---

## Security Controls

### Transaction Limits

```python
MAX_SWAP_VALUE_USD = Decimal("50000")    # $50,000
MAX_DEPOSIT_VALUE_USD = Decimal("100000") # $100,000
MAX_TRANSFER_VALUE_USD = Decimal("10000") # $10,000
CONFIRMATION_EXPIRY_MINUTES = 5          # 5 minutes
```

### Transaction Approval Service

**Location**: `src/app/infrastructure/security/transaction_approval.py`

Implementa protección OWASP LLM08 (Excessive Agency).

```python
class TransactionApprovalService:
    """
    Protects against LLM-initiated high-risk actions.
    
    High-Risk Transaction Types:
    - wallet_transaction
    - fund_transfer
    - contract_deployment
    - token_swap
    - liquidity_provision
    - stake_assets
    - governance_vote
    
    Risk Levels:
    - LOW: Direct execution
    - MEDIUM: Warning shown
    - HIGH: Approval required
    - CRITICAL: Multi-factor approval
    """
    
    def assess_risk(self, transaction_type, details) -> TransactionRisk
    def requires_approval(self, transaction_type, details) -> bool
    def request_approval(self, transaction_id, user_id, ...) -> TransactionApprovalRequest
    def approve_transaction(self, transaction_id, approver_id) -> bool
    def reject_transaction(self, transaction_id, rejector_id) -> bool
```

### Risk Assessment

```python
# Risk escalation rules
if amount > 1000:
    risk = TransactionRisk.HIGH

if details.get("irreversible"):
    risk = TransactionRisk.CRITICAL

if details.get("affects_multiple_users"):
    risk = TransactionRisk.HIGH

if details.get("external_call"):
    risk = max(risk, TransactionRisk.MEDIUM)
```

---

## Multi-Language Support

### Confirmation Messages

```python
confirm_msgs = {
    "en": f"Swap {amount} {from_token} → {to_token} on {chain.upper()}?",
    "es": f"¿Intercambiar {amount} {from_token} → {to_token} en {chain.upper()}?",
    "fr": f"Échanger {amount} {from_token} → {to_token} sur {chain.upper()} ?",
    "zh": f"在 {chain.upper()} 上将 {amount} {from_token} 兑换为 {to_token}？",
    "pt": f"Trocar {amount} {from_token} → {to_token} em {chain.upper()}?",
}
```

### Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Español |
| `fr` | Français |
| `zh` | 中文 |
| `pt` | Português |

---

## Agent Tools

### SwapAgent Tools

| Tool | Description |
|------|-------------|
| `get_swap_quote` | Get quote from 1inch DEX aggregator |
| `explain_swap` | Explain how a token swap works |
| `get_token_info` | Get token information |
| `compare_dex_routes` | Compare DEX routes for best price |
| `estimate_price_impact` | Estimate price impact |
| `suggest_optimal_swap_time` | Suggest optimal swap timing |

### Tool Implementation

```python
async def get_swap_quote_tool(
    src_token: str,
    dst_token: str,
    amount: str,
    oneinch_client: OneInchClient,
) -> str:
    """Get swap quote from 1inch."""
    # Resolve token addresses
    src_address = COMMON_TOKENS.get(src_token.upper())
    dst_address = COMMON_TOKENS.get(dst_token.upper())
    
    # Convert amount to wei
    decimals = 6 if src_token.upper() in ["USDC", "USDT"] else 18
    amount_wei = str(int(Decimal(amount) * Decimal(10 ** decimals)))
    
    # Get quote
    quote = await oneinch_client.get_quote(
        src=src_address,
        dst=dst_address,
        amount=amount_wei,
    )
    
    return formatted_quote_string
```

---

## Token Address Mappings

### Common Tokens

```python
TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    "base": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
    },
    "arbitrum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    },
}
```

### Token Decimals

| Token | Decimals |
|-------|----------|
| ETH, WETH | 18 |
| USDC, USDT | 6 |
| WBTC | 8 |
| DAI | 18 |

---

## Execution Flow

### Chat to Execution Flow

```
1. User Message: "swap 1 ETH for USDC"
   │
   ▼
2. Intent Detection (LLM/Keywords)
   │ → Detects: action=swap, from_token=ETH, to_token=USDC, amount=1
   │
   ▼
3. SwapHandler.get_swap_quote()
   │ → Selects 1inch (same-chain)
   │ → Returns quote with output amount
   │
   ▼
4. Chat Response: "I can swap 1 ETH for ~3000 USDC. Confirm?"
   │
   ▼
5. User Confirms: "yes" or clicks confirm button
   │
   ▼
6. ExecuteActionCommand.execute(confirmed=false)
   │ → Returns simulation + confirmation message
   │
   ▼
7. Frontend shows confirmation dialog
   │
   ▼
8. ExecuteActionCommand.execute(confirmed=true)
   │ → Builds transaction
   │ → Signs via Privy
   │ → Submits to blockchain
   │
   ▼
9. Returns transaction hash (pending)
```

### Message Parsing

```python
def parse_swap_from_message(self, message: str):
    """
    Parse: "swap 1 ETH for USDC on base"
           "bridge 100 USDC from ethereum to base"
    
    Returns: (amount, from_token, to_token, from_chain, to_chain)
    """
    # Extract amount: regex for numbers
    # Extract tokens: known token list
    # Extract chains: known chain list
    # Detect cross-chain: "bridge", "from", "to" keywords
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **SwapHandler** | `application/chat/handlers/swap_handler.py` | Quote aggregation |
| **ExecuteAction** | `application/chat/commands/execute_action.py` | Action execution |
| **SwapAgent** | `infrastructure/agents/swap_agent.py` | AI agent for swaps |
| **ExecutionAgent** | `adapters/agent_squad/agents/execution_agent_privy.py` | Privy execution |
| **TradingAgent** | `infrastructure/agno/trading_agent.py` | MCP-based trading |
| **SwapTools** | `infrastructure/defi/tools/swap_tools.py` | Agent tools |
| **1inch Client** | `adapters/external/oneinch_client.py` | DEX aggregator |
| **LiFi Client** | `adapters/external/lifi_client.py` | Cross-chain |
| **Approval Service** | `infrastructure/security/transaction_approval.py` | OWASP LLM08 |
| **Schemas** | `presentation/http/schemas/execute.py` | Request/response |
| **Router** | `presentation/http/controllers/chat/router.py` | API endpoint |

---

## Configuration

### Feature Flags

```python
# src/app/setup/config/agent_squad.py
class ExternalAPIsSettings:
    enable_1inch: bool = True
    enable_lifi: bool = True
    enable_hyperliquid: bool = True
```

### Environment Variables

```toml
# config/local/.secrets.toml
[oneinch]
API_KEY = "your-1inch-api-key"

[lifi]
API_KEY = "your-lifi-api-key"  # Optional, higher rate limits
```

---

## Best Practices

### 1. Always Simulate First

```python
# DON'T: Execute directly
result = await execute_command.execute(..., confirmed=True)

# DO: Simulate first, then confirm
simulation = await execute_command.execute(..., confirmed=False)
if user_approves(simulation):
    result = await execute_command.execute(..., confirmed=True)
```

### 2. Handle Confirmation Expiry

```python
# Confirmations expire after 5 minutes
if datetime.utcnow() > action_result.expires_at:
    # Request new simulation
    pass
```

### 3. Validate Token Addresses

```python
def _resolve_token_address(self, token: str, chain: str) -> str:
    if token.startswith("0x"):
        return token  # Already an address
    
    chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
    return chain_tokens.get(token.upper(), token)
```

### 4. Handle Wei Conversions

```python
def _to_wei(self, amount: str, token: str) -> str:
    decimals = 18
    if token.upper() in ["USDC", "USDT"]:
        decimals = 6
    elif token.upper() == "WBTC":
        decimals = 8
    
    return str(int(float(amount) * (10 ** decimals)))
```

### 5. Use Appropriate Slippage

```python
# Default: 1% for most swaps
# High volatility: 2-3%
# Stablecoins: 0.1-0.5%
# Large trades: Consider splitting
```

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| No wallet connected | User hasn't linked wallet | Prompt wallet connection |
| Quote failed | API error or invalid tokens | Retry or show error |
| Insufficient balance | Not enough tokens | Show balance |
| Slippage exceeded | Price moved too much | Increase slippage or retry |
| Confirmation expired | Took too long | Request new simulation |
| Transaction reverted | On-chain failure | Show error, refund gas |

### Error Response

```python
def _no_wallet_response(self, action_id, action_type, language):
    msgs = {
        "en": "No wallet connected. Please connect your wallet.",
        "es": "No hay billetera conectada. Por favor conecta tu billetera.",
        # ...
    }
    return ActionResult(
        status="failed",
        simulation={"success": False, "errors": ["No wallet connected"]},
        summary=msgs.get(language, msgs["en"]),
    )
```

---

**Last Updated**: January 2, 2026
