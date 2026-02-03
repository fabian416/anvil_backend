# Lending Workflow Code Review Checklist

## Overview
Comprehensive review checklist for Aave and Morpho lending integration following Hexagonal Architecture, CQRS, and DeFi safety best practices.

---

## 1. Hexagonal Architecture Compliance

### Domain Layer (`src/app/domain/`)
- [ ] **Lending Domain Entities**
  - [ ] `LendingPosition` entity with identity (user_id, protocol, asset)
  - [ ] `HealthFactor` value object (immutable, validated range 0.0-∞)
  - [ ] `LendingAsset` value object (asset_address, amount, apy, protocol)
  - [ ] `CollateralRatio` value object with validation rules
  - [ ] `LiquidationThreshold` value object per protocol

- [ ] **Domain Services**
  - [ ] `LendingRiskCalculator` - health factor, liquidation risk
  - [ ] `ProtocolComparator` - APY comparison across Aave/Morpho
  - [ ] `CollateralValidator` - validate collateral sufficiency
  - [ ] No infrastructure dependencies (pure business logic)

- [ ] **Domain Ports (Interfaces)**
  ```python
  # src/app/domain/ports/lending_gateway.py
  class ILendingProtocolGateway(Protocol):
      async def get_market_data(self, asset: str) -> MarketData: ...
      async def supply_asset(self, wallet: str, asset: str, amount: Decimal) -> TxHash: ...
      async def borrow_asset(self, wallet: str, asset: str, amount: Decimal) -> TxHash: ...
      async def get_health_factor(self, wallet: str) -> HealthFactor: ...
      async def get_user_positions(self, wallet: str) -> List[LendingPosition]: ...

  class IBalanceValidator(Protocol):
      async def has_sufficient_balance(self, wallet: str, asset: str, amount: Decimal) -> bool: ...
  ```

- [ ] **Domain Events**
  - [ ] `LendingPositionCreated` event
  - [ ] `BorrowExecuted` event
  - [ ] `HealthFactorCritical` event (< 1.2)
  - [ ] `CollateralDeposited` event
  - [ ] Events contain only domain data (no HTTP/MCP references)

### Application Layer (`src/app/application/`)

#### Commands (Write Operations)
- [ ] **Command Models**
  ```python
  # src/app/application/lending/commands/supply_asset.py
  @dataclass(frozen=True)
  class SupplyAssetCommand:
      user_id: UUID
      protocol: str  # 'aave' | 'morpho'
      asset_address: str
      amount: Decimal
      wallet_address: str
  ```

- [ ] **Command Interactors**
  - [ ] `SupplyAssetInteractor` - deposit collateral
  - [ ] `BorrowAssetInteractor` - borrow against collateral
  - [ ] `RepayDebtInteractor` - repay borrowed amount
  - [ ] `WithdrawCollateralInteractor` - withdraw supplied assets
  - [ ] Each interactor has single responsibility
  - [ ] All use dependency injection (Dishka, not FastAPI DI)
  - [ ] Transaction boundaries clearly defined

- [ ] **Command Gateway Usage**
  ```python
  class SupplyAssetInteractor:
      def __init__(
          self,
          lending_gateway: ILendingProtocolGateway,
          balance_validator: IBalanceValidator,
          risk_calculator: LendingRiskCalculator,
          command_gateway: UserCommandGateway,
      ):
          # Injected dependencies via Dishka
  ```

#### Queries (Read Operations)
- [ ] **Query Models**
  ```python
  # src/app/application/lending/queries/lending_position_query_model.py
  @dataclass(frozen=True)
  class LendingPositionQueryModel:
      position_id: str
      user_id: UUID
      protocol: str
      supplied_amount: Decimal
      borrowed_amount: Decimal
      health_factor: float
      apy_supply: float
      apy_borrow: float
      updated_at: datetime
  ```

- [ ] **Query Interactors**
  - [ ] `GetUserLendingPositionsQuery` - all positions for user
  - [ ] `GetBestLendingRatesQuery` - compare APYs across protocols
  - [ ] `GetHealthFactorQuery` - current health factor
  - [ ] `GetLiquidationRiskQuery` - risk assessment
  - [ ] Use `UserQueryGateway` for optimized reads
  - [ ] No business logic in queries (just data retrieval)

#### Authorization
- [ ] **Application Services**
  ```python
  # src/app/application/lending/authorization/lending_authorization_service.py
  class LendingAuthorizationService:
      async def can_execute_lending_action(
          self, user_id: UUID, action: str
      ) -> bool:
          # Guest users: read-only
          # Authenticated: full access
  ```

### Infrastructure Layer (`src/app/infrastructure/`)

#### Adapters
- [ ] **Aave MCP Adapter**
  ```python
  # src/app/infrastructure/adapters/lending/aave_mcp_adapter.py
  class AaveMcpAdapter(ILendingProtocolGateway):
      def __init__(self, mcp_client: McpClient):
          self._client = mcp_client
          self._base_url = "http://localhost:8085"

      async def get_market_data(self, asset: str) -> MarketData:
          # Call mcp__aave__get_market_data tool

      async def supply_asset(
          self, wallet: str, asset: str, amount: Decimal
      ) -> TxHash:
          # Call mcp__aave__supply_asset tool
          # Returns tx hash, NOT success/failure
  ```

- [ ] **Morpho MCP Adapter**
  ```python
  # src/app/infrastructure/adapters/lending/morpho_mcp_adapter.py
  class MorphoMcpAdapter(ILendingProtocolGateway):
      def __init__(self, mcp_client: McpClient):
          self._client = mcp_client
          self._base_url = "http://localhost:8088"

      async def get_vault_data(self, vault_id: str) -> VaultData:
          # Call mcp__morpho__morpho_get_vaults tool
  ```

- [ ] **Balance Validator Adapter**
  ```python
  # src/app/infrastructure/adapters/balance/web3_balance_adapter.py
  class Web3BalanceValidator(IBalanceValidator):
      async def has_sufficient_balance(
          self, wallet: str, asset: str, amount: Decimal
      ) -> bool:
          # Check ERC20 balance via web3 or TheGraph MCP
  ```

#### Persistence
- [ ] **SQLAlchemy Mappings**
  ```python
  # src/app/infrastructure/persistence_sqla/mappings/lending_position_mapping.py
  from sqlalchemy.orm import registry

  mapper_registry = registry()
  lending_positions_table = Table(
      "lending_positions",
      mapper_registry.metadata,
      Column("id", UUID, primary_key=True),
      Column("user_id", UUID, ForeignKey("chat_users.id")),
      Column("protocol", String(20)),  # 'aave' | 'morpho'
      Column("asset_address", String(42)),
      Column("supplied_amount", Numeric(78, 0)),  # Wei precision
      Column("borrowed_amount", Numeric(78, 0)),
      Column("health_factor", Numeric(10, 4)),
      Column("last_updated", DateTime(timezone=True)),
  )
  ```

### Presentation Layer (`src/app/presentation/http/`)

- [ ] **HTTP Controllers**
  ```python
  # src/app/presentation/http/controllers/lending/lending_router.py
  router = APIRouter(prefix="/api/v1/lending", tags=["lending"])

  @router.post("/supply")
  async def supply_asset(
      request: SupplyAssetRequest,
      interactor: FromDishka[SupplyAssetInteractor],
      user_id: UUID = Depends(get_current_user_id),
  ) -> SupplyAssetResponse:
      # Convert HTTP request to command
      # Execute interactor
      # Return HTTP response
  ```

- [ ] **Request/Response Models**
  ```python
  # src/app/presentation/http/schemas/lending/supply_request.py
  class SupplyAssetRequest(BaseModel):
      protocol: Literal["aave", "morpho"]
      asset_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
      amount: Decimal = Field(gt=0)
      wallet_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
  ```

---

## 2. CQRS Pattern Implementation

### Command-Query Separation
- [ ] **Clear Boundaries**
  - [ ] Commands modify state (supply, borrow, repay, withdraw)
  - [ ] Queries only read data (positions, rates, health factor)
  - [ ] No command returns domain data (only success/tx_hash)
  - [ ] No query modifies state

- [ ] **Gateway Usage**
  ```python
  # Commands use UserCommandGateway
  async def supply_asset(self, command: SupplyAssetCommand):
      # Validate balance BEFORE submission
      has_balance = await self._balance_validator.has_sufficient_balance(
          command.wallet_address, command.asset_address, command.amount
      )
      if not has_balance:
          raise InsufficientBalanceError()

      # Execute transaction
      tx_hash = await self._lending_gateway.supply_asset(...)

      # Save via command gateway
      await self._command_gateway.save(lending_position)

  # Queries use UserQueryGateway
  async def get_positions(self, user_id: UUID):
      return await self._query_gateway.find_lending_positions(user_id)
  ```

### Eventual Consistency
- [ ] **Transaction Status Tracking**
  - [ ] Store pending tx with hash immediately
  - [ ] Background task polls tx status
  - [ ] Update position when confirmed
  - [ ] Emit `LendingPositionConfirmed` event

---

## 3. Error Handling and Edge Cases

### Input Validation
- [ ] **Domain-Level Validation**
  ```python
  class LendingAsset:
      def __init__(self, asset_address: str, amount: Decimal):
          if not re.match(r"^0x[a-fA-F0-9]{40}$", asset_address):
              raise InvalidAssetAddressError()
          if amount <= 0:
              raise InvalidAmountError("Amount must be positive")
          self.asset_address = asset_address
          self.amount = amount
  ```

- [ ] **Health Factor Validation**
  ```python
  class HealthFactor:
      def __init__(self, value: float):
          if value < 0:
              raise ValueError("Health factor cannot be negative")
          self._value = value

      @property
      def is_critical(self) -> bool:
          return self._value < 1.2  # Liquidation risk

      @property
      def is_safe(self) -> bool:
          return self._value > 2.0
  ```

### Transaction Failures
- [ ] **Pre-Transaction Checks**
  ```python
  async def _validate_supply_prerequisites(self, command: SupplyAssetCommand):
      # 1. Check wallet balance
      has_balance = await self._balance_validator.has_sufficient_balance(...)
      if not has_balance:
          raise InsufficientBalanceError()

      # 2. Check asset is supported
      market_data = await self._lending_gateway.get_market_data(command.asset_address)
      if not market_data.is_active:
          raise AssetNotSupportedError()

      # 3. Check protocol availability
      health_check = await self._lending_gateway.health_check()
      if not health_check.is_healthy:
          raise ProtocolUnavailableError()
  ```

- [ ] **Post-Transaction Handling**
  ```python
  try:
      tx_hash = await self._lending_gateway.supply_asset(...)
      # Store pending transaction
      await self._save_pending_tx(tx_hash, command)
  except McpToolError as e:
      # MCP server returned error
      logger.error(f"MCP tool failed: {e}")
      raise LendingOperationFailedError(original_error=e)
  except NetworkError as e:
      # Network timeout or connection issue
      raise ProtocolUnreachableError(protocol="aave")
  ```

### Edge Cases
- [ ] **Health Factor Edge Cases**
  - [ ] Health factor = 1.0 exactly (at liquidation threshold)
  - [ ] Health factor = ∞ (no debt, only collateral)
  - [ ] Health factor = 0 (fully liquidated)
  - [ ] Rapid health factor changes during volatile markets

- [ ] **Multi-Signature Workflow**
  - [ ] Partial signature collection (2 of 3 signed)
  - [ ] Signature expiration
  - [ ] Conflicting signatures (nonce mismatch)
  - [ ] Coordinator agent failure mid-flow

- [ ] **Protocol-Specific Edge Cases**
  - [ ] Aave: Variable vs stable rate selection
  - [ ] Morpho: Vault capacity limits
  - [ ] Both: Asset paused by governance
  - [ ] Both: Extreme APY changes during tx execution

---

## 4. Security Considerations

### Wallet Signature Validation
- [ ] **Signature Verification**
  ```python
  from eth_account.messages import encode_defunct
  from web3 import Web3

  class WalletSignatureValidator:
      def verify_signature(
          self, message: str, signature: str, expected_address: str
      ) -> bool:
          # Recreate message hash
          message_hash = encode_defunct(text=message)

          # Recover signer address
          recovered_address = Web3().eth.account.recover_message(
              message_hash, signature=signature
          )

          # Compare addresses (case-insensitive)
          return recovered_address.lower() == expected_address.lower()
  ```

- [ ] **Nonce Management**
  - [ ] Store used nonces to prevent replay attacks
  - [ ] Nonce expiration (e.g., 5 minutes)
  - [ ] User-specific nonce tracking

### Balance Checks
- [ ] **Pre-Flight Balance Validation**
  ```python
  async def _check_balance_before_supply(self, command: SupplyAssetCommand):
      balance = await self._balance_validator.get_balance(
          command.wallet_address, command.asset_address
      )

      if balance < command.amount:
          raise InsufficientBalanceError(
              available=balance,
              required=command.amount,
              asset=command.asset_address,
          )
  ```

- [ ] **Gas Reserve Checks**
  - [ ] Ensure user has enough ETH for gas
  - [ ] Gas estimation before tx submission
  - [ ] Fallback to higher gas limit if estimation fails

### Authorization
- [ ] **User Context Awareness**
  ```python
  # Guest users: read-only access
  @router.get("/rates")
  async def get_lending_rates(
      user_id: Optional[UUID] = Depends(get_current_user_id_optional),
  ):
      # Anyone can view rates

  # Authenticated users: write access
  @router.post("/supply")
  async def supply_asset(
      user_id: UUID = Depends(get_current_user_id_required),
  ):
      # Must be authenticated
  ```

- [ ] **Wallet Ownership Verification**
  - [ ] Verify user owns the wallet address
  - [ ] Store wallet<->user mapping in `user_wallets` table
  - [ ] Reject transactions for unowned wallets

### Rate Limiting
- [ ] **Transaction Rate Limits**
  - [ ] Max 10 lending operations per hour per user
  - [ ] Max 3 concurrent pending transactions per user
  - [ ] Exponential backoff on repeated failures

---

## 5. Performance Optimization

### MCP Call Caching
- [ ] **Market Data Caching**
  ```python
  from functools import lru_cache
  from datetime import datetime, timedelta

  class CachedAaveMcpAdapter:
      def __init__(self, adapter: AaveMcpAdapter, cache_ttl: int = 60):
          self._adapter = adapter
          self._cache: Dict[str, Tuple[MarketData, datetime]] = {}
          self._cache_ttl = timedelta(seconds=cache_ttl)

      async def get_market_data(self, asset: str) -> MarketData:
          # Check cache
          if asset in self._cache:
              data, cached_at = self._cache[asset]
              if datetime.utcnow() - cached_at < self._cache_ttl:
                  return data

          # Fetch fresh data
          data = await self._adapter.get_market_data(asset)
          self._cache[asset] = (data, datetime.utcnow())
          return data
  ```

- [ ] **Health Factor Caching**
  - [ ] Cache health factor for 30 seconds (frequently queried)
  - [ ] Invalidate on borrow/repay/supply/withdraw events
  - [ ] Use Redis for distributed caching

### Parallel Queries
- [ ] **Protocol Comparison Optimization**
  ```python
  async def get_best_lending_rates(self, asset: str) -> ProtocolComparison:
      # Parallel fetch from Aave and Morpho
      aave_data, morpho_data = await asyncio.gather(
          self._aave_adapter.get_market_data(asset),
          self._morpho_adapter.get_vault_data(asset),
          return_exceptions=True,
      )

      # Handle partial failures
      if isinstance(aave_data, Exception):
          logger.warning(f"Aave fetch failed: {aave_data}")
          aave_data = None

      if isinstance(morpho_data, Exception):
          logger.warning(f"Morpho fetch failed: {morpho_data}")
          morpho_data = None

      return ProtocolComparison(aave=aave_data, morpho=morpho_data)
  ```

### Database Optimization
- [ ] **Indexes**
  ```sql
  CREATE INDEX idx_lending_positions_user_id ON lending_positions(user_id);
  CREATE INDEX idx_lending_positions_protocol ON lending_positions(protocol);
  CREATE INDEX idx_lending_positions_health_factor ON lending_positions(health_factor) WHERE health_factor < 1.5;
  ```

- [ ] **Query Optimization**
  - [ ] Use `UserQueryGateway` for efficient reads
  - [ ] Avoid N+1 queries with eager loading
  - [ ] Paginate large result sets

---

## 6. Testing Strategy

### Unit Tests (Domain & Application)
- [ ] **Domain Services**
  ```python
  # tests/unit/domain/services/test_lending_risk_calculator.py
  def test_health_factor_calculation():
      calculator = LendingRiskCalculator()

      # Test safe position
      hf = calculator.calculate_health_factor(
          collateral_value=Decimal("1000"),
          borrowed_value=Decimal("500"),
          liquidation_threshold=Decimal("0.8"),
      )
      assert hf.value == 1.6  # (1000 * 0.8) / 500
      assert hf.is_safe

      # Test critical position
      hf = calculator.calculate_health_factor(
          collateral_value=Decimal("1000"),
          borrowed_value=Decimal("900"),
          liquidation_threshold=Decimal("0.8"),
      )
      assert hf.value < 1.2
      assert hf.is_critical
  ```

- [ ] **Command Interactors**
  ```python
  # tests/unit/application/lending/test_supply_asset_interactor.py
  @pytest.mark.asyncio
  async def test_supply_asset_success(mocker):
      # Mock dependencies
      mock_gateway = mocker.AsyncMock(spec=ILendingProtocolGateway)
      mock_balance_validator = mocker.AsyncMock(spec=IBalanceValidator)
      mock_command_gateway = mocker.AsyncMock(spec=UserCommandGateway)

      mock_balance_validator.has_sufficient_balance.return_value = True
      mock_gateway.supply_asset.return_value = "0xabc123..."

      interactor = SupplyAssetInteractor(
          lending_gateway=mock_gateway,
          balance_validator=mock_balance_validator,
          command_gateway=mock_command_gateway,
      )

      command = SupplyAssetCommand(
          user_id=UUID("..."),
          protocol="aave",
          asset_address="0x...",
          amount=Decimal("100"),
          wallet_address="0x...",
      )

      result = await interactor.execute(command)

      assert result.tx_hash == "0xabc123..."
      mock_gateway.supply_asset.assert_called_once()
  ```

- [ ] **Error Scenarios**
  ```python
  @pytest.mark.asyncio
  async def test_supply_asset_insufficient_balance(mocker):
      mock_balance_validator = mocker.AsyncMock(spec=IBalanceValidator)
      mock_balance_validator.has_sufficient_balance.return_value = False

      interactor = SupplyAssetInteractor(
          balance_validator=mock_balance_validator,
          # ...other mocks
      )

      with pytest.raises(InsufficientBalanceError):
          await interactor.execute(command)
  ```

### Integration Tests (Infrastructure)
- [ ] **Aave MCP Adapter**
  ```python
  # tests/integration/infrastructure/adapters/test_aave_mcp_adapter.py
  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_aave_get_market_data_real_mcp():
      # Assumes Aave MCP server running on port 8085
      client = McpClient(base_url="http://localhost:8085")
      adapter = AaveMcpAdapter(client)

      market_data = await adapter.get_market_data(
          asset="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC
      )

      assert market_data.supply_apy > 0
      assert market_data.borrow_apy > 0
      assert market_data.total_supply > 0
  ```

- [ ] **Database Persistence**
  ```python
  # tests/integration/infrastructure/persistence/test_lending_position_repository.py
  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_save_and_retrieve_lending_position(db_session):
      repository = LendingPositionRepository(db_session)

      position = LendingPosition(
          id=UUID("..."),
          user_id=UUID("..."),
          protocol="aave",
          asset_address="0x...",
          supplied_amount=Decimal("1000"),
          health_factor=HealthFactor(2.5),
      )

      await repository.save(position)
      await db_session.commit()

      retrieved = await repository.find_by_id(position.id)
      assert retrieved.health_factor.value == 2.5
  ```

### End-to-End Tests (Lending Flows)
- [ ] **Full Supply Flow**
  ```python
  # tests/e2e/test_lending_supply_flow.py
  @pytest.mark.e2e
  @pytest.mark.asyncio
  async def test_supply_asset_e2e(
      authenticated_client: AsyncClient,
      test_user: User,
      mock_wallet: str,
  ):
      # 1. Get current rates
      response = await authenticated_client.get("/api/v1/lending/rates")
      assert response.status_code == 200

      # 2. Submit supply transaction
      response = await authenticated_client.post(
          "/api/v1/lending/supply",
          json={
              "protocol": "aave",
              "asset_address": "0x...",
              "amount": "100.0",
              "wallet_address": mock_wallet,
          },
      )
      assert response.status_code == 202  # Accepted
      tx_hash = response.json()["tx_hash"]

      # 3. Poll for confirmation
      await asyncio.sleep(10)  # Wait for block confirmation

      # 4. Verify position created
      response = await authenticated_client.get("/api/v1/lending/positions")
      positions = response.json()["positions"]
      assert any(p["tx_hash"] == tx_hash for p in positions)
  ```

- [ ] **Borrow Against Collateral Flow**
  ```python
  @pytest.mark.e2e
  @pytest.mark.asyncio
  async def test_borrow_against_collateral_e2e(authenticated_client):
      # 1. Supply collateral
      supply_response = await authenticated_client.post("/api/v1/lending/supply", ...)

      # 2. Wait for confirmation
      await wait_for_tx_confirmation(supply_response.json()["tx_hash"])

      # 3. Check health factor
      hf_response = await authenticated_client.get("/api/v1/lending/health-factor")
      assert hf_response.json()["health_factor"] == float('inf')  # No debt yet

      # 4. Borrow asset
      borrow_response = await authenticated_client.post(
          "/api/v1/lending/borrow",
          json={"asset_address": "0x...", "amount": "50.0"},
      )
      assert borrow_response.status_code == 202

      # 5. Verify health factor updated
      hf_response = await authenticated_client.get("/api/v1/lending/health-factor")
      assert 1.0 < hf_response.json()["health_factor"] < float('inf')
  ```

### Test Coverage Requirements
- [ ] **Minimum Coverage**
  - [ ] Domain layer: 90%+
  - [ ] Application layer: 85%+
  - [ ] Infrastructure adapters: 70%+
  - [ ] Presentation layer: 60%+

- [ ] **Critical Paths 100% Coverage**
  - [ ] Balance validation logic
  - [ ] Health factor calculation
  - [ ] Transaction pre-checks
  - [ ] Error handling paths

---

## 7. Documentation Requirements

- [ ] **API Documentation**
  - [ ] OpenAPI schemas for all endpoints
  - [ ] Example requests/responses
  - [ ] Error code documentation

- [ ] **Architecture Documentation**
  - [ ] Component diagram (domain, application, infrastructure)
  - [ ] Sequence diagrams for key flows (supply, borrow, liquidation)
  - [ ] MCP integration architecture

- [ ] **Developer Guide**
  - [ ] How to add new lending protocols
  - [ ] How to add new MCP tools
  - [ ] Testing guidelines

---

## 8. Deployment Checklist

- [ ] **Configuration**
  - [ ] MCP server URLs in TOML config
  - [ ] Aave: `http://localhost:8085`
  - [ ] Morpho: `http://localhost:8088`
  - [ ] Cache TTL settings
  - [ ] Rate limit configurations

- [ ] **Database Migrations**
  - [ ] `lending_positions` table created
  - [ ] `lending_transactions` table created
  - [ ] Indexes applied
  - [ ] Foreign key constraints

- [ ] **Monitoring**
  - [ ] Health factor alerts (< 1.5)
  - [ ] Transaction failure rate tracking
  - [ ] MCP server availability monitoring
  - [ ] APY change notifications

---

## Review Sign-Off

- [ ] **Architecture Review** (@software-engineering-expert)
- [ ] **Security Review** (@security-specialist)
- [ ] **Performance Review** (@performance-optimizer)
- [ ] **Testing Review** (@test-automation-expert)
- [ ] **Documentation Review** (@documentation-specialist)

**Final Approval**: @code-reviewer
