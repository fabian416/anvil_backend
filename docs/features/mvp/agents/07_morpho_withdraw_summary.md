# Morpho Withdraw Implementation - Analysis Summary

**Date**: 2026-01-28  
**Status**: ✅ Analysis Complete - Implementation Spec Ready

---

## Key Findings

### ✅ What Exists

1. **Database Schema**
   - `lending_transactions` table with `withdraw` action_type ✅
   - `lending_positions` table for position tracking ✅
   - `lending_supplies` table for supply amounts ✅

2. **Infrastructure**
   - `/conversations/{id}/execute` endpoint handles `withdraw` action ✅
   - `ExecuteActionCommand._handle_withdraw()` stub exists ✅
   - Aave MCP has `aave_withdraw_supply` as reference implementation ✅
   - Lending agent JSON config references `morpho_withdraw` tool ✅

3. **Flow Architecture**
   - Conversation → Message → Agent Response → Execute Data → User Sign → POST /execute ✅
   - Transaction logging to `lending_transactions` ✅
   - Celery task infrastructure for background processing ✅

### ❌ What's Missing

1. **MCP Tool Implementation**
   - `morpho_withdraw` tool not implemented in `MorphoMCPServer`
   - Only query tools exist (get_vaults, get_positions, etc.)
   - No execution tools for Morpho Blue markets

2. **Morpho Blue Integration**
   - No GraphQL client setup for Morpho Blue API
   - No position fetching from Morpho Blue
   - No transaction building for Morpho Blue withdraw

3. **Celery Background Tasks**
   - No task to confirm withdraw transactions
   - No position synchronization after withdraw
   - No health factor recalculation after withdraw

4. **Database Fields**
   - `lending_transactions.wallet_address` missing (needed for position lookup)
   - `lending_transactions.market_id` missing (needed for Morpho Blue market reference)

---

## Implementation Requirements

### 1. MCP Tool: `morpho_withdraw`

**File**: `src/app/infrastructure/mcp/servers/morpho_mcp.py`

**Requirements**:
- Register `morpho_withdraw` tool
- Implement `_withdraw_handler` method
- Get position from Morpho Blue GraphQL API
- Validate position exists and has sufficient supply
- Calculate health factor impact (if has borrow)
- Build withdraw transaction using Web3.py
- Return transaction data for user signing

**Key Methods Needed**:
- `_get_morpho_blue_positions()` - GraphQL query for user positions
- `_build_withdraw_transaction()` - Web3.py contract interaction
- `_calculate_health_factor()` - Health factor calculation
- `_estimate_health_factor_after_withdraw()` - Impact estimation

### 2. Celery Task: `confirm_withdraw_transaction`

**File**: `src/app/infrastructure/celery/tasks.py`

**Requirements**:
- Wait for transaction confirmation
- Update `lending_transactions` status
- Refresh user position from Morpho Blue
- Update `lending_positions` and `lending_supplies` tables
- Recalculate health factor if needed

**Application Task**: `src/app/application/lending/tasks.py`
- `ConfirmWithdrawTransactionTask` class
- Transaction confirmation logic
- Position synchronization logic
- Health factor recalculation logic

### 3. Database Migration

**File**: `alembic/versions/XXXX_add_morpho_withdraw_fields.py`

**Required Changes**:
```sql
ALTER TABLE lending_transactions
  ADD COLUMN wallet_address VARCHAR(42),
  ADD COLUMN market_id VARCHAR(66);

CREATE INDEX idx_lending_transactions_wallet 
  ON lending_transactions(wallet_address);
```

### 4. Execute Endpoint Integration

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Required Changes**:
- Trigger Celery task after withdraw transaction is saved
- Pass market_id and other metadata to task
- Handle task scheduling errors gracefully

### 5. Workflow Agent Modifications

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`

**Required Changes**:
- Add withdraw action support (currently only handles deposit)
- Add withdraw keywords to restart detection ("withdraw", "remove", "take out")
- Implement `_handle_withdraw_request` method
- Add position fetching for withdraw (get user's existing positions)
- Update execute data builder for withdraw action type
- Add withdraw confirmation flow with health factor validation

### 6. Supervisor Modifications

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

**Required Changes**:
- Add withdraw detection to `_detect_fresh_workflow_start` method
- Ensure routing to `lending_workflow` agent for withdraw requests
- Update workflow continuation logic to handle withdraw confirmations

### 7. Knowledge Agent Updates

**File**: `anvil_knowledge/features/shortcuts.json`

**Required Changes**:
- Add `LENDING_WITHDRAW` intent with patterns:
  - "withdraw USDC", "withdraw from morpho", "remove my supply", "my lendings"
- Update `LENDING_POSITION` intent to include:
  - "my lendings", "my lending positions", "show my deposits"
- Add routing configuration for `LENDING_WITHDRAW` intent

---

## Flow Diagram

```
User Request: "Withdraw 1000 USDC from Morpho"
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Agent processes message                          │
│ Calls morpho_withdraw MCP tool                  │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ MCP Tool: morpho_withdraw                       │
│ 1. Get position from GraphQL API                │
│ 2. Validate supply exists                       │
│ 3. Calculate health factor impact               │
│ 4. Build transaction                            │
│ 5. Return execute_data                          │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Agent Response with execute_data                │
│ User sees transaction preview                   │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ User signs transaction in frontend             │
│ POST /conversations/{id}/execute                │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Execute Endpoint                                 │
│ 1. Save transaction to lending_transactions    │
│ 2. Schedule Celery task                         │
│ 3. Return success response                      │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ Celery Task: confirm_withdraw_transaction       │
│ 1. Wait for transaction confirmation           │
│ 2. Update transaction status                   │
│ 3. Refresh position from Morpho                 │
│ 4. Update lending_positions table              │
│ 5. Recalculate health factor                    │
└─────────────────────────────────────────────────┘
```

---

## Critical Implementation Notes

### 1. Morpho Blue vs MetaMorpho

**Important**: The existing Morpho MCP server only handles **MetaMorpho vaults** (deposit/withdraw shares). This implementation adds support for **Morpho Blue markets** (direct lending positions).

**Key Differences**:
- MetaMorpho: Vault-based, share-based withdrawals
- Morpho Blue: Market-based, asset-based withdrawals with collateral/borrow positions

### 2. Health Factor Validation

**Critical**: Withdraw operations can affect health factor if user has borrow positions. Must:
- Calculate health factor before withdraw
- Estimate health factor after withdraw
- Reject if health factor would drop below 1.3
- Suggest safe withdrawal amount if needed

### 3. GraphQL API Usage

**Free Tier**: Morpho Blue GraphQL API is free and unlimited. Use it for:
- Position discovery
- Market data
- Health factor calculation

**Fallback**: If GraphQL fails, can fall back to direct contract calls (requires RPC provider).

### 4. Transaction Building

**Morpho Blue Contract**: `0xBBBBBbBBBbBBBbBBBbBBBbBBBbBBBbBBBb37eeFfCB`

**Withdraw Function**:
```solidity
function withdraw(
    bytes32 id,        // Market ID (keccak256 hash)
    uint256 assets,    // Amount to withdraw (shares)
    address onBehalf,  // User address
    address to         // Recipient address
) returns (uint256)
```

**Market ID**: Must be keccak256 hash of market parameters. Get from GraphQL API.

---

## Testing Strategy

### Unit Tests
- MCP tool handler with mock GraphQL responses
- Transaction building logic
- Health factor calculation
- Position parsing

### Integration Tests
- Full flow: conversation → execute → Celery task
- Position synchronization
- Health factor updates
- Error handling

### E2E Tests
- Real Morpho Blue position withdrawal on testnet
- Transaction confirmation flow
- Position update verification

---

## Next Steps

1. ✅ **Analysis Complete** - This document
2. ✅ **Implementation Spec** - `07_morpho_withdraw_implementation_spec.md`
3. ⏳ **MCP Tool Implementation** - Add `morpho_withdraw` to MorphoMCPServer
4. ⏳ **Celery Task Implementation** - Create `ConfirmWithdrawTransactionTask`
5. ⏳ **Database Migration** - Add missing fields
6. ⏳ **Integration** - Update execute endpoint
7. ⏳ **Workflow Agent Updates** - Add withdraw support to LendingWorkflowAgent
8. ⏳ **Supervisor Updates** - Add withdraw detection to AuthenticatedSupervisor
9. ⏳ **Knowledge Agent Updates** - Add withdraw and "my lendings" intents
10. ⏳ **Testing** - Unit, integration, E2E tests

---

## References

- **Full Spec**: `07_morpho_withdraw_implementation_spec.md`
- **Morpho Doc**: `07_morpho.md`
- **Database Schema**: `docs/ceo/agents/lending/database_schema.md`
- **Aave Reference**: `src/app/infrastructure/mcp/servers/aave_mcp.py::_withdraw_supply`
- **Execute Endpoint**: `src/app/presentation/http/controllers/chat/conversations_router.py::execute_transaction`
