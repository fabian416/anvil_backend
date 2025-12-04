# Granular Feature Flags Specification

## Executive Summary

**Objective:** Implement granular enable/disable controls for every MCP server, agent, and project template via environment configuration.

**Scope:**
- 6 MCP Servers (DeFiLlama, 1inch, The Graph, CoinGecko, Aave, Portfolio)
- 4 Agno Agents (Trading, Lending, Portfolio, Analytics)
- 5 Project Templates (Swing Trader, Arbitrage Hunter, Portfolio Manager, Conservative Investor, Day Trader)

**Total Flags:** 15 granular controls

**Duration:** 6-9 hours  
**Value:** Enterprise-grade operational control

---

## 1. MCP Server Flags (6 Servers)

### Current MCP Servers

| Server | File | Purpose |
|--------|------|---------|
| DeFiLlama | `defillama_mcp.py` | TVL, protocol data, yield farming |
| 1inch | `oneinch_mcp.py` | DEX aggregation, swap quotes |
| The Graph | `thegraph_mcp.py` | Blockchain indexing, subgraph queries |
| CoinGecko | `coingecko_mcp.py` | Market data, price feeds |
| Aave | `aave_mcp.py` | Lending protocol integration |
| Portfolio | `portfolio_mcp.py` | Portfolio tracking, analytics |

### Proposed Configuration

```toml
[mcp]
enabled = true  # Master switch for all MCP servers

[mcp.servers]
defillama_enabled = true  # TVL & protocol data
oneinch_enabled = true  # DEX aggregation
thegraph_enabled = true  # Blockchain indexing
coingecko_enabled = true  # Market data
aave_enabled = true  # Lending protocol
portfolio_enabled = true  # Portfolio tracking
```

### Use Cases

**Development (Cost Optimization):**
```toml
[mcp.servers]
defillama_enabled = true  # Free tier
oneinch_enabled = false  # Paid API
thegraph_enabled = false  # Paid API
coingecko_enabled = true  # Free tier
```

**Production (All Features):**
```toml
[mcp.servers]
defillama_enabled = true
oneinch_enabled = true
thegraph_enabled = true
coingecko_enabled = true
aave_enabled = true
portfolio_enabled = true
```

**Testing (Minimal):**
```toml
[mcp.servers]
defillama_enabled = false
oneinch_enabled = false
thegraph_enabled = false
coingecko_enabled = true  # Only basic market data
```

---

## 2. Agno Agent Flags (4 Agents)

### Current Agno Agents

| Agent | File | Purpose |
|-------|------|---------|
| Trading Agent | `trading_agent.py` | Trade execution, strategy analysis |
| Lending Agent | `lending_agent.py` | Lending/borrowing recommendations |
| Portfolio Agent | `portfolio_agent.py` | Portfolio optimization, rebalancing |
| Analytics Agent | `analytics_agent.py` | Data analysis, insights |

### Agent Router

- `AgentRouter` (`agent_router.py`) - Routes queries to appropriate agent
- `AgentType` enum: `TRADING`, `LENDING`, `PORTFOLIO`, `ANALYTICS`

### Proposed Configuration

```toml
[agno]
enabled = true  # Master switch for all Agno agents
intent_classification_enabled = true  # Auto-route to agents
fallback_to_general = true  # Fallback if agent disabled

[agno.agents]
trading_enabled = true  # Trade execution & strategy
lending_enabled = true  # Lending/borrowing
portfolio_enabled = true  # Portfolio optimization
analytics_enabled = true  # Data analysis & insights
```

### Use Cases

**Production (All Agents):**
```toml
[agno.agents]
trading_enabled = true
lending_enabled = true
portfolio_enabled = true
analytics_enabled = true
```

**Conservative Mode (No Trading):**
```toml
[agno.agents]
trading_enabled = false  # Disable trade execution
lending_enabled = true  # Allow lending info
portfolio_enabled = true  # Allow portfolio advice
analytics_enabled = true  # Allow analysis
```

**Read-Only Mode:**
```toml
[agno.agents]
trading_enabled = false  # No execution
lending_enabled = false  # No execution
portfolio_enabled = true  # Analysis only
analytics_enabled = true  # Analysis only
```

---

## 3. Project Template Flags (5 Templates)

### Current Project Templates

| Template | Slug | Target User | Tools |
|----------|------|-------------|-------|
| DeFi Swing Trader | `defi-swing-trader` | Intermediate | Hunter AI (5 tools) |
| Arbitrage Hunter | `arbitrage-hunter` | Expert | ULTRA (3 tools) + Risk |
| AI Portfolio Manager | `ai-portfolio-manager` | Long-term | Sentiment, Risk, Portfolio |
| Conservative Investor | `conservative-investor` | Beginner | Sentiment, Risk (limited) |
| Day Trader Pro | `day-trader-pro` | Expert | Hunter AI (4 tools) |

### Proposed Configuration

```toml
[projects]
enabled = true  # Master switch for projects
templates_enabled = true  # Master switch for templates

[projects.templates]
defi_swing_trader_enabled = true  # Intermediate swing trading
arbitrage_hunter_enabled = true  # Expert arbitrage
ai_portfolio_manager_enabled = true  # Long-term portfolio
conservative_investor_enabled = true  # Beginner safety
day_trader_pro_enabled = true  # Expert day trading
```

### Use Cases

**Public Launch (Safe Templates Only):**
```toml
[projects.templates]
defi_swing_trader_enabled = true  # Safe for intermediate
arbitrage_hunter_enabled = false  # Too risky for launch
ai_portfolio_manager_enabled = true  # Safe long-term
conservative_investor_enabled = true  # Beginner-friendly
day_trader_pro_enabled = false  # Too aggressive for launch
```

**Enterprise (Custom Only):**
```toml
[projects]
templates_enabled = false  # No pre-built templates
# Force admins to create custom projects
```

**Beta Testing (Limited):**
```toml
[projects.templates]
defi_swing_trader_enabled = true  # Test swing trading
arbitrage_hunter_enabled = true  # Test arbitrage
ai_portfolio_manager_enabled = false  # Not ready
conservative_investor_enabled = true  # Always available
day_trader_pro_enabled = false  # Not ready
```

---

## 4. Implementation Plan

### Phase 1: Analysis & Specification (COMPLETE) ✅

**Deliverables:**
- ✅ Identify all MCP servers (6 servers)
- ✅ Identify all Agno agents (4 agents)
- ✅ Identify all project templates (5 templates)
- ✅ Define configuration structure
- ✅ Document use cases

### Phase 2: MCP Server Flags (1-2 hours)

**Tasks:**
1. Create `MCPSettings` config class
2. Add TOML configuration for MCP servers
3. Update `MCPManager` to respect flags
4. Update each MCP server to check enabled flag
5. Add tests for MCP server toggles

**Files to Modify:**
- `src/app/setup/config/mcp.py` (NEW)
- `src/app/infrastructure/mcp/manager.py`
- `src/app/infrastructure/mcp/servers/*.py` (6 files)
- `config/local/config.toml`
- `tests/integration/mcp/test_mcp_flags.py` (NEW)

### Phase 3: Agent Flags (1-2 hours)

**Tasks:**
1. Create `AgnoSettings` config class
2. Add TOML configuration for agents
3. Update `AgentRouter` to respect flags
4. Update agent routing logic
5. Add fallback behavior
6. Add tests for agent toggles

**Files to Modify:**
- `src/app/setup/config/agno.py` (update existing)
- `src/app/infrastructure/agno/agent_router.py`
- `src/app/infrastructure/agno/*.py` (4 agent files)
- `config/local/config.toml`
- `tests/integration/agno/test_agent_flags.py` (NEW)

### Phase 4: Project Template Flags (1 hour)

**Tasks:**
1. Create `ProjectTemplateSettings` config class
2. Add TOML configuration for templates
3. Update `create_project_from_template` to check flags
4. Update project listing endpoints
5. Add tests for template toggles

**Files to Modify:**
- `src/app/setup/config/projects.py` (NEW)
- `src/app/application/projects/templates/project_templates.py`
- `src/app/presentation/http/controllers/admin/projects_router.py`
- `config/local/config.toml`
- `tests/integration/projects/test_template_flags.py` (NEW)

### Phase 5: Update Documentation (1 hour)

**Tasks:**
1. Update `FEATURE_FLAGS_IMPLEMENTATION.md`
2. Create `GRANULAR_FLAGS_GUIDE.md`
3. Update `README.md` configuration section
4. Create admin guide for flag management

**Files to Create/Update:**
- `docs/FEATURE_FLAGS_IMPLEMENTATION.md` (update)
- `docs/GRANULAR_FLAGS_GUIDE.md` (NEW)
- `docs/admin/FLAG_MANAGEMENT.md` (NEW)
- `README.md` (update config section)

---

## 5. Configuration Structure

### Complete Configuration Example

```toml
# ═══════════════════════════════════════════════════════════
# GRANULAR FEATURE FLAGS
# ═══════════════════════════════════════════════════════════

# MCP Servers
[mcp]
enabled = true  # Master switch

[mcp.servers]
defillama_enabled = true  # TVL & protocol data
oneinch_enabled = true  # DEX aggregation
thegraph_enabled = true  # Blockchain indexing
coingecko_enabled = true  # Market data
aave_enabled = true  # Lending protocol
portfolio_enabled = true  # Portfolio tracking

# Agno Agents
[agno]
enabled = true  # Master switch
intent_classification_enabled = true  # Auto-routing
fallback_to_general = true  # Fallback behavior

[agno.agents]
trading_enabled = true  # Trade execution
lending_enabled = true  # Lending/borrowing
portfolio_enabled = true  # Portfolio optimization
analytics_enabled = true  # Data analysis

# Project Templates
[projects]
enabled = true  # Master switch
templates_enabled = true  # Template master switch

[projects.templates]
defi_swing_trader_enabled = true  # Intermediate
arbitrage_hunter_enabled = true  # Expert
ai_portfolio_manager_enabled = true  # Long-term
conservative_investor_enabled = true  # Beginner
day_trader_pro_enabled = true  # Expert
```

---

## 6. Error Handling

### MCP Server Disabled

```python
# When MCP server disabled
if not settings.mcp.servers.defillama_enabled:
    raise MCPServerDisabledError(
        "DeFiLlama MCP server is disabled. "
        "Enable with mcp.servers.defillama_enabled=true"
    )
```

### Agent Disabled

```python
# When agent disabled
if not settings.agno.agents.trading_enabled:
    if settings.agno.fallback_to_general:
        # Route to general agent
        logger.info("Trading agent disabled, using general agent")
        return general_agent.process(query)
    else:
        raise AgentDisabledError(
            "Trading agent is disabled. "
            "Enable with agno.agents.trading_enabled=true"
        )
```

### Template Disabled

```python
# When template disabled
if not settings.projects.templates.arbitrage_hunter_enabled:
    raise TemplateDisabledError(
        "Arbitrage Hunter template is disabled. "
        "Enable with projects.templates.arbitrage_hunter_enabled=true"
    )
```

---

## 7. Benefits

### Operational Control

- ✅ Enable/disable individual MCP servers (cost control)
- ✅ Enable/disable individual agents (feature gating)
- ✅ Enable/disable project templates (user segmentation)
- ✅ No code changes required

### Cost Optimization

- ✅ Disable expensive MCP servers in dev/test
- ✅ Reduce API costs by 60-80%
- ✅ Per-environment configuration

### Security

- ✅ Disable risky features (trading agents)
- ✅ Disable complex templates (arbitrage)
- ✅ Gradual feature rollout
- ✅ Quick rollback if issues

### Testing

- ✅ Test individual components
- ✅ Isolate feature testing
- ✅ Mock disabled services

---

## 8. Testing Strategy

### Unit Tests

- Test each flag independently
- Test master switches
- Test fallback behavior
- Test error messages

### Integration Tests

- Test MCP server toggles with real calls
- Test agent routing with disabled agents
- Test project creation with disabled templates
- Test cross-flag interactions

### E2E Tests

- Test full user flows with various flag combinations
- Test admin flag management
- Test environment-specific configs

---

## 9. Migration Strategy

### Backward Compatibility

- All flags default to `true` (enabled)
- Existing deployments work without changes
- Optional flags in constructors

### Rollout Plan

1. **Week 1:** MCP server flags (low risk)
2. **Week 2:** Agent flags (medium risk)
3. **Week 3:** Template flags (low risk)
4. **Week 4:** Full testing & documentation

### Monitoring

- Log when features are disabled
- Track flag usage in analytics
- Alert on unexpected flag combinations

---

## 10. Success Criteria

### Functionality

- ✅ All 15 flags configurable via TOML
- ✅ Master switches work correctly
- ✅ Fallback behavior implemented
- ✅ Clear error messages

### Testing

- ✅ 30+ tests covering all flags
- ✅ 100% pass rate
- ✅ Integration tests for each component

### Documentation

- ✅ Complete flag reference
- ✅ Use case examples
- ✅ Admin management guide
- ✅ Troubleshooting guide

### Performance

- ✅ No performance impact when enabled
- ✅ Fast startup with disabled features
- ✅ Minimal overhead

---

## 11. Future Enhancements

### Dynamic Flags

- Runtime flag toggling (without restart)
- Admin UI for flag management
- Per-user flag overrides

### Advanced Controls

- Rate limiting per MCP server
- Agent priority/weighting
- Template visibility rules

### Analytics

- Flag usage tracking
- Cost analysis per flag
- Performance impact analysis

---

## Appendix A: Flag Reference

| Category | Flag | Default | Description |
|----------|------|---------|-------------|
| **MCP Master** | `mcp.enabled` | `true` | Master switch for all MCP servers |
| **MCP Servers** | `mcp.servers.defillama_enabled` | `true` | DeFiLlama TVL & protocol data |
| | `mcp.servers.oneinch_enabled` | `true` | 1inch DEX aggregation |
| | `mcp.servers.thegraph_enabled` | `true` | The Graph blockchain indexing |
| | `mcp.servers.coingecko_enabled` | `true` | CoinGecko market data |
| | `mcp.servers.aave_enabled` | `true` | Aave lending protocol |
| | `mcp.servers.portfolio_enabled` | `true` | Portfolio tracking |
| **Agno Master** | `agno.enabled` | `true` | Master switch for all agents |
| | `agno.intent_classification_enabled` | `true` | Auto-routing to agents |
| | `agno.fallback_to_general` | `true` | Fallback if agent disabled |
| **Agno Agents** | `agno.agents.trading_enabled` | `true` | Trading agent |
| | `agno.agents.lending_enabled` | `true` | Lending agent |
| | `agno.agents.portfolio_enabled` | `true` | Portfolio agent |
| | `agno.agents.analytics_enabled` | `true` | Analytics agent |
| **Projects Master** | `projects.enabled` | `true` | Master switch for projects |
| | `projects.templates_enabled` | `true` | Master switch for templates |
| **Templates** | `projects.templates.defi_swing_trader_enabled` | `true` | Swing trading template |
| | `projects.templates.arbitrage_hunter_enabled` | `true` | Arbitrage template |
| | `projects.templates.ai_portfolio_manager_enabled` | `true` | Portfolio template |
| | `projects.templates.conservative_investor_enabled` | `true` | Conservative template |
| | `projects.templates.day_trader_pro_enabled` | `true` | Day trading template |

**Total:** 21 flags (6 master + 15 granular)

---

**Document Version:** 1.0  
**Date:** December 1, 2025  
**Status:** Specification Complete ✅  
**Next:** Implementation (Phase 2-5)
