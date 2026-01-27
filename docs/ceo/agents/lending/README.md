# Lending Workflow Specification

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Complete Specification
**Author**: Claude Code (Senior Python Backend Engineer)

---

## Overview

This directory contains comprehensive specifications for the **Lending Workflow** feature, supporting supply/deposit, borrow, leverage loop, and health factor monitoring across **Aave V3** (port 8085) and **Morpho Protocol** (port 8088).

---

## Document Structure

### 1. [`architecture.md`](./architecture.md)

**Purpose**: Hexagonal architecture design with complete layer separation

**Contents**:
- Domain layer entities and value objects
- Application layer CQRS commands and queries
- Infrastructure layer MCP adapters
- Presentation layer HTTP endpoints
- User context awareness (guest vs authenticated)
- Balance validation flow
- Multi-agent coordination

**Key Highlights**:
- Complete domain modeling for lending positions
- Port-adapter pattern for Aave and Morpho MCP integration
- Health factor monitoring with risk assessment
- Balance checker integration before transactions
- Dishka DI configuration

**Read This First**: Understanding the architecture is critical before implementation.

---

### 2. [`implementation_plan.md`](./implementation_plan.md)

**Purpose**: Detailed 7-week implementation roadmap with tasks and milestones

**Contents**:
- **Phase 1**: Domain modeling and ports (Week 1)
- **Phase 2**: MCP adapter integration (Week 2)
- **Phase 3**: User context awareness (Week 3)
- **Phase 4**: Balance validation flow (Week 4)
- **Phase 5**: Knowledge agent updates (Week 5)
- **Phase 6**: Supervisor configuration (Week 6)
- **Phase 7**: Testing and documentation (Week 7)

**Key Highlights**:
- Task-by-task breakdown with estimated times
- File creation checklists
- Testing requirements
- Risk mitigation strategies
- Success metrics

**Read This Second**: Follow the implementation plan sequentially for best results.

---

### 3. [`database_schema.md`](./database_schema.md)

**Purpose**: Complete PostgreSQL database schema with tables, indexes, and migrations

**Contents**:
- **6 core tables**: positions, supplies, borrows, transactions, preferences, health_checks
- **1 specialized table**: leverage_loop_executions
- **2 views**: user summary and position details
- **Alembic migration template**
- Performance optimization strategies
- Security considerations (RLS policies)

**Key Highlights**:
- UUID primary keys throughout
- Soft delete support
- Health factor tracking with risk levels
- Transaction status tracking
- User preferences for auto-management
- Leverage loop progress tracking

**Read This Third**: Database schema must be implemented early in Phase 1.

---

## Quick Start

### For Developers

1. **Read the architecture** (`architecture.md`) to understand the hexagonal design
2. **Review the implementation plan** (`implementation_plan.md`) to see the roadmap
3. **Set up the database** using schemas from `database_schema.md`
4. **Start with Phase 1** (Domain modeling) and work sequentially

### For Project Managers

1. Review the **7-week timeline** in `implementation_plan.md`
2. Check **success metrics** for tracking progress
3. Review **risk mitigation** strategies for potential blockers
4. Assign developers to phases based on expertise

### For QA Engineers

1. Review **testing requirements** in each phase
2. Check **integration test plans** in Phase 7
3. Review **error handling scenarios** in Phase 4
4. Prepare test cases for multi-agent workflows

---

## Key Features Implemented

### 1. Supply/Deposit Operations
- Automatic wallet signature flow
- Balance validation before execution
- Multi-protocol support (Aave + Morpho)
- Real-time APY tracking

### 2. Borrow Operations (Aave Only)
- Health factor impact calculation
- Pre-borrow safety validation
- Minimum health factor enforcement (default: 1.5)
- Variable vs stable rate selection

### 3. Leverage Loop
- Semi-automatic with sequential signatures (3 signatures required)
- Iteration planning with gas estimation
- Progress tracking in database
- Safety checks at each step

### 4. Health Check Monitoring
- Real-time health factor monitoring
- Risk level classification (low → critical → liquidatable)
- Automated alerts for high-risk positions
- Liquidation price calculation

### 5. Multi-Agent Flows
- Market Scanner Agent (find best rates)
- Risk Agent (assess health factor impact)
- Balance Checker Agent (validate sufficient funds)
- Executor Agent (generate transaction data)

### 6. User Context Awareness
- Guest users: View-only access to rates and market data
- Authenticated users: Full transaction execution
- Different capabilities based on authentication status

---

## Architecture Principles

### Hexagonal Architecture (Clean Architecture)

```
Domain Layer (Business Logic)
    ↓
Application Layer (Use Cases)
    ↓
Infrastructure Layer (External Systems)
    ↓
Presentation Layer (HTTP API)
```

### CQRS Pattern

- **Commands**: Write operations (supply, borrow, repay)
- **Queries**: Read operations (get position, calculate health factor)
- Separate models for commands vs queries

### Port-Adapter Pattern

- **Ports**: Domain interfaces (e.g., `LendingGateway`)
- **Adapters**: Infrastructure implementations (e.g., `AaveMCPAdapter`)
- Protocol-agnostic domain layer

### Dependency Injection (Dishka)

- All dependencies injected via Dishka framework
- Request-scoped services for transactional consistency
- App-scoped services for caching

---

## MCP Server Integration

### Aave MCP Server (Port 8085)

**Tools Available**:
- `get_market_data` - Market rates and liquidity
- `get_user_positions` - User positions with health factor
- `calculate_health_factor` - HF calculation
- `get_available_to_borrow` - Max borrow capacity
- `supply_asset` - Supply operation
- `borrow_asset` - Borrow operation
- `repay_loan` - Repay operation
- `withdraw_supply` - Withdraw operation
- `get_liquidation_risk` - Risk analysis

**Implementation**: `/home/ubuntu/anvil_backend/src/app/infrastructure/mcp/servers/aave_mcp.py`

### Morpho MCP Server (Port 8088)

**Tools Available**:
- `morpho_get_vaults` - List MetaMorpho vaults
- `morpho_get_vault_details` - Vault information
- `morpho_get_vault_apy` - APY breakdown
- `morpho_get_markets` - Morpho Blue markets
- `morpho_get_user_positions` - User vault positions

**Implementation**: `/home/ubuntu/anvil_backend/src/app/infrastructure/mcp/servers/morpho_mcp.py`

**Note**: Morpho only supports supply operations (no borrowing)

---

## Database Schema Summary

### Core Tables

1. **lending_positions**: Aggregate positions per user/protocol/chain
2. **lending_supplies**: Individual supply positions per asset
3. **lending_borrows**: Individual borrow positions per asset (Aave only)
4. **lending_transactions**: All transaction history with status tracking
5. **user_lending_preferences**: User risk settings and preferences
6. **lending_health_checks**: Health monitoring history
7. **leverage_loop_executions**: Leverage loop progress tracking

### Key Relationships

```
lending_positions (1) ──< (many) lending_supplies
lending_positions (1) ──< (many) lending_borrows
lending_positions (1) ──< (many) lending_transactions
lending_positions (1) ──< (many) lending_health_checks
lending_positions (1) ──< (many) leverage_loop_executions
```

---

## Testing Strategy

### Unit Tests
- Domain entities and value objects
- Domain service business logic
- Validation methods

### Integration Tests
- MCP adapter communication
- Database operations
- Multi-agent coordination

### End-to-End Tests
- Supply flow (balance → MCP → position update)
- Borrow flow (position → HF validation → MCP)
- Leverage loop (sequential execution)

---

## Timeline Summary

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | 1 week | Domain modeling and ports |
| Phase 2 | 1 week | MCP adapter integration |
| Phase 3 | 1 week | User context awareness |
| Phase 4 | 1 week | Balance validation flow |
| Phase 5 | 1 week | Knowledge agent updates |
| Phase 6 | 1 week | Supervisor configuration |
| Phase 7 | 1 week | Testing and documentation |
| **Total** | **7 weeks** | **Complete implementation** |

---

## Dependencies

### Existing Infrastructure

- ✅ Aave MCP server (`aave_mcp.py`)
- ✅ Morpho MCP server (`morpho_mcp.py`)
- ✅ Portfolio MCP server (for balance checking)
- ✅ Aave gateway and adapter (`AaveAdapter`, `AaveClient`)
- ✅ Morpho gateway and adapter (`MorphoAdapter`, `MorphoClient`)
- ✅ User context service (`UserContextService`)
- ✅ Intent detector (`IntentDetectorV2`)
- ✅ Conversation service (`ConversationService`)

### New Components Required

- ❌ `LendingPosition` entity
- ❌ `HealthFactor` value object enhancements
- ❌ `LendingService` domain service
- ❌ `LendingGateway` port
- ❌ `BalanceGateway` port
- ❌ `AaveMCPAdapter` (implements `LendingGateway`)
- ❌ `MorphoMCPAdapter` (implements `LendingGateway`)
- ❌ `BalanceChecker` (implements `BalanceGateway`)
- ❌ Lending interactors (Supply, Borrow, Leverage)
- ❌ Database tables (6 tables + 2 views)

---

## Success Metrics

### Technical Metrics
- 100% test coverage for domain layer
- >90% test coverage for application layer
- <500ms average response time for position queries
- >99% uptime for MCP adapters
- Zero health factor calculation errors

### User Metrics
- >80% success rate for supply operations
- >75% success rate for borrow operations
- Zero liquidations due to system errors
- <5% error rate for balance validation

---

## Risk Mitigation

### High-Risk Areas

1. **Health Factor Calculation Accuracy**
   - **Mitigation**: Double-check against on-chain data
   - **Testing**: Compare with Aave UI calculations

2. **MCP Server Availability**
   - **Mitigation**: Fallback to direct RPC calls
   - **Testing**: Simulate MCP unavailability

3. **Transaction Failures After Validation**
   - **Mitigation**: Add slippage buffer, retry logic
   - **Testing**: Test under high gas scenarios

---

## Next Steps

1. ✅ **Review specifications** with team and stakeholders
2. ⬜ **Set up development environment** (ensure MCP servers are running)
3. ⬜ **Create Alembic migration** from `database_schema.md`
4. ⬜ **Begin Phase 1 implementation** (domain modeling)
5. ⬜ **Set up CI/CD pipeline** for automated testing
6. ⬜ **Schedule weekly sync meetings** to track progress

---

## Questions or Issues?

Contact the development team or refer to:
- **Architecture questions**: See `architecture.md`
- **Implementation questions**: See `implementation_plan.md`
- **Database questions**: See `database_schema.md`
- **Existing code**: Check `/home/ubuntu/anvil_backend/src/app/`

---

## Document Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-27 | Initial complete specification |

---

**End of Lending Workflow Specification**
