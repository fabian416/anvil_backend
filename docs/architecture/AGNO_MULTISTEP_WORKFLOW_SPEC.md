# AGNO Multi-Step Workflow Agents for Authenticated Users

**Document**: AGNO-MS-001  
**Version**: 1.0.0  
**Date**: January 22, 2026  
**Status**: 🟡 **Planning Phase** - CTO Analysis Complete  
**Owner**: Backend Team

---

## 🎯 Executive Summary

This specification defines the implementation of **AGNO-based multi-step workflow agents** for authenticated users in the `/api/v1/conversations/{id}/messages` endpoint. The goal is to replace the current intent-based handlers with intelligent, stateful agent workflows that can:

- Execute complex DeFi operations (swap, lending, buy, transfer, money market)
- Maintain conversation state without manual state machines
- Use MCP tools for real-time data
- Provide better UX with natural multi-turn conversations

### Business Value

| Metric | Current (Intent Handlers) | Target (AGNO Agents) |
|--------|---------------------------|---------------------|
| Code Complexity | High (manual state machines) | Low (agent memory) |
| Multi-step UX | Rigid numbered steps | Natural conversation |
| State Management | Manual `pending_action` flags | Built-in agent memory |
| Error Recovery | Limited | Intelligent retry |
| Extensibility | Hard (new handler per feature) | Easy (new tool per feature) |

---

## 1. Current Architecture Analysis

### 1.1 Old Intent-Based System

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User: "lending"                                                │
│       ↓                                                         │
│  IntentDetector → ChatIntent.LENDING                           │
│       ↓                                                         │
│  LendingMultiStepHandler.handle_flow()                         │
│       ↓                                                         │
│  Returns: pending_action="lending_awaiting_asset"              │
│                                                                 │
│  User: "USDC"                                                   │
│       ↓                                                         │
│  Handler checks pending_action                                  │
│       ↓                                                         │
│  Returns: pending_action="lending_awaiting_amount"             │
│                                                                 │
│  ... (manual state machine continues)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Problems with Current Approach:**

1. **Manual State Machines**: Each handler manages its own state via `pending_action` and `*_info` dicts
2. **Rigid Flow**: Steps must follow exact sequence (1→2→3→4)
3. **No Context Awareness**: Can't handle "I changed my mind, use ETH instead"
4. **Code Duplication**: Similar patterns repeated across lending, swap, buy handlers
5. **Hard to Extend**: New operation = new handler + state machine

### 1.2 Existing Handlers to Migrate

| Handler | Location | Multi-Steps |
|---------|----------|-------------|
| `LendingMultiStepHandler` | `application/guest/handlers/lending_multistep.py` | asset → amount → quote → confirm |
| `SwapHandler` | `application/chat/handlers/swap_handler.py` | tokens → amount → quote → confirm |
| `BuyHandler` | `application/chat/handlers/buy_handler.py` | crypto → amount → payment → confirm |
| `MoonPaySwapHandler` | `application/chat/handlers/moonpay_swap_handler.py` | pair → amount → quote → confirm |
| `MoneyMarketHandler` | `application/chat/handlers/money_market_handler.py` | compare → select → execute |

### 1.3 Current Agent Squad Architecture

```
src/app/infrastructure/adapters/agent_squad/agents/
├── chat_agent.py              # Conversation/greetings
├── hunter_ai_agent.py         # Market data, prices
├── knowledge_agent.py         # DeFi education
├── portfolio_agent.py         # Portfolio management
├── wallet_agent.py            # Wallet operations
├── transaction_history_agent.py
├── defi_yield_agent.py        # Yield farming
├── gas_optimizer_agent.py     # Gas prices
├── risk_analyzer_agent.py     # Risk assessment
├── execution_agent_privy.py   # Transaction execution
└── ... (18+ agents total)
```

---

## 2. Proposed AGNO Architecture

### 2.1 AGNO Agent Team Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGNO MULTI-STEP ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User: "I want to swap some ETH to USDC"                       │
│       ↓                                                         │
│  AuthenticatedSupervisorCoordinator                            │
│       ↓ routes to                                               │
│  SwapWorkflowAgent (AGNO Team)                                 │
│       │                                                         │
│       ├── QuoteFinderAgent (MCP: 1inch, LiFi)                  │
│       │     └── memory: {from_token, to_token, quotes}         │
│       │                                                         │
│       ├── ConfirmationAgent                                     │
│       │     └── memory: {selected_quote, user_confirmed}       │
│       │                                                         │
│       └── ExecutorAgent (MCP: Privy, wallet)                   │
│             └── memory: {tx_hash, status}                       │
│                                                                 │
│  Built-in conversation memory handles:                         │
│  - "Actually, make it 0.5 ETH" → Updates amount                │
│  - "Cancel" → Resets workflow                                   │
│  - "What was the quote again?" → Recalls from memory           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Team Structure

```python
# Conceptual structure based on agno-multistep.md

from agno import Agent, Team, Workflow
from agno.tools import Tool

# Tool: 1inch Quote
class OneInchQuoteTool(Tool):
    """Fetch swap quotes from 1inch API."""
    async def execute(self, from_token: str, to_token: str, amount: float, chain: str):
        # Uses existing OneInchClient adapter
        pass

# Tool: LiFi Quote (cross-chain)
class LiFiQuoteTool(Tool):
    """Fetch cross-chain swap quotes from LiFi API."""
    async def execute(self, from_token: str, to_token: str, amount: float, from_chain: str, to_chain: str):
        # Uses existing LiFiClient adapter
        pass

# Tool: Execute Transaction
class PrivyExecuteTool(Tool):
    """Execute transaction via Privy wallet."""
    async def execute(self, tx_data: dict, wallet_address: str):
        # Uses existing Privy integration
        pass

# Agent 1: Quote Finder
quote_agent = Agent(
    name="SwapQuoteFinder",
    instructions="""
    You are a DeFi swap quote specialist.
    
    Extract from user message:
    - from_token: Source token (ETH, USDC, etc.)
    - to_token: Destination token
    - amount: Amount to swap
    - chain: Network (default: base)
    
    Use OneInchQuoteTool for same-chain swaps.
    Use LiFiQuoteTool for cross-chain swaps.
    
    Return quotes in clear format with price impact.
    """,
    tools=[OneInchQuoteTool(), LiFiQuoteTool()],
    memory=True,  # Remember extracted params
)

# Agent 2: Confirmation Handler
confirm_agent = Agent(
    name="SwapConfirmer",
    instructions="""
    You present swap quotes to the user and handle confirmation.
    
    If user says:
    - "yes", "confirm", "do it" → Mark as confirmed, proceed to executor
    - "no", "cancel" → Cancel workflow
    - "change to X ETH" → Update amount, re-fetch quote
    - Questions about the quote → Answer using memory
    
    Track the user's confirmation status.
    """,
    memory=True,
)

# Agent 3: Executor
executor_agent = Agent(
    name="SwapExecutor",
    instructions="""
    You execute confirmed swaps via Privy wallet.
    
    Steps:
    1. Verify user confirmation from memory
    2. Build transaction data from quote
    3. Execute via PrivyExecuteTool
    4. Return transaction hash and status
    
    Handle errors gracefully with retry options.
    """,
    tools=[PrivyExecuteTool()],
    memory=True,
)

# Workflow Team
swap_team = Team(
    agents=[quote_agent, confirm_agent, executor_agent],
    workflow=Workflow.SEQUENTIAL,  # Or PARALLEL for independent tasks
)
```

### 2.3 File Structure

```
src/app/infrastructure/adapters/agent_squad/
├── agents/
│   └── workflows/                    # NEW: AGNO workflow agents
│       ├── __init__.py
│       ├── base_workflow_agent.py    # Base class for workflow agents
│       ├── swap_workflow_agent.py    # Swap multi-step workflow
│       ├── lending_workflow_agent.py # Lending multi-step workflow
│       ├── buy_workflow_agent.py     # Fiat on-ramp workflow
│       ├── transfer_workflow_agent.py # Token transfer workflow
│       └── money_market_workflow_agent.py # Compare & select workflow
├── tools/                            # NEW: AGNO MCP tools
│   ├── __init__.py
│   ├── oneinch_tool.py              # 1inch quote/execute
│   ├── lifi_tool.py                 # LiFi cross-chain
│   ├── morpho_tool.py               # Morpho vault operations
│   ├── aave_tool.py                 # Aave V3 operations
│   ├── privy_tool.py                # Wallet execution
│   └── coingecko_tool.py            # Price data
└── workflow_orchestrator.py          # NEW: Coordinates workflow agents
```

---

## 3. Implementation Plan

### Phase 1: Foundation (Week 1)

| Task | Description | Priority |
|------|-------------|----------|
| 1.1 | Create `base_workflow_agent.py` with AGNO integration | P0 |
| 1.2 | Create MCP tool wrappers for existing adapters | P0 |
| 1.3 | Create `SwapWorkflowAgent` as pilot | P0 |
| 1.4 | Integrate with `AuthenticatedSupervisorCoordinator` | P0 |

### Phase 2: Migration (Week 2)

| Task | Description | Priority |
|------|-------------|----------|
| 2.1 | Create `LendingWorkflowAgent` (Morpho + Aave) | P0 |
| 2.2 | Create `BuyWorkflowAgent` (fiat on-ramp) | P1 |
| 2.3 | Create `TransferWorkflowAgent` | P1 |
| 2.4 | Create `MoneyMarketWorkflowAgent` | P2 |

### Phase 3: Polish (Week 3)

| Task | Description | Priority |
|------|-------------|----------|
| 3.1 | Error handling and retry logic | P0 |
| 3.2 | Multi-language support (i18n) | P1 |
| 3.3 | Telemetry and monitoring | P1 |
| 3.4 | Documentation and tests | P0 |

---

## 4. Technical Specification

### 4.1 Base Workflow Agent Interface

```python
# src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

from app.domain.enums.agent_type import AgentType
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.value_objects.message_content import MessageContent


@dataclass
class WorkflowState:
    """State of a multi-step workflow."""
    step: str  # Current step in workflow
    data: dict[str, Any]  # Accumulated data
    confirmed: bool = False
    cancelled: bool = False
    execute_data: dict[str, Any] | None = None  # For frontend execution modal


class BaseWorkflowAgent(AgentGateway, ABC):
    """
    Base class for AGNO-based multi-step workflow agents.
    
    Subclasses implement specific workflows (swap, lending, etc.)
    while this base class handles:
    - State management via agent memory
    - Tool invocation
    - Error handling
    - Response formatting
    """
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the agent type for this workflow."""
        pass
    
    @property
    @abstractmethod
    def workflow_steps(self) -> list[str]:
        """Define the steps in this workflow."""
        pass
    
    @abstractmethod
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: dict[str, Any],
    ) -> tuple[str, WorkflowState]:
        """
        Process current workflow step.
        
        Returns:
            Tuple of (response_content, updated_state)
        """
        pass
    
    async def execute(
        self,
        message: MessageContent,
        conversation_context: Any,
    ) -> AgentResponse:
        """Execute workflow agent."""
        # Load state from conversation context or initialize
        state = self._load_state(conversation_context) or WorkflowState(
            step=self.workflow_steps[0],
            data={},
        )
        
        # Get user context (wallet, preferences)
        user_context = self._extract_user_context(conversation_context)
        
        # Process current step
        response_content, new_state = await self.process_step(
            message=message,
            state=state,
            user_context=user_context,
        )
        
        # Build response with state for next turn
        return AgentResponse(
            content=response_content,
            agent_type=self.agent_type,
            metadata={
                "workflow_state": new_state.__dict__,
                "execute_data": new_state.execute_data,
            },
        )
```

### 4.2 Swap Workflow Agent Implementation

```python
# src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py

from typing import Any
from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent
from .base_workflow_agent import BaseWorkflowAgent, WorkflowState


class SwapWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step swap workflow.
    
    Steps:
    1. parse_request: Extract tokens and amount
    2. fetch_quote: Get quotes from 1inch/LiFi
    3. confirm: User confirms or modifies
    4. execute: Execute transaction
    """
    
    def __init__(
        self,
        oneinch_client,
        lifi_client,
        llm_client,
    ):
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._llm = llm_client
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.SWAP  # Add to enum
    
    @property
    def workflow_steps(self) -> list[str]:
        return ["parse_request", "fetch_quote", "confirm", "execute"]
    
    async def process_step(
        self,
        message: MessageContent,
        state: WorkflowState,
        user_context: dict[str, Any],
    ) -> tuple[str, WorkflowState]:
        """Process swap workflow step."""
        
        step = state.step
        
        if step == "parse_request":
            # Use LLM to extract swap parameters
            params = await self._extract_swap_params(message.value)
            if not params.get("from_token") or not params.get("to_token"):
                return self._ask_for_tokens(state)
            
            state.data.update(params)
            state.step = "fetch_quote"
            # Fall through to fetch quote immediately
            
        if step == "fetch_quote":
            # Fetch quotes from aggregators
            quote = await self._fetch_best_quote(
                from_token=state.data["from_token"],
                to_token=state.data["to_token"],
                amount=state.data.get("amount", 0),
                chain=state.data.get("chain", "base"),
                wallet=user_context.get("wallet_address"),
            )
            
            if not quote:
                return "❌ Unable to fetch quote. Please try again.", state
            
            state.data["quote"] = quote
            state.step = "confirm"
            return self._format_quote_response(quote, state.data), state
        
        if step == "confirm":
            # Check for confirmation or modification
            action = await self._parse_user_intent(message.value)
            
            if action == "confirm":
                state.confirmed = True
                state.step = "execute"
                # Generate execute_data for frontend modal
                state.execute_data = self._build_execute_data(state.data)
                return self._format_ready_to_execute(state.data), state
                
            elif action == "cancel":
                state.cancelled = True
                return "❌ Swap cancelled. Let me know if you want to try again!", state
                
            elif action == "modify":
                # Extract new parameters and re-fetch quote
                new_params = await self._extract_swap_params(message.value)
                state.data.update(new_params)
                state.step = "fetch_quote"
                return await self.process_step(message, state, user_context)
            
            else:
                return "Would you like to confirm this swap? Reply 'yes' or 'cancel'.", state
        
        if step == "execute":
            # Transaction is executed by frontend via execute_data
            # This step confirms execution or handles errors
            return self._format_execution_pending(state.data), state
        
        return "I didn't understand that. How can I help with your swap?", state
```

### 4.3 Integration with AuthenticatedSupervisorCoordinator

```python
# Updates to src/app/domain/services/agent_squad/authenticated_supervisor.py

def _build_planning_prompt(self, ...):
    """Updated prompt with workflow agent routing."""
    
    return f"""...
    
<rules>
AUTHENTICATED USER MULTI-STEP WORKFLOWS:

For action requests that require multiple steps, route to workflow agents:

1. SWAP WORKFLOW → "swap_workflow"
   - "swap X ETH to USDC" → Start swap workflow
   - User in swap flow → Continue swap_workflow
   
2. LENDING WORKFLOW → "lending_workflow"  
   - "deposit into morpho" → Start lending workflow
   - "earn yield on USDC" → Start lending workflow
   
3. BUY WORKFLOW → "buy_workflow"
   - "buy ETH with card" → Start buy workflow
   - "on-ramp $100" → Start buy workflow
   
4. TRANSFER WORKFLOW → "transfer_workflow"
   - "send 0.5 ETH to 0x..." → Start transfer workflow
   
5. MONEY MARKET WORKFLOW → "money_market_workflow"
   - "compare lending rates" → Start money market workflow

WORKFLOW CONTINUATION:
- Check conversation context for active workflow
- If workflow in progress, route to same workflow agent
- User can say "cancel" to exit any workflow
</rules>
"""
```

---

## 5. Migration Strategy

### 5.1 Feature Flags

```python
# src/app/setup/config/workflow_agents.py

class WorkflowAgentSettings(BaseSettings):
    """Feature flags for workflow agents."""
    
    # Master toggle
    enabled: bool = True
    
    # Per-workflow toggles
    swap_workflow_enabled: bool = True
    lending_workflow_enabled: bool = True
    buy_workflow_enabled: bool = False  # Start disabled
    transfer_workflow_enabled: bool = False
    money_market_workflow_enabled: bool = False
    
    # Fallback to old handlers
    fallback_to_legacy: bool = True
```

### 5.2 Gradual Rollout

1. **Phase 1**: Enable `swap_workflow` for 10% of users (A/B test)
2. **Phase 2**: If metrics positive, enable for all users
3. **Phase 3**: Enable `lending_workflow`
4. **Phase 4**: Enable remaining workflows
5. **Phase 5**: Deprecate old handlers

---

## 6. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Multi-step completion rate | 45% | 75% |
| Average steps to complete | 4.2 | 3.0 |
| Error recovery rate | 20% | 80% |
| User satisfaction (NPS) | +32 | +50 |
| Code lines per workflow | ~800 | ~200 |

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| AGNO integration issues | Medium | High | Fallback to legacy handlers |
| State corruption | Low | High | Validation + logging |
| LLM context pollution | Medium | Medium | Explicit state passing (already fixed) |
| Performance regression | Low | Medium | Benchmark before/after |

---

## 8. Dependencies

### External
- AGNO runtime (to be installed)
- Existing MCP tools infrastructure

### Internal
- `AuthenticatedSupervisorCoordinator` (completed)
- Existing adapter clients (1inch, LiFi, Morpho, Aave)
- Privy wallet integration

---

## 9. Open Questions

1. **AGNO Version**: Which version of AGNO to use? (need to verify compatibility)
2. **Memory Persistence**: Store workflow state in DB or conversation context?
3. **Cross-conversation Memory**: Should agent remember user preferences across conversations?
4. **Error Budget**: What's the acceptable error rate before fallback?

---

## 10. Architecture Diagrams

### 10.1 Overall Architecture

![AGNO Workflow Architecture](https://mermaid.ink/svg/pako:eNqFkk1vozAQhu_8Cotzq1X6dVpVApRWkfBuVYh8GO3BhSFYYW3WNsnm36_ATWJHpMvB-Jl550ueplP7quXakjKNCCHEDB8bzfuWrA1qiMeTvOOfAY2Nf02K8VvD5KBoDN-gs6Osp3-YJhlsC_F4orSi4hZrUgw96p0wSnspkyKDQHZWZUrpWkhulT7rVxmspEVpSdZxY0QjUH_VCFN623RqbyBOXn_8PDFJNiit8TqphcbKCiVJ_n4yFgyKPe-PUVPQOSRnkKOshdxcEaQM0uFwxVkyKDWXpkF9RUEZUCXxQLneop0Rzc9cKtUZiGn25q7_G7JcwELIqh3FXnt3kIsXcWG8B6p036oL8wMkfIcXxkd402J3uLA-QaaEfMVq6yWZH6Sw3CLEpzeb2JuGFXD0Ta7vH_rbs7HY35CaW35DKiUboX9j_VWVF63GjaohPt68EksKy79YDRYJVTX3BmEZMN51aEmmpMRq7knW5Pb2edzx6HPXJ145XDkqmE95QGlAZUCUnesUzAkWAd0F9Bi5lXV0H9BDQE6ZztJT5FbX99EgJw1y0iDOb4gVftFPSgMqA6IBRW4BJtOSRu6tnCD7B7-uR84)

### 10.2 Swap Workflow Sequence

![Swap Workflow Sequence](https://mermaid.ink/svg/pako:eNp9U0tu2zAQ3fcUEwEFUsBRbSfZEIXbQrGQLly4pgR1Z7DUxCIsiQpJWTaKLtsDdJ3T5SQBKTmy68IbLfg-82YepPGxxpLjnWArxYo3AAAVU0ZwUbHSQAxMQ6xRnSDUIrSuUG2Elv_BE0doWJVItX7IZfN5haU54UWWNgvmEEmZ6xM4tHCoZGmwTB3qPvHVZEIJeLphFQz9W5hG92AkxPQu8ByDWkZCYCFrgxZy1KbL0jt9lQZBblCBZVODFYwIzJnSCAt7Hd1mpklnON0axbixKVmh4XIa3Q_c3IEN8u6s85hAiIZn8K2WBnvfiMBIlDyzN_BXaJaPFr9szaKrbrITERgNxje3biJ8gqE_HL8FUVSMm340TawmJuDRwwM9__l7oP7wQ72fzJXgCF-cnrRu7j2Q5YNQxUfv7D7XBDriUSs71MclBLI0oqzx-P6vJ50xtQbeGmH6zwYLZOnOFohb5LXBC--AEJL98zJlhhH4ybgRsiSu7gH4vv_r7AY3tlBn4Bhh60kz2ezfYSZTlr_uFxIIcsHXJ7KIwFyJzc512IU6bDAkYLbLjOmMwHA7Gl_7vt9HC_frPj_9dn8NcFlUORq8gOh7r_BeAH8_EOY)

---

## 11. References

- [AGNO Runtime Spec](./archive/historical/AGNO_RUNTIME_INTEGRATION_SPEC.md)
- [agno-multistep.md](../../agno-multistep.md) - Original AGNO example
- [Guest/Auth Supervisor Separation](./guest_authenticated_supervisor_separation.md)
- [Hexagonal Architecture Rules](../.cursor/rules/hexagonal-architecture.mdc)
