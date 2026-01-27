# Lending Workflow Technical Risk Analysis

## Executive Summary
Comprehensive risk assessment for Aave and Morpho lending integration, covering transaction failures, health factor edge cases, multi-signature workflows, MCP server reliability, and liquidation scenarios.

---

## 1. Transaction Failure Scenarios

### 1.1 Insufficient Balance
**Risk Level**: HIGH
**Probability**: Medium (10-15% of user attempts)

**Scenario**:
```
User initiates supply of 1000 USDC
Actual balance: 800 USDC
```

**Failure Points**:
1. **Pre-Check Missing**: No balance validation before MCP call
2. **MCP Tool Execution**: Transaction reverts on-chain
3. **Gas Wasted**: User pays gas for failed transaction

**Mitigation**:
```python
class SupplyAssetInteractor:
    async def execute(self, command: SupplyAssetCommand):
        # CRITICAL: Check balance BEFORE MCP call
        balance = await self._balance_validator.get_balance(
            command.wallet_address, command.asset_address
        )

        if balance < command.amount:
            raise InsufficientBalanceError(
                available=balance,
                required=command.amount,
                shortfall=command.amount - balance,
            )

        # Proceed with transaction
        tx_hash = await self._lending_gateway.supply_asset(...)
```

**Testing**:
- [ ] Unit test: `test_supply_fails_insufficient_balance`
- [ ] Integration test: Mock web3 balance check
- [ ] E2E test: Actual wallet with low balance

**Monitoring**:
- Alert: Balance check failures > 5% of attempts
- Metric: `lending.balance_check.failures` (Counter)

---

### 1.2 Network Errors (RPC Node Failures)
**Risk Level**: MEDIUM
**Probability**: Low (1-3% of transactions)

**Scenario**:
```
MCP server calls Ethereum RPC node
RPC node returns: 502 Bad Gateway
```

**Failure Points**:
1. **Timeout**: RPC request takes > 30 seconds
2. **Connection Reset**: Network interruption mid-request
3. **Invalid Response**: Malformed JSON from RPC

**Mitigation**:
```python
class AaveMcpAdapter:
    async def supply_asset(
        self, wallet: str, asset: str, amount: Decimal
    ) -> TxHash:
        try:
            result = await self._client.call_tool(
                "mcp__aave__supply_asset",
                {
                    "wallet_address": wallet,
                    "asset": asset,
                    "amount": str(amount),
                },
                timeout=60,  # 60 second timeout
            )
            return result["tx_hash"]

        except TimeoutError as e:
            # Retry with exponential backoff
            raise NetworkTimeoutError(protocol="aave", original_error=e)

        except McpServerError as e:
            if e.status_code in (502, 503, 504):
                # RPC node unavailable, try fallback
                raise RpcNodeUnavailableError(node=e.node_url)
            raise
```

**Retry Strategy**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(NetworkTimeoutError),
)
async def supply_asset_with_retry(self, ...):
    return await self._adapter.supply_asset(...)
```

**Testing**:
- [ ] Integration test: Mock MCP server timeout
- [ ] Integration test: Simulate 502/503 responses
- [ ] Load test: 100 concurrent requests to test retry logic

**Monitoring**:
- Alert: RPC error rate > 5%
- Metric: `lending.rpc.errors` (Counter, labeled by error type)
- Dashboard: RPC latency p50, p95, p99

---

### 1.3 Gas Estimation Errors
**Risk Level**: MEDIUM
**Probability**: Medium (5-10% during network congestion)

**Scenario**:
```
Gas estimation: 150,000 gas
Actual usage: 180,000 gas (due to state changes)
Transaction fails: Out of gas
```

**Failure Points**:
1. **Underestimation**: Volatile market conditions change gas requirements
2. **State Changes**: Another transaction modifies contract state
3. **Complex Interactions**: Multi-hop operations (e.g., Morpho vault)

**Mitigation**:
```python
class GasEstimator:
    async def estimate_with_buffer(
        self, tx_params: Dict[str, Any], buffer_pct: float = 20.0
    ) -> int:
        # Get base estimate from RPC
        base_estimate = await self._web3.eth.estimate_gas(tx_params)

        # Add safety buffer
        buffered_estimate = int(base_estimate * (1 + buffer_pct / 100))

        # Cap at reasonable maximum
        max_gas = 1_000_000
        return min(buffered_estimate, max_gas)
```

**Fallback Strategy**:
```python
# If estimation fails, use protocol-specific defaults
DEFAULT_GAS_LIMITS = {
    "aave_supply": 250_000,
    "aave_borrow": 300_000,
    "morpho_deposit": 350_000,
    "morpho_withdraw": 400_000,
}
```

**Testing**:
- [ ] Integration test: Mock gas estimation failure
- [ ] E2E test: Test during simulated network congestion
- [ ] Chaos test: Random gas limit reductions

**Monitoring**:
- Alert: Gas estimation failures > 5%
- Metric: `lending.gas.estimation_failures` (Counter)
- Metric: `lending.gas.actual_vs_estimated` (Histogram)

---

## 2. Health Factor Calculation Errors

### 2.1 Stale Price Data
**Risk Level**: CRITICAL
**Probability**: Low (1-2% during flash crashes)

**Scenario**:
```
User borrows $500 against $1000 ETH collateral
Health Factor calculated: 1.6 (safe)
Actual ETH price drops 20% in 5 minutes
Real Health Factor: 1.28 (risky)
System shows: 1.6 (cached value)
```

**Failure Points**:
1. **Cache TTL Too Long**: 60 second cache during volatile market
2. **Oracle Delay**: Chainlink oracle updates lag by 1-2 blocks
3. **Price Manipulation**: Flash loan attack skews oracle

**Mitigation**:
```python
class HealthFactorCalculator:
    def __init__(
        self,
        price_oracle: IPriceOracle,
        cache_ttl: int = 10,  # 10 seconds max
    ):
        self._oracle = price_oracle
        self._cache_ttl = cache_ttl

    async def calculate(
        self, wallet: str, force_refresh: bool = False
    ) -> HealthFactor:
        # Always fetch fresh prices for critical checks
        if force_refresh:
            prices = await self._oracle.get_prices(use_cache=False)
        else:
            prices = await self._oracle.get_prices(use_cache=True)

        # Get user positions
        positions = await self._get_user_positions(wallet)

        # Calculate weighted collateral value
        collateral_value = sum(
            p.supplied_amount * prices[p.asset] * p.liquidation_threshold
            for p in positions
        )

        # Calculate total debt value
        debt_value = sum(
            p.borrowed_amount * prices[p.asset]
            for p in positions
        )

        if debt_value == 0:
            return HealthFactor(float('inf'))

        return HealthFactor(collateral_value / debt_value)
```

**Critical Check Enforcement**:
```python
# ALWAYS force refresh before allowing borrows
async def borrow_asset(self, command: BorrowAssetCommand):
    health_factor = await self._calculator.calculate(
        command.wallet_address, force_refresh=True  # Fresh prices
    )

    # Simulate health factor after borrow
    simulated_hf = await self._calculator.calculate_after_borrow(
        command.wallet_address,
        command.asset_address,
        command.amount,
        force_refresh=True,
    )

    if simulated_hf.value < 1.2:
        raise HealthFactorTooLowError(
            current=health_factor.value,
            after_borrow=simulated_hf.value,
            minimum=1.2,
        )
```

**Testing**:
- [ ] Unit test: Simulate price drop during calculation
- [ ] Integration test: Mock oracle with delayed prices
- [ ] Stress test: 50% price swing in 1 minute

**Monitoring**:
- Alert: Health factor < 1.3 (warning), < 1.2 (critical)
- Alert: Price deviation > 5% from multiple oracles
- Metric: `lending.health_factor.distribution` (Histogram)

---

### 2.2 Precision Loss in Calculations
**Risk Level**: LOW
**Probability**: Very Low (<0.1%)

**Scenario**:
```python
collateral_value = Decimal("1000.123456789012345678")  # Wei precision
debt_value = Decimal("999.987654321098765432")
health_factor = collateral_value / debt_value
# Result: 1.000135802469135802468  (many decimal places)
# Stored in DB: 1.0001  (4 decimal places)
# Precision lost!
```

**Mitigation**:
```python
class HealthFactor:
    def __init__(self, value: Decimal):
        # Use Decimal for precision, not float
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        # Validate range
        if value < 0:
            raise ValueError("Health factor cannot be negative")

        # Round to 4 decimal places for storage
        self._value = value.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

    @property
    def value(self) -> Decimal:
        return self._value

    def __repr__(self) -> str:
        return f"HealthFactor({self._value})"
```

**Database Schema**:
```sql
CREATE TABLE lending_positions (
    -- Use NUMERIC for precision (not FLOAT)
    health_factor NUMERIC(10, 4) NOT NULL,  -- 10 digits, 4 decimal places
    supplied_amount NUMERIC(78, 0) NOT NULL,  -- Wei precision (78 digits)
    borrowed_amount NUMERIC(78, 0) NOT NULL,
);
```

**Testing**:
- [ ] Unit test: Verify precision with large numbers
- [ ] Unit test: Test edge cases (0, infinity, 1.0000)
- [ ] Integration test: Round-trip DB storage

---

## 3. Multi-Signature Workflow Interruptions

### 3.1 Partial Signature Collection
**Risk Level**: MEDIUM
**Probability**: Medium (10% of multi-sig txs)

**Scenario**:
```
Multi-sig: 2 of 3 required
Signatures collected: 1 of 3
Timeout: 5 minutes
Status: Incomplete
```

**Failure Points**:
1. **Signer Unavailable**: Mobile device offline
2. **Signature Expiration**: Nonce changes before collection complete
3. **Conflicting Signatures**: Different transaction data signed

**Mitigation**:
```python
class MultiSigCoordinator:
    def __init__(
        self,
        signature_timeout: int = 300,  # 5 minutes
        max_retries: int = 3,
    ):
        self._timeout = signature_timeout
        self._max_retries = max_retries

    async def collect_signatures(
        self, tx_data: Dict[str, Any], required_signers: List[str]
    ) -> List[str]:
        signatures = []
        start_time = datetime.utcnow()

        for signer in required_signers:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > self._timeout:
                raise SignatureCollectionTimeoutError(
                    collected=len(signatures),
                    required=len(required_signers),
                )

            # Request signature with retry
            for attempt in range(self._max_retries):
                try:
                    signature = await self._request_signature(signer, tx_data)
                    signatures.append(signature)
                    break
                except SignerUnavailableError:
                    if attempt == self._max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return signatures
```

**Persistence Strategy**:
```python
# Store partial signatures in DB for recovery
class MultiSigTransaction:
    id: UUID
    tx_data: Dict[str, Any]
    required_signatures: int
    collected_signatures: List[str]
    status: str  # 'pending', 'complete', 'expired'
    expires_at: datetime
    created_at: datetime
```

**Recovery Flow**:
```python
# Background task to clean up expired multi-sig requests
@celery.task
async def cleanup_expired_multisig():
    expired_txs = await db.query(
        MultiSigTransaction
    ).filter(
        MultiSigTransaction.status == 'pending',
        MultiSigTransaction.expires_at < datetime.utcnow(),
    ).all()

    for tx in expired_txs:
        tx.status = 'expired'
        await db.commit()

        # Notify users
        await notification_service.send_multisig_expired(tx)
```

**Testing**:
- [ ] Unit test: Simulate signer timeout
- [ ] Integration test: Partial signature collection
- [ ] E2E test: Full multi-sig flow with delays

**Monitoring**:
- Alert: Multi-sig timeout rate > 10%
- Metric: `lending.multisig.completion_time` (Histogram)
- Metric: `lending.multisig.failures` (Counter, labeled by reason)

---

### 3.2 Nonce Mismatch (Race Conditions)
**Risk Level**: HIGH
**Probability**: Low (2-3% during high activity)

**Scenario**:
```
User submits 2 transactions simultaneously:
TX1: Supply 1000 USDC (nonce: 5)
TX2: Borrow 500 USDC (nonce: 5)  # Same nonce!
Result: One transaction fails
```

**Mitigation**:
```python
class NonceManager:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def get_next_nonce(self, wallet: str) -> int:
        # Atomic increment in Redis
        key = f"nonce:{wallet}"

        # Use Redis transaction for atomicity
        async with self._redis.pipeline() as pipe:
            while True:
                try:
                    # Watch key for changes
                    await pipe.watch(key)

                    # Get current nonce from blockchain
                    on_chain_nonce = await self._web3.eth.get_transaction_count(
                        wallet, "pending"
                    )

                    # Get highest used nonce from Redis
                    cached_nonce = await pipe.get(key)
                    if cached_nonce is None:
                        next_nonce = on_chain_nonce
                    else:
                        next_nonce = max(int(cached_nonce) + 1, on_chain_nonce)

                    # Atomically set next nonce
                    pipe.multi()
                    pipe.set(key, next_nonce, ex=300)  # 5 min expiry
                    await pipe.execute()

                    return next_nonce

                except WatchError:
                    # Another transaction modified the key, retry
                    continue
```

**Testing**:
- [ ] Concurrency test: 100 parallel nonce requests
- [ ] Integration test: Simulate blockchain nonce changes
- [ ] Stress test: Rapid sequential transactions

**Monitoring**:
- Alert: Nonce mismatch rate > 1%
- Metric: `lending.nonce.conflicts` (Counter)

---

## 4. MCP Server Failures and Fallback Strategies

### 4.1 Aave MCP Server Downtime
**Risk Level**: HIGH
**Probability**: Low (1-2% uptime issues)

**Scenario**:
```
Request: GET http://localhost:8085/mcp__aave__get_market_data
Response: Connection refused (server crashed)
```

**Mitigation - Fallback Chain**:
```python
class ResilientLendingGateway(ILendingProtocolGateway):
    def __init__(
        self,
        primary_adapter: AaveMcpAdapter,
        fallback_adapter: Optional[DirectAaveAdapter] = None,
    ):
        self._primary = primary_adapter
        self._fallback = fallback_adapter

    async def get_market_data(self, asset: str) -> MarketData:
        try:
            # Try MCP server first
            return await self._primary.get_market_data(asset)

        except McpServerUnreachableError as e:
            logger.warning(f"Aave MCP server down, using fallback: {e}")

            if self._fallback is None:
                raise NoFallbackAvailableError(protocol="aave")

            # Fall back to direct web3 calls
            return await self._fallback.get_market_data(asset)
```

**Direct Adapter (Fallback)**:
```python
class DirectAaveAdapter(ILendingProtocolGateway):
    """Direct web3 calls to Aave contracts (no MCP)"""

    def __init__(self, web3: Web3, aave_pool_address: str):
        self._web3 = web3
        self._pool = web3.eth.contract(
            address=aave_pool_address, abi=AAVE_POOL_ABI
        )

    async def get_market_data(self, asset: str) -> MarketData:
        # Direct contract call
        reserve_data = await self._pool.functions.getReserveData(asset).call()

        return MarketData(
            supply_apy=self._calculate_apy(reserve_data.liquidityRate),
            borrow_apy=self._calculate_apy(reserve_data.variableBorrowRate),
            total_supply=reserve_data.totalATokenSupply,
            # ...
        )
```

**Health Checks**:
```python
@celery.task(schedule=crontab(minute="*/1"))  # Every minute
async def check_mcp_server_health():
    servers = [
        ("aave", "http://localhost:8085"),
        ("morpho", "http://localhost:8088"),
    ]

    for name, url in servers:
        try:
            response = await httpx.get(f"{url}/health", timeout=5)
            if response.status_code != 200:
                await alert_service.send_alert(
                    f"MCP server {name} unhealthy: {response.status_code}"
                )
        except httpx.ConnectError:
            await alert_service.send_alert(f"MCP server {name} unreachable")
```

**Testing**:
- [ ] Integration test: Kill MCP server mid-request
- [ ] E2E test: Test fallback to direct adapter
- [ ] Chaos test: Random MCP server restarts

**Monitoring**:
- Alert: MCP server downtime > 1 minute
- Metric: `lending.mcp.uptime` (Gauge, per protocol)
- Metric: `lending.mcp.fallback_usage` (Counter)

---

### 4.2 Rate Limiting from MCP Servers
**Risk Level**: MEDIUM
**Probability**: Medium (5-10% during peak usage)

**Scenario**:
```
100 users query Aave rates simultaneously
MCP server: 429 Too Many Requests
```

**Mitigation - Request Coalescing**:
```python
class CoalescedMcpAdapter:
    def __init__(self, adapter: AaveMcpAdapter):
        self._adapter = adapter
        self._in_flight_requests: Dict[str, asyncio.Future] = {}

    async def get_market_data(self, asset: str) -> MarketData:
        # Check if request already in-flight
        if asset in self._in_flight_requests:
            # Wait for existing request to complete
            return await self._in_flight_requests[asset]

        # Create new request
        future = asyncio.ensure_future(self._adapter.get_market_data(asset))
        self._in_flight_requests[asset] = future

        try:
            result = await future
            return result
        finally:
            # Clean up
            del self._in_flight_requests[asset]
```

**Client-Side Rate Limiting**:
```python
from aiolimiter import AsyncLimiter

class RateLimitedMcpAdapter:
    def __init__(self, adapter: AaveMcpAdapter):
        self._adapter = adapter
        # 100 requests per minute
        self._limiter = AsyncLimiter(max_rate=100, time_period=60)

    async def get_market_data(self, asset: str) -> MarketData:
        async with self._limiter:
            return await self._adapter.get_market_data(asset)
```

**Testing**:
- [ ] Load test: 1000 concurrent requests
- [ ] Integration test: Mock 429 responses
- [ ] Performance test: Measure request coalescing savings

**Monitoring**:
- Alert: 429 responses > 5% of requests
- Metric: `lending.mcp.rate_limit_hits` (Counter)
- Metric: `lending.mcp.request_coalesce_savings` (Counter)

---

## 5. Liquidation Risk Edge Cases

### 5.1 Flash Crashes (Rapid Price Movements)
**Risk Level**: CRITICAL
**Probability**: Very Low (0.1-0.5% annually)

**Scenario**:
```
User health factor: 1.5 (safe)
ETH price drops 30% in 2 minutes (flash crash)
New health factor: 1.05 (critical)
Liquidation threshold: 1.0
User is liquidated before they can react
```

**Mitigation - Proactive Monitoring**:
```python
@celery.task(schedule=crontab(minute="*/5"))  # Every 5 minutes
async def monitor_health_factors():
    # Find all positions with health factor < 1.5
    risky_positions = await db.query(LendingPosition).filter(
        LendingPosition.health_factor < 1.5
    ).all()

    for position in risky_positions:
        # Recalculate with fresh prices
        current_hf = await health_factor_calculator.calculate(
            position.wallet_address, force_refresh=True
        )

        if current_hf.value < 1.2:
            # CRITICAL: Send urgent notification
            await notification_service.send_liquidation_warning(
                user_id=position.user_id,
                current_hf=current_hf.value,
                collateral_needed=calculate_collateral_needed(position, 1.5),
            )

        elif current_hf.value < 1.5:
            # WARNING: Send advisory notification
            await notification_service.send_health_factor_warning(
                user_id=position.user_id,
                current_hf=current_hf.value,
            )
```

**Auto-Repay Feature** (Optional):
```python
class AutoRepayService:
    async def execute_auto_repay(self, position: LendingPosition):
        """Automatically repay debt to improve health factor"""

        # Calculate minimum repayment needed to reach HF = 2.0
        target_hf = 2.0
        repay_amount = self._calculate_repay_amount(position, target_hf)

        # Check if user has funds
        balance = await self._balance_validator.get_balance(
            position.wallet_address, position.borrow_asset
        )

        if balance < repay_amount:
            # Partial repay with available balance
            repay_amount = balance

        # Execute repayment
        tx_hash = await self._lending_gateway.repay_asset(
            wallet=position.wallet_address,
            asset=position.borrow_asset,
            amount=repay_amount,
        )

        return tx_hash
```

**Testing**:
- [ ] Simulation test: 50% price drop scenario
- [ ] Integration test: Mock rapid price feed updates
- [ ] E2E test: Auto-repay trigger flow

**Monitoring**:
- Alert: Any position HF < 1.1 (immediate)
- Alert: Number of positions HF < 1.5 increases > 20% in 5 min
- Dashboard: Health factor distribution histogram

---

### 5.2 Oracle Failure (Stale or Manipulated Prices)
**Risk Level**: CRITICAL
**Probability**: Very Low (<0.1%)

**Scenario**:
```
Chainlink oracle stops updating (rare bug)
Last price: $2000 ETH (30 minutes ago)
Actual price: $1800 ETH
System calculates HF based on stale $2000 price
User appears safe but is actually at liquidation risk
```

**Mitigation - Multi-Oracle Validation**:
```python
class MultiOraclePriceValidator:
    def __init__(
        self,
        primary_oracle: IPriceOracle,  # Chainlink
        secondary_oracle: IPriceOracle,  # Uniswap TWAP
        max_deviation: float = 5.0,  # 5% max difference
    ):
        self._primary = primary_oracle
        self._secondary = secondary_oracle
        self._max_deviation = max_deviation

    async def get_validated_price(self, asset: str) -> Decimal:
        # Get prices from both oracles
        primary_price, secondary_price = await asyncio.gather(
            self._primary.get_price(asset),
            self._secondary.get_price(asset),
            return_exceptions=True,
        )

        # Handle oracle failures
        if isinstance(primary_price, Exception):
            logger.error(f"Primary oracle failed: {primary_price}")
            if isinstance(secondary_price, Exception):
                raise AllOraclesFailedError()
            return secondary_price

        if isinstance(secondary_price, Exception):
            logger.warning(f"Secondary oracle failed: {secondary_price}")
            return primary_price

        # Check for manipulation/staleness
        deviation_pct = abs(
            (primary_price - secondary_price) / primary_price * 100
        )

        if deviation_pct > self._max_deviation:
            logger.critical(
                f"Oracle price deviation {deviation_pct}% exceeds {self._max_deviation}%"
            )
            raise OraclePriceDeviationError(
                primary=primary_price,
                secondary=secondary_price,
                deviation=deviation_pct,
            )

        # Return average of both oracles
        return (primary_price + secondary_price) / 2
```

**Staleness Check**:
```python
async def _check_price_staleness(self, price_data: Dict[str, Any]) -> bool:
    """Check if price is too old"""
    last_update = datetime.fromtimestamp(price_data["updated_at"])
    age_seconds = (datetime.utcnow() - last_update).total_seconds()

    MAX_AGE_SECONDS = 300  # 5 minutes

    if age_seconds > MAX_AGE_SECONDS:
        logger.error(f"Price is stale: {age_seconds}s old")
        return False

    return True
```

**Testing**:
- [ ] Unit test: Simulate oracle deviation > 5%
- [ ] Integration test: Mock stale oracle data
- [ ] Chaos test: Kill primary oracle mid-calculation

**Monitoring**:
- Alert: Oracle deviation > 3%
- Alert: Oracle age > 3 minutes
- Metric: `lending.oracle.deviation` (Gauge, per asset)
- Metric: `lending.oracle.staleness` (Gauge, seconds)

---

## 6. Risk Mitigation Summary

### Critical Safeguards
1. **Pre-Transaction Balance Validation** (ALWAYS)
2. **Force Price Refresh for Borrows** (ALWAYS)
3. **Multi-Oracle Price Validation** (CRITICAL operations)
4. **Health Factor Monitoring** (Every 5 minutes)
5. **MCP Server Health Checks** (Every 1 minute)

### Fallback Strategies
1. **Network Errors**: Retry with exponential backoff (3 attempts)
2. **MCP Server Down**: Fall back to direct web3 calls
3. **Oracle Failure**: Use secondary oracle or reject operation
4. **Gas Estimation Failure**: Use protocol-specific defaults

### Monitoring Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Health Factor | < 1.5 | < 1.2 |
| Balance Check Failures | > 5% | > 10% |
| RPC Errors | > 3% | > 5% |
| MCP Downtime | > 30s | > 1 min |
| Oracle Deviation | > 3% | > 5% |
| Transaction Failures | > 5% | > 10% |

---

## 7. Testing Requirements

### Critical Path Tests (100% Coverage Required)
- [ ] Balance validation before all transactions
- [ ] Health factor calculation with edge cases
- [ ] Multi-oracle price validation
- [ ] Gas estimation with fallbacks
- [ ] MCP server failover logic

### Chaos Engineering Tests
- [ ] Random MCP server kills
- [ ] Network latency injection (500ms-5s)
- [ ] Simulated flash crashes (50% price drop)
- [ ] Oracle manipulation attempts
- [ ] Concurrent transaction storms (1000+ TPS)

### Load Tests
- [ ] 10,000 users checking health factors simultaneously
- [ ] 1,000 concurrent supply transactions
- [ ] MCP server request coalescing under load

---

## Sign-Off

- [ ] **Risk Assessment**: @security-specialist
- [ ] **Failure Scenarios**: @reliability-engineer
- [ ] **Testing Strategy**: @test-automation-expert
- [ ] **Monitoring Plan**: @observability-specialist

**Final Approval**: @code-reviewer
