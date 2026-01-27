# Lending Workflow Implementation Plan

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Implementation Roadmap
**Timeline**: 6 Phases

---

## Overview

This document provides a detailed implementation roadmap for the Lending Workflow feature, covering Supply/Deposit, Borrow, Leverage Loop, and Health Check monitoring across Aave V3 and Morpho Protocol.

---

## Phase 1: Domain Modeling and Ports (Week 1)

### 1.1 Domain Entities

**Task**: Create lending domain entities
**Priority**: Critical
**Estimated Time**: 2 days

#### Files to Create:

```
src/app/domain/entities/lending/
├── lending_position.py          # Aggregate root
├── supply_position.py           # Supply detail
├── borrow_position.py           # Borrow detail (Aave only)
└── leverage_plan.py             # Leverage loop plan
```

#### Implementation Checklist:

- [ ] **Create `LendingPosition` entity**
  - Fields: `position_id`, `user_id`, `protocol`, `chain`, `supplies`, `borrows`, `health_factor`
  - Methods: `can_borrow()`, `requires_repayment()`, `calculate_max_borrow()`
  - Business invariants: HF > 1.0 for healthy positions

- [ ] **Create `SupplyPosition` entity**
  - Fields: `asset`, `amount`, `amount_usd`, `apy`, `is_collateral`, `protocol`, `vault_address`
  - Validation: Amount must be positive

- [ ] **Create `BorrowPosition` entity**
  - Fields: `asset`, `amount`, `amount_usd`, `apy`, `rate_mode`, `debt_token_address`
  - Validation: Only for Aave protocol

- [ ] **Create `LeveragePlan` entity**
  - Fields: `steps`, `final_leverage`, `total_gas_estimate`
  - Method: `calculate_iterations()`

**Testing**:
- Unit tests for all entity methods
- Business invariant validation tests
- Edge case tests (zero amounts, negative values)

---

### 1.2 Value Objects

**Task**: Create immutable value objects
**Priority**: Critical
**Estimated Time**: 1 day

#### Files to Create:

```
src/app/domain/value_objects/lending/
├── health_factor.py             # Already exists, enhance
├── risk_level.py                # Risk classification
├── liquidation_price.py         # Price at which liquidation occurs
└── borrow_capacity.py           # Max safe borrow amount
```

#### Implementation Checklist:

- [ ] **Enhance `HealthFactor` value object**
  - Add `risk_level` property
  - Add `buffer_percentage` calculation
  - Add comparison methods (`__lt__`, `__gt__`)
  - Immutable with `frozen=True`

- [ ] **Create `RiskLevel` enum**
  - Values: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`, `LIQUIDATABLE`
  - Color coding for UI

- [ ] **Create `LiquidationPrice` value object**
  - Calculate price at which HF = 1.0
  - Percentage drop from current price

- [ ] **Create `BorrowCapacity` value object**
  - Max borrow maintaining target HF
  - Conservative vs aggressive recommendations

**Testing**:
- Immutability tests
- Comparison tests
- Edge case tests (infinite HF when no debt)

---

### 1.3 Domain Ports (Interfaces)

**Task**: Define port interfaces
**Priority**: Critical
**Estimated Time**: 1 day

#### Files to Create:

```
src/app/domain/ports/
├── lending_gateway.py           # Main lending port
├── balance_gateway.py           # Balance checking port
└── health_monitor_gateway.py   # Health monitoring port
```

#### Implementation Checklist:

- [ ] **Create `LendingGateway` protocol**
  - Methods: `get_position()`, `supply()`, `borrow()`, `repay()`, `withdraw()`
  - Protocol-agnostic interface

- [ ] **Create `BalanceGateway` protocol**
  - Methods: `get_token_balance()`, `get_native_balance()`
  - Multi-chain support

- [ ] **Create `HealthMonitorGateway` protocol**
  - Methods: `calculate_health_factor()`, `monitor_position()`, `get_liquidation_risk()`
  - Real-time monitoring interface

**Testing**:
- Protocol compliance tests
- Type checking with mypy

---

### 1.4 Domain Services

**Task**: Implement domain business logic
**Priority**: Critical
**Estimated Time**: 2 days

#### Files to Create:

```
src/app/domain/services/
├── lending_service.py           # Core lending logic
├── leverage_calculator.py       # Leverage loop calculations
└── risk_assessor.py             # Risk assessment logic
```

#### Implementation Checklist:

- [ ] **Create `LendingService`**
  - Method: `calculate_leverage_loop()` - Iterative leverage calculation
  - Method: `validate_borrow_safety()` - Pre-borrow safety check
  - Method: `recommend_repay_amount()` - Optimal repay amount
  - No external dependencies (pure domain logic)

- [ ] **Create `LeverageCalculator`**
  - Method: `calculate_iterations()` - Loop iteration plan
  - Method: `estimate_final_position()` - Final leverage multiplier
  - Method: `calculate_total_cost()` - Gas + fees

- [ ] **Create `RiskAssessor`**
  - Method: `assess_liquidation_risk()` - Risk level determination
  - Method: `calculate_buffer()` - Price buffer before liquidation
  - Method: `recommend_action()` - Action recommendation based on risk

**Testing**:
- Unit tests for all calculations
- Integration tests for complex scenarios
- Property-based tests for invariants

---

### 1.5 Domain Exceptions

**Task**: Define domain-specific exceptions
**Priority**: High
**Estimated Time**: 0.5 day

#### Files to Create:

```
src/app/domain/exceptions/
└── lending.py                   # All lending exceptions
```

#### Implementation Checklist:

- [ ] **Create lending exceptions**
  - `LendingError` (base)
  - `InsufficientBalanceError`
  - `UnsafeBorrowError`
  - `HealthFactorTooLowError`
  - `ProtocolNotSupportedError`
  - `LiquidationRiskError`

---

## Phase 2: MCP Adapter Integration (Week 2)

### 2.1 Aave MCP Adapter

**Task**: Implement Aave MCP adapter
**Priority**: Critical
**Estimated Time**: 3 days

#### Files to Create:

```
src/app/infrastructure/adapters/lending/
├── __init__.py
├── aave_mcp_adapter.py          # Aave implementation
└── aave_health_monitor.py       # Health monitoring
```

#### Implementation Checklist:

- [ ] **Create `AaveMCPAdapter` (implements `LendingGateway`)**
  - Constructor: Accept `MCPClient`, `ExternalAPICache`
  - Method: `get_position()` - Call MCP `get_user_positions` tool
  - Method: `supply()` - Call MCP `supply_asset` tool
  - Method: `borrow()` - Call MCP `borrow_asset` tool with HF validation
  - Method: `repay()` - Call MCP `repay_loan` tool
  - Method: `withdraw()` - Call MCP `withdraw_supply` tool
  - Base URL: `http://localhost:8085`

- [ ] **Create `AaveHealthMonitor`**
  - Method: `monitor_position()` - Continuous HF monitoring
  - Method: `get_liquidation_risk()` - Call MCP `get_liquidation_risk` tool
  - Method: `calculate_health_factor()` - Call MCP `calculate_health_factor` tool
  - Alert thresholds: HF < 1.5 (warning), HF < 1.2 (urgent)

- [ ] **Implement caching strategy**
  - Cache key: `aave:position:{chain}:{address}`
  - TTL: 30 seconds (positions are dynamic)
  - Cache invalidation on transactions

- [ ] **Implement error handling**
  - Map MCP errors to domain exceptions
  - Retry logic with exponential backoff
  - Fallback to direct RPC if MCP unavailable

**Testing**:
- Integration tests with mock MCP server
- Error handling tests
- Caching behavior tests

---

### 2.2 Morpho MCP Adapter

**Task**: Implement Morpho MCP adapter
**Priority**: Critical
**Estimated Time**: 2 days

#### Files to Create:

```
src/app/infrastructure/adapters/lending/
├── morpho_mcp_adapter.py        # Morpho implementation
└── morpho_vault_scanner.py      # Vault discovery
```

#### Implementation Checklist:

- [ ] **Create `MorphoMCPAdapter` (implements `LendingGateway`)**
  - Constructor: Accept `MCPClient`, `MorphoGateway`, `ExternalAPICache`
  - Method: `get_position()` - Use existing `MorphoGateway.get_user_positions()`
  - Method: `supply()` - Call MCP `morpho_supply` tool (if exists) or direct vault interaction
  - Note: Morpho only supports supply (no borrow)
  - Base URL: `http://localhost:8088`

- [ ] **Create `MorphoVaultScanner`**
  - Method: `find_best_vaults()` - Scan for highest APY vaults
  - Method: `compare_with_aave()` - Yield comparison
  - Integration with existing `LendingHandler`

- [ ] **Implement vault discovery**
  - Call MCP `morpho_get_vaults` tool
  - Filter by asset, risk tier, minimum APY
  - Sort by APY (highest first)

**Testing**:
- Integration tests with existing Morpho infrastructure
- Vault discovery tests
- Yield comparison tests

---

### 2.3 Balance Checker Adapter

**Task**: Implement balance validation
**Priority**: Critical
**Estimated Time**: 1 day

#### Files to Create:

```
src/app/infrastructure/adapters/portfolio/
└── balance_checker.py           # Balance validation
```

#### Implementation Checklist:

- [ ] **Create `BalanceChecker` (implements `BalanceGateway`)**
  - Constructor: Accept `PortfolioMCPServer`, `Web3Client`
  - Method: `get_token_balance()` - ERC20 balance via Portfolio MCP or Web3
  - Method: `get_native_balance()` - Native token (ETH) balance
  - Fallback: Direct RPC call if MCP unavailable

- [ ] **Implement multi-chain support**
  - Chain mapping: ethereum → 1, polygon → 137, base → 8453, etc.
  - Different RPC endpoints per chain

- [ ] **Implement balance caching**
  - Cache key: `balance:{chain}:{address}:{token}`
  - TTL: 10 seconds (balances change frequently)

**Testing**:
- Multi-chain balance retrieval tests
- Fallback behavior tests
- Caching tests

---

## Phase 3: User Context Awareness (Week 3)

### 3.1 User Context Service

**Task**: Implement user capability detection
**Priority**: High
**Estimated Time**: 2 days

#### Files to Create:

```
src/app/application/common/services/
└── user_context_service.py      # Enhanced with lending capabilities
```

#### Implementation Checklist:

- [ ] **Enhance `UserContextService`**
  - Method: `can_execute_transactions()` - Check if user can execute
  - Method: `get_lending_capabilities()` - Return `LendingCapabilities` object
  - Method: `get_wallet_address()` - Get user's wallet address
  - Method: `is_authenticated()` - Check authentication status

- [ ] **Create `LendingCapabilities` dataclass**
  - Fields: `can_view`, `can_supply`, `can_borrow`, `can_leverage`
  - Guest: Only `can_view=True`
  - Authenticated: All capabilities enabled

- [ ] **Implement permission checks**
  - Decorator: `@requires_authentication` for transaction endpoints
  - Decorator: `@requires_lending_capability` with specific capability check

**Testing**:
- Permission tests for guest users
- Permission tests for authenticated users
- Decorator behavior tests

---

### 3.2 Guest Handler Integration

**Task**: Extend guest handlers for lending
**Priority**: Medium
**Estimated Time**: 1 day

#### Files to Modify:

```
src/app/application/guest/handlers/
├── guest_handler_service.py     # Add lending intent handling
└── lending_multistep.py         # Already exists, enhance
```

#### Implementation Checklist:

- [ ] **Extend `GuestHandlerService`**
  - Add `LENDING_RATES` intent handler
  - Add `LENDING_COMPARISON` intent handler
  - Add educational responses for transaction attempts

- [ ] **Enhance `lending_multistep.py`**
  - Add multi-step flow for lending rate queries
  - Add protocol comparison flow
  - Add "sign up to execute" prompts

**Testing**:
- Guest intent handling tests
- Multi-step flow tests
- Rate limiting tests

---

## Phase 4: Balance Validation Flow (Week 4)

### 4.1 Pre-Transaction Validation

**Task**: Implement balance checks before execution
**Priority**: Critical
**Estimated Time**: 2 days

#### Files to Create:

```
src/app/application/lending/validators/
├── __init__.py
├── balance_validator.py         # Balance validation
├── transaction_validator.py     # Transaction validation
└── health_factor_validator.py   # HF validation
```

#### Implementation Checklist:

- [ ] **Create `BalanceValidator`**
  - Method: `validate_supply()` - Check user has enough tokens
  - Method: `validate_gas()` - Check user has enough gas tokens
  - Method: `estimate_total_cost()` - Calculate total cost including gas

- [ ] **Create `TransactionValidator`**
  - Method: `validate_transaction()` - Comprehensive pre-tx validation
  - Checks: Balance, gas, allowance, contract availability
  - Return: `ValidationResult` with pass/fail and reasons

- [ ] **Create `HealthFactorValidator`**
  - Method: `validate_borrow()` - Check HF after borrow
  - Method: `validate_withdrawal()` - Check HF after withdrawal
  - Method: `get_safe_amount()` - Calculate max safe amount

- [ ] **Integrate into interactors**
  - Add validation step before transaction execution
  - Return clear error messages for failures
  - Suggest corrective actions (e.g., "You need 0.05 ETH for gas")

**Testing**:
- Validation success tests
- Validation failure tests
- Gas estimation tests

---

### 4.2 Error Messages and User Feedback

**Task**: Implement user-friendly error messages
**Priority**: High
**Estimated Time**: 1 day

#### Files to Create:

```
src/app/application/lending/messages/
├── __init__.py
├── error_messages.py            # Error message templates
└── recommendation_messages.py   # Action recommendations
```

#### Implementation Checklist:

- [ ] **Create error message templates**
  - Insufficient balance: "You need {required} {asset} but only have {balance}"
  - Insufficient gas: "You need {required} ETH for gas but only have {balance}"
  - Unsafe borrow: "Borrowing {amount} would reduce your health factor to {hf}. Minimum recommended: {min_hf}"
  - Position at risk: "Your health factor is {hf}. Consider adding collateral or repaying debt."

- [ ] **Create action recommendations**
  - Suggest specific amounts to add/repay
  - Link to helpful resources
  - Provide alternative options

- [ ] **Implement i18n support**
  - English, Spanish, Portuguese, Chinese
  - Use existing `t()` function pattern

**Testing**:
- Message rendering tests
- i18n tests
- Recommendation logic tests

---

## Phase 5: Knowledge Agent Updates (Week 5)

### 5.1 Knowledge Base Updates

**Task**: Update knowledge files with lending workflows
**Priority**: High
**Estimated Time**: 2 days

#### Files to Update:

```
anvil_knowledge/features/
├── lending_morpho.json          # Already exists, enhance
├── lending_aave.json            # Create new
└── lending_workflows.json       # Create new
```

#### Implementation Checklist:

- [ ] **Enhance `lending_morpho.json`**
  - Add workflow examples
  - Add balance validation guidance
  - Add error handling examples

- [ ] **Create `lending_aave.json`**
  - Document supply/borrow/repay/withdraw flows
  - Health factor monitoring guidance
  - Liquidation risk examples
  - Multi-chain support details

- [ ] **Create `lending_workflows.json`**
  - Document leverage loop flow
  - Document health check monitoring
  - Document multi-agent coordination
  - Document guest vs authenticated flows

**Testing**:
- JSON schema validation
- Knowledge retrieval tests

---

### 5.2 Intent Detection Updates

**Task**: Add lending intents to intent detector
**Priority**: High
**Estimated Time**: 1 day

#### Files to Modify:

```
src/app/application/chat/services/
└── intent_detector_v2.py        # Add lending intents
```

#### Implementation Checklist:

- [ ] **Add new lending intents**
  - `LENDING_SUPPLY` - Supply assets intent
  - `LENDING_BORROW` - Borrow assets intent (authenticated only)
  - `LENDING_LEVERAGE` - Leverage loop intent (authenticated only)
  - `LENDING_HEALTH_CHECK` - Health monitoring intent
  - `LENDING_RATES` - Rate comparison intent (guest allowed)
  - `LENDING_POSITION` - Position query intent (authenticated only)

- [ ] **Add intent patterns**
  - Supply: "supply {amount} {asset} to {protocol}"
  - Borrow: "borrow {amount} {asset} from {protocol}"
  - Leverage: "leverage {amount}x on {protocol}"
  - Health check: "check my health factor"
  - Rates: "show lending rates for {asset}"

- [ ] **Add to `RESTRICTED_INTENTS`**
  - `LENDING_SUPPLY`, `LENDING_BORROW`, `LENDING_LEVERAGE`, `LENDING_POSITION`
  - Require authentication for execution

**Testing**:
- Intent detection tests
- Pattern matching tests
- Restriction enforcement tests

---

## Phase 6: Supervisor Configuration Updates (Week 6)

### 6.1 Agent Squad Integration

**Task**: Configure lending agents in supervisor
**Priority**: Medium
**Estimated Time**: 2 days

#### Files to Modify:

```
src/app/domain/services/agent_squad/
└── supervisor_coordinator.py    # Add lending workflows
```

#### Implementation Checklist:

- [ ] **Add lending workflow plans**
  - `LendingSupplyWorkflow` - Market Scanner → Balance Checker → Executor
  - `LendingBorrowWorkflow` - Position Analyzer → Risk Agent → Executor
  - `LeverageLoopWorkflow` - Risk Agent → Loop Calculator → Executor (sequential)

- [ ] **Configure agent tasks**
  - Market Scanner: Find best rates across protocols
  - Risk Agent: Assess health factor impact
  - Balance Checker: Validate sufficient balance
  - Loop Calculator: Plan leverage iterations
  - Executor Agent: Generate transaction data

- [ ] **Implement workflow execution**
  - Sequential execution for leverage loops (3 signatures)
  - Parallel execution for market scanning
  - Error handling and rollback logic

**Testing**:
- Workflow execution tests
- Agent coordination tests
- Error recovery tests

---

### 6.2 Aave Specialist Agent

**Task**: Enhance Aave Specialist agent configuration
**Priority**: Medium
**Estimated Time**: 1 day

#### Files to Modify:

```
src/app/application/agents/library/
└── aave_specialist.py           # Enhance with new workflows
```

#### Implementation Checklist:

- [ ] **Update system prompt**
  - Add leverage loop guidance
  - Add health factor monitoring instructions
  - Add balance validation requirements

- [ ] **Add workflow examples**
  - Supply example with balance check
  - Borrow example with HF calculation
  - Leverage loop example with sequential steps

**Testing**:
- Agent response tests
- Workflow integration tests

---

### 6.3 Shortcuts Configuration

**Task**: Add lending shortcuts
**Priority**: Low
**Estimated Time**: 0.5 day

#### Files to Modify:

```
anvil_knowledge/features/
└── shortcuts.json               # Add lending shortcuts
```

#### Implementation Checklist:

- [ ] **Add lending command shortcuts**
  - "show lending rates for {asset}"
  - "supply {amount} {asset} to {protocol}"
  - "check my lending position"
  - "what's my health factor?"
  - "compare Aave and Morpho rates"

**Testing**:
- Shortcut pattern matching tests
- Intent routing tests

---

## Phase 7: Testing and Documentation (Week 7)

### 7.1 Integration Tests

**Task**: Comprehensive integration testing
**Priority**: Critical
**Estimated Time**: 3 days

#### Test Categories:

- [ ] **End-to-end flow tests**
  - Supply flow: Balance check → MCP call → Position update
  - Borrow flow: Position check → HF validation → MCP call
  - Leverage loop: Sequential execution with 3 signatures

- [ ] **Multi-agent workflow tests**
  - Market Scanner → Risk Agent → Executor coordination
  - Agent failure recovery
  - Timeout handling

- [ ] **User context tests**
  - Guest restrictions enforcement
  - Authenticated user full access
  - Permission checks

- [ ] **Error handling tests**
  - Insufficient balance scenarios
  - MCP server unavailable
  - Health factor violations

---

### 7.2 API Documentation

**Task**: Create comprehensive API documentation
**Priority**: High
**Estimated Time**: 1 day

#### Documentation Files:

```
docs/api/
├── lending_supply.md            # Supply endpoint docs
├── lending_borrow.md            # Borrow endpoint docs
├── lending_position.md          # Position query docs
└── lending_leverage.md          # Leverage loop docs
```

---

### 7.3 User Documentation

**Task**: Create user guides
**Priority**: Medium
**Estimated Time**: 1 day

#### Documentation Files:

```
docs/user_guides/
├── lending_quickstart.md        # Quick start guide
├── health_factor_guide.md       # Understanding health factors
└── leverage_loop_guide.md       # Leverage loop strategy guide
```

---

## Implementation Dependencies

### Critical Path

```
Phase 1 (Domain) → Phase 2 (Adapters) → Phase 4 (Validation) → Phase 7 (Testing)
```

### Parallel Tracks

- **Phase 3 (User Context)** can run parallel with Phase 2
- **Phase 5 (Knowledge)** can run parallel with Phase 4
- **Phase 6 (Supervisor)** can run parallel with Phase 5

---

## Risk Mitigation

### Technical Risks

1. **MCP Server Availability**
   - **Risk**: MCP servers may be unavailable
   - **Mitigation**: Implement fallback to direct RPC calls
   - **Testing**: Simulate MCP unavailability

2. **Health Factor Calculation Accuracy**
   - **Risk**: Incorrect HF calculations could lead to liquidations
   - **Mitigation**: Double-check against on-chain data
   - **Testing**: Compare with Aave UI calculations

3. **Transaction Failures**
   - **Risk**: Transactions may fail after balance validation
   - **Mitigation**: Add slippage buffer, retry logic
   - **Testing**: Test under high gas price scenarios

### User Experience Risks

1. **Guest User Confusion**
   - **Risk**: Guests may not understand why they can't execute
   - **Mitigation**: Clear messaging about authentication requirement
   - **Testing**: User testing with guest accounts

2. **Complex Leverage Flows**
   - **Risk**: Users may not understand 3-signature requirement
   - **Mitigation**: Step-by-step guidance, progress indicators
   - **Testing**: User testing with leverage loops

---

## Success Metrics

### Technical Metrics

- [ ] **100% test coverage** for domain layer
- [ ] **>90% test coverage** for application layer
- [ ] **<500ms** average response time for position queries
- [ ] **>99% uptime** for MCP adapters
- [ ] **Zero health factor calculation errors**

### User Metrics

- [ ] **>80% success rate** for supply operations
- [ ] **>75% success rate** for borrow operations
- [ ] **Zero liquidations** due to system errors
- [ ] **<5% error rate** for balance validation

---

## Timeline Summary

- **Week 1**: Domain modeling and ports
- **Week 2**: MCP adapter integration
- **Week 3**: User context awareness
- **Week 4**: Balance validation flow
- **Week 5**: Knowledge agent updates
- **Week 6**: Supervisor configuration
- **Week 7**: Testing and documentation

**Total Estimated Time**: 7 weeks

---

## Next Steps

1. **Review this plan** with team and stakeholders
2. **Prioritize phases** based on business needs
3. **Assign developers** to each phase
4. **Set up development environment** (MCP servers running)
5. **Begin Phase 1** implementation
