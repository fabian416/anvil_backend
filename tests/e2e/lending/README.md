# Lending System E2E Test Suite

Comprehensive end-to-end testing suite for the complete lending workflow.

## Test Coverage Overview

### Part 1: Supply Workflow (`test_supply_workflow_e2e.py`) ✅ CREATED
- **Complete supply flow validation**
- Balance checks BEFORE execute_data generation
- Aave and Morpho protocol support
- Insufficient balance/gas blocking
- Asset validation
- Execute_data structure validation

**Key Tests:**
- `test_successful_aave_supply_complete_flow` - Full Aave supply workflow
- `test_supply_blocked_insufficient_balance` - Critical balance validation
- `test_supply_blocked_insufficient_gas` - Gas requirement validation
- `test_successful_morpho_supply_complete_flow` - Morpho vault supply
- `test_supply_unsupported_protocol` - Protocol validation
- `test_supply_asset_not_found_in_market` - Market data validation

### Part 2: Borrow Workflow (`test_borrow_workflow_e2e.py`) ✅ CREATED
- **Health factor validation BEFORE approval UI**
- Safe/Caution/Danger/Critical level handling
- Blocking unsafe borrows (HF < min_threshold)
- Collateral sufficiency checks
- Variable vs stable rate modes

**Key Tests:**
- `test_successful_safe_borrow_complete_flow` - Safe borrow (HF > 2.0)
- `test_borrow_BLOCKED_unsafe_health_factor` - CRITICAL: Block HF < 1.5
- `test_borrow_BLOCKED_critical_health_factor` - Block HF < 1.2
- `test_borrow_caution_level_allowed_above_threshold` - Allow with warning
- `test_borrow_blocked_no_collateral` - No collateral scenario
- `test_borrow_with_stable_rate_mode` - Rate mode selection

### Part 3: Leverage Loop (`test_leverage_loop_e2e.py`) ✅ CREATED
- **3x leverage multi-step workflow**
- Loop calculation (supply → borrow → swap iterations)
- Health factor safety validation per step
- Early termination on unsafe conditions
- Balance and asset validation

**Key Tests:**
- `test_successful_3x_leverage_loop_calculation` - Complete 3x loop
- `test_leverage_loop_interrupted_by_hf_drop` - Safety interruption
- `test_leverage_loop_blocked_insufficient_balance` - Balance check
- `test_leverage_loop_blocked_unsupported_asset` - Asset validation
- `test_leverage_loop_invalid_leverage_range` - Range validation (2x-4x)

### Part 4: Health Check (`test_health_check_e2e.py`) - TO CREATE
Tests LENDING_HEALTH_CHECK shortcut and position monitoring.

**Tests to implement:**
```python
test_health_check_safe_position()  # HF > 2.0
test_health_check_caution_position()  # 1.5 < HF < 2.0
test_health_check_danger_position()  # 1.2 < HF < 1.5
test_health_check_critical_with_alert()  # HF < 1.2 + alert creation
test_health_check_no_positions()  # No lending positions
test_health_check_multiple_protocols()  # Aave + Morpho aggregation
test_health_check_saves_to_database()  # Persistence validation
```

### Part 5: Multi-Language (`test_multilanguage_e2e.py`) - TO CREATE
Tests all 4 languages (en, es, pt, zh) for lending messages.

**Tests to implement:**
```python
test_supply_messages_all_languages()  # en, es, pt, zh
test_borrow_messages_all_languages()  # All languages
test_health_check_messages_all_languages()  # All languages
test_leverage_loop_warnings_all_languages()  # All languages
test_error_messages_all_languages()  # Error translation
test_status_labels_translation()  # SAFE, CAUTION, etc.
test_parameter_extraction_multilanguage()  # Parse "10 ETH" vs "10 个ETH"
```

### Part 6: Integration Tests (`test_lending_integration.py`) - TO CREATE
Integration tests with real database and mocked MCPs.

**Tests to implement:**
```python
# Repository Integration
test_save_and_retrieve_supply_position()
test_save_and_retrieve_borrow_position()
test_update_transaction_status()
test_save_loop_execution_state()
test_get_loop_execution_with_steps()

# View Queries
test_user_lending_summary_view()
test_protocol_comparison_view()
test_health_check_time_series()

# Alerts
test_create_critical_alert()
test_get_unread_alerts()
test_mark_alert_as_read()

# User Preferences
test_save_user_preferences()
test_get_user_preferences_with_defaults()
```

### Part 7: Performance Tests (`test_lending_performance.py`) - TO CREATE
Performance benchmarks and load testing.

**Tests to implement:**
```python
# Benchmark Tests
test_supply_command_performance()  # < 200ms
test_borrow_command_performance()  # < 300ms (includes HF validation)
test_health_check_query_performance()  # < 100ms
test_leverage_loop_calculation_performance()  # < 500ms
test_database_query_performance()  # < 50ms per query

# Load Tests
test_concurrent_supply_requests()  # 100 concurrent
test_concurrent_borrow_requests()  # 50 concurrent
test_database_connection_pool_under_load()
test_health_check_batch_query()  # 1000 users
```

## Test Execution

### Run All Lending E2E Tests
```bash
pytest tests/e2e/lending/ -v -m e2e
```

### Run Specific Test File
```bash
pytest tests/e2e/lending/test_supply_workflow_e2e.py -v
pytest tests/e2e/lending/test_borrow_workflow_e2e.py -v
pytest tests/e2e/lending/test_leverage_loop_e2e.py -v
```

### Run with Coverage
```bash
pytest tests/e2e/lending/ --cov=app.application.lending --cov-report=html
```

### Run Performance Tests
```bash
pytest tests/performance/test_lending_performance.py -v -m performance
```

## Mock Strategy

### MCP Servers (Mocked - NO Real API Calls)
- **Portfolio MCP**: Mock balance checks, token prices
- **Aave MCP**: Mock market data, user positions, APYs
- **Morpho MCP**: Mock vault data, APYs, TVL
- **1inch MCP**: Mock swap quotes, gas estimates
- **Privy**: Mock wallet signatures and execute_data

### Real Components (Integration Tests)
- PostgreSQL database (anvil_test)
- SQLAlchemy repositories
- Database views and queries
- DI container with Dishka
- Domain services

## Fixture Organization

### Common Fixtures (`conftest.py`)
```python
@pytest.fixture
def test_user_context():
    """Provides user_id and wallet_address for tests."""

@pytest.fixture
def mock_balance_checker():
    """Mocks IBalanceChecker port."""

@pytest.fixture
def mock_aave_gateway():
    """Mocks AaveGateway port."""

@pytest.fixture
def mock_morpho_gateway():
    """Mocks MorphoGateway port."""

@pytest.fixture
def mock_lending_repository():
    """Mocks ILendingRepository port."""

@pytest.fixture
def mock_swap_executor():
    """Mocks ISwapExecutor port."""

@pytest.fixture
def mock_hf_validator():
    """Mocks HealthFactorValidatorService."""

@pytest.fixture
def mock_privy_wallet():
    """Mocks Privy wallet signatures."""

@pytest.fixture
def clean_test_database():
    """Cleans up test data after each test."""
```

## Coverage Targets

- **Unit Test Coverage**: > 90% (lending application layer)
- **E2E Test Coverage**: > 85% (critical user workflows)
- **Integration Test Coverage**: > 80% (repository + database)
- **Performance Test Coverage**: All critical paths benchmarked

## Critical Safety Validations

### MUST BE TESTED:
1. ✅ Balance checked BEFORE execute_data (supply)
2. ✅ Health factor validated BEFORE execute_data (borrow)
3. ✅ Unsafe borrows BLOCKED (HF < min_threshold)
4. ✅ Leverage loop stops on unsafe conditions
5. ✅ No automatic execution (all steps require approval)
6. ✅ Gas balance validation
7. ✅ Collateral sufficiency checks
8. ✅ Asset validation
9. ✅ Protocol validation
10. ✅ Chain support validation

## Test Data Management

### Test Wallets
- `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb` - Primary test wallet
- `0x1234567890123456789012345678901234567890` - Secondary wallet

### Test Assets
- ETH, WETH, wstETH - Collateral assets
- USDC, USDT, DAI - Borrow/stablecoin assets

### Test Chains
- ethereum (primary)
- base, arbitrum, polygon (multi-chain)

## Continuous Integration

```yaml
# .github/workflows/lending-tests.yml
name: Lending System Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run E2E Tests
        run: pytest tests/e2e/lending/ -v
      - name: Run Integration Tests
        run: pytest tests/integration/lending/ -v
      - name: Run Performance Tests
        run: pytest tests/performance/test_lending_performance.py -v
      - name: Upload Coverage
        uses: codecov/codecov-action@v2
```

## Next Steps

1. **Complete Part 4-7 implementation** (see test templates above)
2. **Add fixture conftest.py** for shared test utilities
3. **Implement performance benchmarks** with pytest-benchmark
4. **Add contract tests** for API responses
5. **Create test data factories** for repeatable test scenarios
6. **Add mutation testing** with mutmut for robustness
7. **Implement visual regression tests** for frontend components
8. **Add chaos engineering tests** for failure scenarios

## Related Documentation

- `/home/ubuntu/anvil_backend/docs/LENDING_SYSTEM.md` - System architecture
- `/home/ubuntu/anvil_backend/docs/HEALTH_FACTOR_SAFETY.md` - Safety design
- `/home/ubuntu/anvil_backend/docs/LEVERAGE_LOOP.md` - Loop mechanics
- `/home/ubuntu/anvil_backend/tests/unit/application/lending/` - Unit tests
