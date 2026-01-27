# Money Market Agents - Quick Index

**🚀 Start Here**: [README.md](./README.md)

---

## Core Documents

### 1. [README.md](./README.md) 📖
**What**: Overview, executive summary, CTO methodology analysis
**When**: Read first for high-level understanding
**Key Topics**:
- System capabilities and features
- Architecture overview diagram
- CTO methodology breakdown (Problem → Solution → Risk Assessment)
- Quick reference for Aave vs Compound
- Integration points and performance characteristics

---

### 2. [MCP_METHODS.md](./MCP_METHODS.md) 🛠️
**What**: Complete reference of all 13 methods (9 Aave + 4 Compound)
**When**: Reference when implementing agent workflows
**Key Topics**:
- **Aave V3 MCP Server** (9 methods):
  - `get_market_data` - Fetch lending rates
  - `get_user_positions` - View user positions
  - `calculate_health_factor` - Risk monitoring
  - `get_available_to_borrow` - Borrowing capacity
  - `supply_asset` - Transaction generation
  - `borrow_asset` - Safe borrow with validation
  - `repay_loan` - Debt repayment
  - `withdraw_supply` - Safe withdrawal
  - `get_liquidation_risk` - Detailed risk analysis

- **Compound V3 Client** (4 methods):
  - `get_market` - Market data
  - `get_markets` - All markets per chain
  - `get_user_position` - User position
  - `get_all_markets` - Cross-chain aggregation

- **Comparison Matrix**: Feature-by-feature comparison
- **Method Selection Guide**: When to use which method
- **Best Practices**: Safety validations, caching, error handling
- **Integration Examples**: Real agent workflows

---

### 3. [database-architecture-spec.md](./database-architecture-spec.md) 🗄️
**What**: Complete PostgreSQL database schema for money market system
**When**: Reference when implementing persistence layer
**Key Topics**:
- **5 Core Tables**:
  - `money_market_protocols` - Protocol registry
  - `money_market_rates` - Time-series rate data with caching
  - `money_market_comparisons` - Audit log
  - `money_market_user_preferences` - User settings
  - `money_market_rate_alerts` - Alert tracking

- **3 Views**:
  - `v_latest_money_market_rates` - Latest cached rates
  - `v_best_supply_rates` - Best APY finder
  - `v_protocol_comparison_summary` - Side-by-side comparison

- **Performance Optimizations**:
  - TTL-based caching (60s)
  - 20+ strategic indexes
  - Covering indexes for hot paths
  - Future partitioning strategy

- **Alembic Migration Template**: Ready-to-use migration script
- **Testing Strategy**: Unit and integration test examples

---

## Document Navigation

### By Role

**For AI Agent Developers**:
1. Start: [README.md](./README.md) (Architecture Overview)
2. Deep Dive: [MCP_METHODS.md](./MCP_METHODS.md) (All available tools)
3. Workflows: See "Agent Workflow Examples" in each method

**For Backend Engineers**:
1. Start: [README.md](./README.md) (System Design)
2. Database: [database-architecture-spec.md](./database-architecture-spec.md) (Schema & migrations)
3. Integration: [MCP_METHODS.md](./MCP_METHODS.md) (API contracts)

**For Product Managers**:
1. Start: [README.md](./README.md) (Capabilities & features)
2. Use Cases: See "Use Cases" sections in [MCP_METHODS.md](./MCP_METHODS.md)

---

## Quick Reference

### Aave V3 MCP
- **Port**: 8085
- **Methods**: 9 comprehensive tools
- **Chains**: 6 (Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Base)
- **Assets**: 10+ per chain (USDC, USDT, DAI, ETH, WETH, WBTC, etc.)
- **Safety**: Built-in HF validation, transaction generation

### Compound V3
- **Integration**: Direct Python client
- **Methods**: 4 core methods
- **Chains**: 4 (Ethereum, Base, Arbitrum, Polygon)
- **Assets**: 2 per chain (USDC, WETH)
- **Focus**: Simplified Comet markets

### Database
- **Tables**: 5 core tables
- **Views**: 3 optimized views
- **Caching**: 60s TTL
- **Performance**: Sub-100ms queries with indexes

---

## Implementation Checklist

### Phase 1: Database Setup ✅
- [ ] Review [database-architecture-spec.md](./database-architecture-spec.md)
- [ ] Create Alembic migration
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify tables created: `\dt money_market*`
- [ ] Insert seed data (protocols)

### Phase 2: MCP Integration ✅
- [ ] Review Aave MCP in [MCP_METHODS.md](./MCP_METHODS.md)
- [ ] Start Aave MCP server: `make mcp.aave` (port 8085)
- [ ] Test health check: `curl http://localhost:8085/health`
- [ ] Initialize Compound client
- [ ] Test sample calls

### Phase 3: Agent Workflows 🚧
- [ ] Implement `MoneyMarketHandler.compare_rates()`
- [ ] Add caching layer (60s TTL)
- [ ] Create fallback logic for RPC failures
- [ ] Test with Hunter AI agent
- [ ] Test with Risk Analyzer agent

### Phase 4: Testing & Monitoring 🚧
- [ ] Unit tests for health factor calculations
- [ ] Integration tests with real RPC calls
- [ ] Performance testing (target: <1s end-to-end)
- [ ] Set up monitoring dashboards
- [ ] Configure alerts for stale data

---

## Common Workflows

### Workflow 1: Rate Comparison
```
User Request → MoneyMarketHandler → Check Cache → [Cache Hit]
                                                 ↓
                                    [Cache Miss] → Aave MCP (Port 8085)
                                                 → Compound Client
                                                 → Store in DB (60s TTL)
                                                 → Return Comparison
```

### Workflow 2: Safe Borrow
```
User "Borrow 5000 USDC" → Execution Agent
                         → Aave MCP: calculate_health_factor
                         → [HF Check] → If estimated HF < 1.2 → BLOCK
                                     → If estimated HF >= 1.2 → Generate TX
                         → Return Transaction Calldata
                         → User Signs & Submits
```

### Workflow 3: Risk Monitoring
```
Risk Analyzer (Every 5 min) → Aave MCP: get_user_positions
                             → Calculate HF
                             → [HF < 1.5] → Send Alert
                             → Log Alert in money_market_rate_alerts
```

---

## Support & Contact

**Questions?**
- Architecture: See [README.md](./README.md) "CTO Methodology" section
- Method Usage: See [MCP_METHODS.md](./MCP_METHODS.md) "Agent Workflow Examples"
- Database: See [database-architecture-spec.md](./database-architecture-spec.md) "Testing Strategy"

**Related Documentation**:
- [Lending Workflow Spec](../lending/README.md) - For Morpho integration
- [Aave Official Docs](https://docs.aave.com/developers/)
- [Compound V3 Docs](https://docs.compound.finance/)

---

**Status**: ✅ Complete Specification | 🚀 Ready for Implementation

**Last Updated**: 2026-01-27
**Version**: 1.0
