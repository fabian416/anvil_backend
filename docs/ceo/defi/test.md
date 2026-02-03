# DeFi Operations Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Good Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The DeFi Operations module has comprehensive test coverage:
- **Integration Tests**: 2 dedicated files + 10+ related files
- **Unit Tests**: 7 adapter test files
- **Component Tests**: DeFi protocol structure tests

**Total Test Files**: 20+ files covering DeFi functionality

---

## 1. Existing Integration Tests

### 1.1 Aave Integration Tests
**Path**: `tests/integration/defi/test_aave_integration.py`

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestAaveComponentsExist` | 9 | Router, gateway, adapter, entities, VOs, exceptions, schemas, provider |
| `TestAaveExceptionHierarchy` | 2 | Exception inheritance, error codes |
| `TestAaveEntitySerialization` | 3 | Market, position, health factor round-trips |
| `TestAaveRouterRegistration` | 2 | Router export, provider registration |
| `TestHealthFactorCalculations` | 5 | Risk levels (safe, moderate, high, critical, liquidatable) |
| `TestAaveMCPServer` | 2 | MCP server existence, name |
| `TestAaveAdapterIntegration` | 3 | Get markets, user position, calculate HF |

**Key Tests**:
```python
def test_aave_router_exists():
    """Test Aave router can be created."""
    
def test_aave_router_routes():
    """Test Aave router has required routes."""
    # markets, positions, stats, rates, health

def test_risk_level_safe():
    """Test safe risk level classification."""
    
def test_risk_level_liquidatable():
    """Test liquidatable risk level classification."""
```

---

### 1.2 DeFi Protocol Integration Tests
**Path**: `tests/integration/defi/test_defi_integration.py`

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestCurveIntegration` | 6 | Router, gateway, adapter, entities, VOs |
| `TestHyperliquidIntegration` | 5 | Router, gateway, adapter, entities, VOs |
| `TestMorphoIntegration` | 5 | Router, gateway, adapter, entities, VOs |
| `TestLayerZeroIntegration` | 5 | Router, gateway, adapter, entities, VOs |
| `TestAxelarIntegration` | 5 | Router, gateway, adapter, entities, VOs |
| `TestDeFiExceptionsIntegration` | 5 | Exception definitions per protocol |

**Key Tests**:
```python
def test_curve_router_exists():
    """Test Curve router can be created."""
    
def test_hyperliquid_router_exists():
    """Test Hyperliquid router can be created."""
    
def test_morpho_entities_exist():
    """Test Morpho domain entities exist."""
    
def test_layerzero_value_objects_exist():
    """Test LayerZero value objects exist."""
```

---

## 2. Existing Unit Tests

### 2.1 Adapter Unit Tests

| File | Protocol | Tests |
|------|----------|-------|
| `tests/unit/infrastructure/adapters/test_aave_adapter.py` | Aave | Adapter methods |
| `tests/unit/infrastructure/adapters/test_morpho_adapter.py` | Morpho | Adapter methods |
| `tests/unit/infrastructure/adapters/test_hyperliquid_adapter.py` | Hyperliquid | Adapter methods |
| `tests/unit/infrastructure/adapters/test_curve_adapter.py` | Curve | Adapter methods |
| `tests/unit/infrastructure/adapters/test_layerzero_adapter.py` | LayerZero | Adapter methods |
| `tests/unit/infrastructure/adapters/test_axelar_adapter.py` | Axelar | Adapter methods |
| `tests/unit/infrastructure/agents/test_lending_borrowing_agent_aave.py` | Aave Agent | Agent behavior |

---

### 2.2 Gateway Unit Tests
**Path**: `tests/unit/infrastructure/gateways/test_gateway_implementations.py`

Tests for DeFi gateway implementations.

---

## 3. Component Tests

### 3.1 Mock Gateways
**Path**: `tests/component/mocks/gateways.py`

Mock implementations for DeFi gateways used in component tests.

---

### 3.2 Chat DeFi Integration
**Path**: `tests/component/chat/test_graphrag_component.py`

Tests DeFi knowledge graph integration.

---

## 4. Related Test Files

| File | DeFi Relevance |
|------|----------------|
| `tests/integration/projects/test_project_tool_integration.py` | DeFi project tools |
| `tests/integration/ultra/test_flash_loans.py` | Flash loan integration |
| `tests/integration/mcp/test_perplexity_mcp.py` | MCP DeFi research |
| `tests/fixtures/mock_services.py` | DeFi service mocks |

---

## 5. Missing Tests (Gaps Analysis)

### 5.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **E2E** | Full DeFi workflows | HIGH | Complete user journeys |
| **Router** | HTTP endpoint tests | HIGH | Request/response validation |
| **Provider** | CoinGecko tests | MEDIUM | Price data retrieval |
| **Provider** | DeFiLlama tests | MEDIUM | TVL data retrieval |
| **Celery** | Background tasks | MEDIUM | Task execution |

### 5.2 Missing E2E Tests

```python
# tests/e2e/defi/test_defi_workflow.py (MISSING)

class TestAaveWorkflow:
    def test_view_markets_and_check_position():
        """
        Test Aave user workflow:
        1. View available markets
        2. Check user position
        3. Calculate health factor
        """
        
    def test_borrow_capacity_check():
        """
        Test borrow capacity workflow:
        1. Get user position
        2. Check available to borrow
        3. Verify health factor impact
        """

class TestMorphoWorkflow:
    def test_find_best_yield_vault():
        """
        Test yield finding workflow:
        1. List vaults by APY
        2. Get vault details
        3. Compare with other protocols
        """

class TestHyperliquidWorkflow:
    def test_trading_risk_assessment():
        """
        Test trading workflow:
        1. View markets
        2. Check funding rates
        3. Calculate position risk
        """

class TestCrossChainWorkflow:
    def test_bridge_transfer_tracking():
        """
        Test cross-chain workflow:
        1. Estimate transfer costs
        2. Track transfer status
        3. Verify completion
        """
```

### 5.3 Missing HTTP Router Tests

```python
# tests/integration/defi/test_aave_http.py (MISSING)

@pytest.mark.integration
class TestAaveHTTP:
    def test_get_markets_returns_data(self, client):
        """Test GET /aave/markets returns valid data."""
        response = client.get("/api/v1/aave/markets?chain=ethereum")
        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert "count" in data
        
    def test_get_position_invalid_address(self, client):
        """Test GET /aave/positions/{invalid} returns 400."""
        response = client.get("/api/v1/aave/positions/invalid_address")
        assert response.status_code == 400
        
    def test_calculate_health_factor(self, client):
        """Test POST /aave/calculate/health-factor."""
        response = client.post(
            "/api/v1/aave/calculate/health-factor",
            json={
                "collateral_usd": 10000,
                "debt_usd": 5000,
                "liquidation_threshold": 0.825
            }
        )
        assert response.status_code == 200

# tests/integration/defi/test_hyperliquid_http.py (MISSING)

@pytest.mark.integration
class TestHyperliquidHTTP:
    def test_get_markets(self, client):
        """Test GET /hyperliquid/markets."""
        
    def test_get_funding_rates(self, client):
        """Test GET /hyperliquid/funding."""
        
    def test_calculate_risk(self, client):
        """Test POST /hyperliquid/risk/calculate."""
```

### 5.4 Missing Provider Tests

```python
# tests/unit/infrastructure/providers/test_coingecko.py (MISSING)

class TestCoinGeckoClient:
    async def test_get_price_success(self):
        """Test successful price retrieval."""
        
    async def test_get_price_rate_limited(self):
        """Test rate limit handling."""
        
    async def test_get_market_chart(self):
        """Test historical data retrieval."""

# tests/unit/infrastructure/providers/test_defillama.py (MISSING)

class TestDefiLlamaClient:
    async def test_get_protocol_tvl(self):
        """Test TVL retrieval."""
        
    async def test_get_yields(self):
        """Test yield data retrieval."""
```

### 5.5 Missing Celery Task Tests

```python
# tests/integration/celery/test_defi_tasks.py (MISSING)

class TestDeFiCeleryTasks:
    def test_refresh_market_data_task(self):
        """Test market data refresh task."""
        
    def test_monitor_liquidation_risk_task(self):
        """Test liquidation monitoring task."""
        
    def test_track_cross_chain_transfers_task(self):
        """Test transfer tracking task."""
```

---

## 6. Test Commands

### Run All DeFi Tests

```bash
# All DeFi integration tests
pytest tests/integration/defi/ -v

# All DeFi-related tests
pytest -k "defi or aave or morpho or curve or hyperliquid or layerzero or axelar" -v
```

### Run Specific Protocol Tests

```bash
# Aave tests
pytest tests/integration/defi/test_aave_integration.py -v

# Adapter tests
pytest tests/unit/infrastructure/adapters/test_aave_adapter.py -v
pytest tests/unit/infrastructure/adapters/test_morpho_adapter.py -v
pytest tests/unit/infrastructure/adapters/test_hyperliquid_adapter.py -v
```

### Run with Coverage

```bash
pytest tests/integration/defi/ \
  --cov=src/app/presentation/http/controllers/defi \
  --cov=src/app/infrastructure/adapters/external \
  --cov=src/app/infrastructure/defi \
  --cov-report=html
```

---

## 7. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| Routers | ~30% | 80% | 50% |
| Adapters | ~50% | 75% | 25% |
| Domain Entities | ~60% | 80% | 20% |
| Providers | ~10% | 60% | 50% |
| Celery Tasks | ~5% | 60% | 55% |

---

## 8. Test Fixtures

### 8.1 Mock DeFi Gateway
```python
@pytest.fixture
def mock_aave_gateway():
    """Mock AaveGateway for testing."""
    gateway = AsyncMock(spec=AaveGateway)
    gateway.get_markets.return_value = [
        AaveMarket(
            symbol="USDC",
            supply_apy=Decimal("0.05"),
            borrow_apy_variable=Decimal("0.08"),
            ...
        )
    ]
    return gateway
```

### 8.2 Mock Cache
```python
@pytest.fixture
def mock_cache():
    """Mock Redis cache for adapter tests."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache
```

### 8.3 Test Wallets
```python
@pytest.fixture
def test_wallet_address():
    """Test wallet address for position tests."""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21"
```

---

## 9. Test Markers

```python
# pytest.ini or pyproject.toml markers
markers = [
    "defi: DeFi protocol tests",
    "aave: Aave V3 tests",
    "morpho: Morpho Blue tests",
    "hyperliquid: Hyperliquid perpetuals tests",
    "curve: Curve Finance tests",
    "cross_chain: LayerZero/Axelar tests",
    "llm_validation: Tests requiring LLM validation",
]
```

---

## References

- **Integration Tests**: `tests/integration/defi/`
- **Unit Tests**: `tests/unit/infrastructure/adapters/`
- **Component Tests**: `tests/component/`
- **Test Fixtures**: `tests/fixtures/mock_services.py`
