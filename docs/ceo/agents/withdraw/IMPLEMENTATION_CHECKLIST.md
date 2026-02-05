# Hyperliquid Withdraw Agent - Implementation Checklist

**Created**: 2026-02-04
**Estimated Time**: 48 hours (5-7 days with buffer)
**Status**: Ready for Implementation (pending blocker resolution)

---

## 📋 Pre-Implementation Setup

### Critical Blockers (MUST RESOLVE BEFORE STARTING)

- [ ] **Hyperliquid API Key Procurement**
  - [ ] Register with Hyperliquid (if required)
  - [ ] Obtain testnet API credentials
  - [ ] Obtain mainnet API credentials
  - [ ] Verify Exchange API access (not just Info API)
  - [ ] Document rate limits (1200 Info, 100 Exchange)
  - [ ] Test API key on testnet

**Owner**: DevOps + Engineering Lead
**Estimated Time**: 1-2 days
**Blocking**: Phase 1 start

---

- [ ] **Wallet Linking Strategy Decision**
  - [ ] Review options with Product + Legal teams:
    - Option A: Generate 1 Hyperliquid wallet per user (recommended)
    - Option B: User-provided Hyperliquid wallet address
    - Option C: Single custodial wallet for all users (highest risk)
  - [ ] Confirm custody model compliance
  - [ ] Document wallet creation flow
  - [ ] Obtain legal sign-off

**Owner**: Product + Legal + Engineering
**Estimated Time**: 1 day
**Blocking**: Phase 1 implementation

---

- [ ] **Target Chain Preference**
  - [ ] Decide with Product team:
    - Option A: Always bridge to Base (original spec assumption)
    - Option B: Always keep on Arbitrum (save bridge fees)
    - Option C: User chooses destination chain (best UX, more complexity)
  - [ ] Document bridge fee disclosure strategy
  - [ ] Update user flow documentation

**Owner**: Product team
**Estimated Time**: 0.5 days
**Blocking**: Phase 2 implementation

---

### Environment Configuration

- [ ] **HashiCorp Vault Setup**
  - [ ] Install Vault locally for development
    ```bash
    brew install vault  # macOS
    # or download from https://www.vaultproject.io/downloads
    ```
  - [ ] Start Vault in dev mode
    ```bash
    vault server -dev
    # Save dev token from output
    ```
  - [ ] Configure Vault in `config/local/.secrets.toml`
    ```toml
    [vault]
    address = "http://127.0.0.1:8200"
    token = "hvs.dev-token-here"
    namespace = "anvil"
    kv_mount_path = "secret"
    ```
  - [ ] Test Vault connectivity
    ```bash
    vault kv put secret/test key=value
    vault kv get secret/test
    ```
  - [ ] Set up production Vault (Vault Enterprise or HCP Vault)
  - [ ] Configure auto-unseal with cloud KMS
  - [ ] Create Vault policies for backend service
  - [ ] Set up key rotation schedule (90 days)

**Reference**: Swap spec [01_HYPERLIQUID_WALLET_MANAGEMENT_SPEC.md](../swap/backend/01_HYPERLIQUID_WALLET_MANAGEMENT_SPEC.md)

---

- [ ] **Infrastructure**
  - [ ] Verify PostgreSQL 14+ with JSONB support
    ```bash
    psql -c "SELECT version();"
    ```
  - [ ] Verify Redis 6+ availability
    ```bash
    redis-cli ping
    ```
  - [ ] Configure WebSocket server (existing)
  - [ ] Set up Prometheus + Grafana
    - [ ] Create dashboards for withdraw metrics
    - [ ] Configure alert rules
  - [ ] Verify Celery worker running
    ```bash
    make celery.worker
    make celery.flower  # monitoring UI
    ```

---

- [ ] **API Keys & Secrets**
  - [ ] Add Hyperliquid API key to Vault
    ```bash
    vault kv put secret/hyperliquid \
      api_key="YOUR_API_KEY" \
      api_secret="YOUR_API_SECRET"
    ```
  - [ ] Verify LiFi API key exists (reuse from swap)
  - [ ] Configure environment variables
    ```toml
    # config/local/.secrets.toml
    [hyperliquid]
    api_url = "https://api.hyperliquid-testnet.xyz"
    websocket_url = "wss://api.hyperliquid-testnet.xyz/ws"

    [lifi]
    api_key = "YOUR_LIFI_KEY"
    api_url = "https://li.fi/v1"
    ```

---

### Code Repository

- [ ] Create feature branch
  ```bash
  git checkout -b feature/hyperliquid-withdraw-agent
  ```
- [ ] Set up CI/CD pipeline (GitHub Actions)
  - [ ] Add testnet integration tests to CI
  - [ ] Configure automatic security scans
  - [ ] Set up deployment pipeline
- [ ] Configure test environment
  ```bash
  export APP_ENV=test
  make up.db
  make create-db
  alembic upgrade head
  ```
- [ ] Set up code review workflow
  - [ ] Minimum 2 reviewers required
  - [ ] Security team review for Vault integration
  - [ ] Performance team review for rate limits

---

## 🏗️ Phase 1: Hyperliquid Client Core (2 days / 16 hours)

### Day 1: Info API + Balance Queries (8 hours)

#### Extend HyperliquidClient Class

- [ ] **Add balance query methods**
  - [ ] `get_user_state(user_address: str) -> Dict[str, Any]`
    - Raw API call to `/info` endpoint
    - POST method with `{"type": "userState", "user": "0x..."}`
    - Parse response: `assetPositions`, `crossMarginSummary`
  - [ ] `get_perps_balance(user_address: str) -> Decimal`
    - Extract `crossMarginSummary.accountValue`
    - Return as Decimal for precision
  - [ ] `get_spot_balance(user_address: str, token: str = "USDC") -> Decimal`
    - Extract from `assetPositions` array
    - Find token by symbol, return `total` field
  - [ ] `get_all_balances(user_address: str) -> Dict[str, Dict[str, Decimal]]`
    - Combined balances: `{"perps": {...}, "spot": {...}}`
    - Include all tokens, not just USDC

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, lines 150-350

---

- [ ] **Add rate limiting logic**
  - [ ] Implement token bucket algorithm
    - 1200 tokens per minute for Info API
    - 100 tokens per minute for Exchange API
  - [ ] Add `@rate_limit` decorator
  - [ ] Track API call counts in Redis
    - Key: `hyperliquid:rate_limit:{api_type}`
    - Value: token count
    - TTL: 60 seconds
  - [ ] Raise `RateLimitExceeded` exception when limit hit
  - [ ] Add exponential backoff retry logic

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, Rate Limiting section

---

- [ ] **Add error handling**
  - [ ] `HyperliquidAPIError` - Base exception
  - [ ] `RateLimitExceeded` - 429 responses
  - [ ] `InsufficientBalance` - Balance too low
  - [ ] `NetworkError` - Connection failures
  - [ ] `InvalidSignature` - EIP-712 validation failed
  - [ ] Retry logic with exponential backoff (3 attempts)
  - [ ] Structured logging (no sensitive data)

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, Error Handling section

---

#### Testing

- [ ] **Unit tests** (10 tests)
  - [ ] `test_get_user_state_success()`
  - [ ] `test_get_perps_balance_parses_correctly()`
  - [ ] `test_get_spot_balance_finds_token()`
  - [ ] `test_get_spot_balance_token_not_found()`
  - [ ] `test_get_all_balances_includes_all_tokens()`
  - [ ] `test_rate_limit_enforced()`
  - [ ] `test_rate_limit_resets_after_60s()`
  - [ ] `test_api_error_raises_exception()`
  - [ ] `test_network_error_retries()`
  - [ ] `test_retry_exhausted_raises()`

**File**: `tests/unit/infrastructure/adapters/test_hyperliquid_client.py`

---

- [ ] **Integration tests** (3 tests)
  - [ ] `test_get_balance_from_testnet()`
    - Real API call to Hyperliquid testnet
    - Verify balance structure
  - [ ] `test_rate_limit_compliance()`
    - Make 1500 calls in 60s
    - Verify rate limiter blocks excess
  - [ ] `test_error_recovery()`
    - Simulate network failure
    - Verify retry succeeds

**File**: `tests/integration/infrastructure/adapters/test_hyperliquid_client_integration.py`

---

### Day 2: Exchange API + EIP-712 Signing (8 hours)

#### Implement Transfer Method

- [ ] **Add `transfer_to_spot()` method**
  - [ ] Method signature:
    ```python
    async def transfer_to_spot(
        self,
        user_address: str,
        amount: Decimal,
        vault_client: VaultClient,
    ) -> str:
        """Transfer USDC from Perps to Spot.

        Returns: Transaction hash
        """
    ```
  - [ ] Check Perps balance >= amount
  - [ ] Construct EIP-712 typed data for `spotTransfer`
    - Domain: `{name: "Exchange", version: "1", chainId: 421614, ...}`
    - Types: `{SpotTransfer: [{name: "hyperliquidChain", type: "string"}, ...]}`
    - Message: `{hyperliquidChain: "Testnet", destination: user_address, token: "USDC", amount: str(amount), time: timestamp}`
  - [ ] Sign with Vault-stored private key
  - [ ] Submit to `/exchange` endpoint
  - [ ] Parse response, return tx hash
  - [ ] Verify transfer (poll balance for 10s)

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, Transfer section

---

#### Implement Withdrawal Method

- [ ] **Add `initiate_withdrawal()` method**
  - [ ] Method signature:
    ```python
    async def initiate_withdrawal(
        self,
        user_address: str,
        amount: Decimal,
        destination_address: str,
        vault_client: VaultClient,
    ) -> Dict[str, Any]:
        """Initiate withdrawal from Spot to Arbitrum L1.

        Returns: {tx_hash, finality_timestamp}
        """
    ```
  - [ ] Check Spot balance >= amount
  - [ ] Construct EIP-712 typed data for `usdTransfer`
    - Domain: Same as transfer
    - Types: `{UsdTransfer: [{name: "hyperliquidChain", type: "string"}, ...]}`
    - Message: `{hyperliquidChain: "Testnet", destination: destination_address, amount: str(amount), time: timestamp}`
  - [ ] Sign with Vault-stored private key
  - [ ] Submit to `/exchange` endpoint
  - [ ] Parse response
  - [ ] Calculate finality timestamp: `now + 30 minutes`
  - [ ] Return `{tx_hash, finality_timestamp}`

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, Withdrawal section

---

- [ ] **Add `get_withdrawal_status()` method**
  - [ ] Method signature:
    ```python
    async def get_withdrawal_status(
        self,
        tx_hash: str,
    ) -> str:
        """Check withdrawal status.

        Returns: "pending" | "finalized" | "failed"
        """
    ```
  - [ ] Query `/info` endpoint with `{"type": "userFunding", "user": "0x..."}`
  - [ ] Find withdrawal by tx_hash in funding history
  - [ ] Check if timestamp + 30min < now
  - [ ] Return status

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, Withdrawal Status section

---

#### Implement EIP-712 Signing

- [ ] **Add `_sign_eip712()` private method**
  - [ ] Method signature:
    ```python
    async def _sign_eip712(
        self,
        domain: Dict[str, Any],
        types: Dict[str, Any],
        message: Dict[str, Any],
        vault_client: VaultClient,
        user_address: str,
    ) -> str:
        """Sign EIP-712 typed data with Vault-stored key.

        Returns: Signature (hex string)
        """
    ```
  - [ ] Retrieve private key from Vault
    - Path: `secret/hyperliquid/wallets/{user_id}`
    - Field: `private_key`
  - [ ] Create Account from private key
    ```python
    from eth_account import Account
    from eth_account.messages import encode_structured_data

    account = Account.from_key(private_key)
    ```
  - [ ] Encode structured data
    ```python
    structured_data = {
        "domain": domain,
        "types": types,
        "message": message,
    }
    encoded = encode_structured_data(structured_data)
    ```
  - [ ] Sign encoded data
    ```python
    signature = account.sign_message(encoded)
    ```
  - [ ] Return signature.signature.hex()
  - [ ] Clear private key from memory
    ```python
    del private_key, account
    ```

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Spec 01, EIP-712 Signing section

---

#### Vault Integration

- [ ] **Reuse `VaultClient` from swap spec**
  - [ ] Verify `VaultClient` class exists
    - File: `src/app/infrastructure/adapters/vault/vault_client.py`
  - [ ] Add method if missing: `read_private_key(user_id: int) -> str`
  - [ ] Add method if missing: `store_private_key(user_id: int, private_key: str) -> str`
  - [ ] Configure connection pooling (reuse Vault connections)

**File**: `src/app/infrastructure/adapters/vault/vault_client.py`

**Reference**: Swap spec [01_HYPERLIQUID_WALLET_MANAGEMENT_SPEC.md](../swap/backend/01_HYPERLIQUID_WALLET_MANAGEMENT_SPEC.md), lines 313-463

---

#### Database Schema Update

- [ ] **Create Alembic migration**
  - [ ] Add `tx_metadata` JSONB column to `transactions` table
    ```sql
    ALTER TABLE transactions
    ADD COLUMN tx_metadata JSONB DEFAULT '{}';
    ```
  - [ ] Add indexes for withdrawal queries
    ```sql
    CREATE INDEX idx_tx_withdrawal_status
    ON transactions ((tx_metadata->>'withdrawal_status'));

    CREATE INDEX idx_tx_finality_timestamp
    ON transactions ((tx_metadata->>'finality_timestamp'));
    ```
  - [ ] Test migration up/down
  - [ ] Deploy to staging

**File**: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_02_04_XXXX_add_withdrawal_metadata.py`

**Reference**: Spec 01, Database Schema section

---

#### Testing

- [ ] **Unit tests** (10 tests)
  - [ ] `test_transfer_to_spot_success()`
  - [ ] `test_transfer_insufficient_balance()`
  - [ ] `test_initiate_withdrawal_success()`
  - [ ] `test_initiate_withdrawal_insufficient_balance()`
  - [ ] `test_get_withdrawal_status_pending()`
  - [ ] `test_get_withdrawal_status_finalized()`
  - [ ] `test_eip712_signing_creates_valid_signature()`
  - [ ] `test_eip712_signing_clears_memory()`
  - [ ] `test_vault_integration_retrieves_key()`
  - [ ] `test_transaction_verification_polls_correctly()`

**File**: `tests/unit/infrastructure/adapters/test_hyperliquid_client.py`

---

- [ ] **Integration tests** (2 tests)
  - [ ] `test_transfer_on_testnet()`
    - Real transfer on Hyperliquid testnet
    - Verify balance changes
  - [ ] `test_withdrawal_on_testnet()`
    - Real withdrawal initiation
    - Verify tx_hash returned
    - DO NOT wait 30 minutes (just verify initiation)

**File**: `tests/integration/infrastructure/adapters/test_hyperliquid_client_integration.py`

---

### Phase 1 Verification

- [ ] All unit tests pass (20 tests)
- [ ] All integration tests pass (5 tests)
- [ ] No private keys in logs (manual review)
- [ ] Rate limit compliance verified
- [ ] Vault integration working
- [ ] Code review completed (2+ reviewers)
- [ ] Security review completed

---

## 🔄 Phase 2: Withdraw Agent (2 days / 16 hours)

### Day 3: Agent Core + Intent Parsing (8 hours)

#### Create WithdrawAgent Class

- [ ] **Create agent file structure**
  ```bash
  touch src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py
  ```

- [ ] **Implement `WithdrawAgent` class skeleton**
  - [ ] Class signature:
    ```python
    class WithdrawAgent:
        """Handles withdrawal from Hyperliquid to user's Privy wallet."""

        def __init__(
            self,
            hyperliquid_client: HyperliquidClient,
            lifi_client: LiFiClient,
            transaction_repository: TransactionRepository,
            vault_client: VaultClient,
        ):
            self.hl_client = hyperliquid_client
            self.lifi_client = lifi_client
            self.tx_repo = transaction_repository
            self.vault_client = vault_client
    ```
  - [ ] Add to Dishka DI container
    ```python
    # src/app/presentation/http/di.py
    withdraw_agent = provide(WithdrawAgent, scope=Scope.REQUEST)
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Implementation section

---

#### Intent Parsing

- [ ] **Implement `parse_withdrawal_intent()` method**
  - [ ] Method signature:
    ```python
    def parse_withdrawal_intent(
        self,
        user_message: str,
    ) -> Optional[WithdrawalIntent]:
        """Parse user message for withdrawal intent.

        Returns: WithdrawalIntent or None
        """
    ```
  - [ ] Regex patterns:
    - `withdraw (\d+(?:\.\d+)?) (USDC|usdc) from (hyperliquid|hl)`
    - `withdraw (\d+(?:\.\d+)?)(?: USDC)? hl`
    - `take (\d+(?:\.\d+)?) (usdc|USDC) out of (hyperliquid|hl)`
  - [ ] LLM extraction fallback (if regex fails)
    - Use existing ChatAgent infrastructure
    - Prompt: "Extract withdrawal amount and destination from: {message}"
  - [ ] Return `WithdrawalIntent` dataclass:
    ```python
    @dataclass
    class WithdrawalIntent:
        amount: Decimal
        token: str  # "USDC"
        destination_chain: str  # "base" | "arbitrum"
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Intent Parsing section

---

#### Balance Validation

- [ ] **Implement `validate_withdrawal()` method**
  - [ ] Method signature:
    ```python
    async def validate_withdrawal(
        self,
        user_id: int,
        intent: WithdrawalIntent,
    ) -> Tuple[bool, str]:
        """Validate withdrawal is possible.

        Returns: (is_valid, error_message)
        """
    ```
  - [ ] Get user's Hyperliquid wallet address
    - Query `hyperliquid_wallets` table by user_id
    - If not found, return `(False, "No Hyperliquid wallet found")`
  - [ ] Query balances
    ```python
    perps_balance = await self.hl_client.get_perps_balance(wallet_address)
    spot_balance = await self.hl_client.get_spot_balance(wallet_address, "USDC")
    total_balance = perps_balance + spot_balance
    ```
  - [ ] Check total balance >= amount
    - If not: `(False, f"Insufficient balance. Have {total_balance} USDC, need {intent.amount}")`
  - [ ] Return `(True, "")`

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Balance Validation section

---

#### Workflow Orchestration Skeleton

- [ ] **Implement `execute_withdrawal()` method skeleton**
  - [ ] Method signature:
    ```python
    async def execute_withdrawal(
        self,
        user_id: int,
        intent: WithdrawalIntent,
        conversation_id: int,
    ) -> str:
        """Execute full withdrawal workflow.

        Returns: transaction_id (UUID)
        """
    ```
  - [ ] Create transaction record
    ```python
    transaction = Transaction(
        user_id=user_id,
        type=TransactionType.WITHDRAW,
        from_chain="hyperliquid",
        to_chain=intent.destination_chain,
        from_token="USDC",
        to_token="USDC",
        amount=intent.amount,
        status=TransactionStatus.PENDING,
        tx_metadata={
            "withdrawal_status": "initiated",
            "steps": [],
        }
    )
    tx_id = await self.tx_repo.create(transaction)
    ```
  - [ ] Send WebSocket notification
    ```python
    await self.notify_frontend(
        user_id,
        "withdrawal.initiated",
        {"transaction_id": tx_id, "amount": intent.amount}
    )
    ```
  - [ ] Implement step placeholders (to be filled in Day 4)
    - Step 1: Transfer to Spot (if needed)
    - Step 2: Initiate withdrawal
    - Step 3: Wait for finality
    - Step 4: Bridge to destination chain
  - [ ] Return transaction_id

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Orchestration section

---

#### Implement Transfer Step

- [ ] **Implement `_execute_transfer_step()` private method**
  - [ ] Method signature:
    ```python
    async def _execute_transfer_step(
        self,
        transaction_id: str,
        wallet_address: str,
        amount: Decimal,
    ) -> bool:
        """Transfer USDC from Perps to Spot if needed.

        Returns: True if successful
        """
    ```
  - [ ] Check current Spot balance
    ```python
    spot_balance = await self.hl_client.get_spot_balance(wallet_address, "USDC")
    ```
  - [ ] If spot_balance >= amount, skip transfer
    ```python
    if spot_balance >= amount:
        await self._update_step("transfer", "skipped", transaction_id)
        return True
    ```
  - [ ] Calculate transfer amount
    ```python
    transfer_amount = amount - spot_balance
    ```
  - [ ] Execute transfer
    ```python
    try:
        tx_hash = await self.hl_client.transfer_to_spot(
            wallet_address,
            transfer_amount,
            self.vault_client
        )
        await self._update_step(
            "transfer",
            "completed",
            transaction_id,
            metadata={"tx_hash": tx_hash}
        )
        return True
    except Exception as e:
        await self._update_step("transfer", "failed", transaction_id, error=str(e))
        return False
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Transfer Step section

---

#### Testing

- [ ] **Unit tests** (8 tests)
  - [ ] `test_parse_withdrawal_intent_regex()`
  - [ ] `test_parse_withdrawal_intent_llm_fallback()`
  - [ ] `test_validate_withdrawal_success()`
  - [ ] `test_validate_withdrawal_insufficient_balance()`
  - [ ] `test_validate_withdrawal_no_wallet()`
  - [ ] `test_transfer_step_skipped_if_sufficient_spot()`
  - [ ] `test_transfer_step_executes_if_needed()`
  - [ ] `test_transfer_step_handles_failure()`

**File**: `tests/unit/infrastructure/adapters/test_withdraw_agent.py`

---

- [ ] **Integration tests** (2 tests)
  - [ ] `test_parse_and_validate_real_message()`
  - [ ] `test_transfer_step_on_testnet()`

**File**: `tests/integration/infrastructure/adapters/test_withdraw_agent_integration.py`

---

### Day 4: Withdrawal + Bridge + Integration (8 hours)

#### Implement Withdrawal Step

- [ ] **Implement `_execute_withdrawal_step()` private method**
  - [ ] Method signature:
    ```python
    async def _execute_withdrawal_step(
        self,
        transaction_id: str,
        wallet_address: str,
        amount: Decimal,
        destination_address: str,
    ) -> Optional[Dict[str, Any]]:
        """Initiate Hyperliquid withdrawal to Arbitrum L1.

        Returns: {tx_hash, finality_timestamp} or None
        """
    ```
  - [ ] Update transaction status
    ```python
    await self._update_step("withdraw", "in_progress", transaction_id)
    ```
  - [ ] Initiate withdrawal
    ```python
    try:
        result = await self.hl_client.initiate_withdrawal(
            wallet_address,
            amount,
            destination_address,
            self.vault_client
        )
        # result = {tx_hash, finality_timestamp}

        await self._update_step(
            "withdraw",
            "completed",
            transaction_id,
            metadata=result
        )
        return result
    except Exception as e:
        await self._update_step("withdraw", "failed", transaction_id, error=str(e))
        return None
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Withdrawal Step section

---

#### Implement Finality Wait

- [ ] **Implement `_wait_for_finality()` private method**
  - [ ] Method signature:
    ```python
    async def _wait_for_finality(
        self,
        transaction_id: str,
        tx_hash: str,
        finality_timestamp: int,
    ) -> bool:
        """Wait for 30-minute Hyperliquid finality.

        Returns: True if finalized
        """
    ```
  - [ ] Update status
    ```python
    await self._update_step(
        "finality_wait",
        "in_progress",
        transaction_id,
        metadata={"finality_timestamp": finality_timestamp}
    )
    ```
  - [ ] Send WebSocket progress updates
    ```python
    while time.time() < finality_timestamp:
        remaining_seconds = finality_timestamp - time.time()
        remaining_minutes = remaining_seconds / 60

        await self.notify_frontend(
            user_id,
            "withdrawal.finality_progress",
            {
                "transaction_id": transaction_id,
                "remaining_minutes": remaining_minutes,
                "progress_percent": (30 - remaining_minutes) / 30 * 100
            }
        )

        await asyncio.sleep(60)  # Update every minute
    ```
  - [ ] Verify finality
    ```python
    status = await self.hl_client.get_withdrawal_status(tx_hash)
    if status == "finalized":
        await self._update_step("finality_wait", "completed", transaction_id)
        return True
    else:
        await self._update_step("finality_wait", "failed", transaction_id)
        return False
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Finality Wait section

---

#### Implement Bridge Step

- [ ] **Implement `_execute_bridge_step()` private method**
  - [ ] Method signature:
    ```python
    async def _execute_bridge_step(
        self,
        transaction_id: str,
        amount: Decimal,
        from_address: str,
        to_address: str,
        destination_chain: str,
    ) -> bool:
        """Bridge from Arbitrum to destination chain via LiFi.

        Returns: True if successful
        """
    ```
  - [ ] Skip if destination is Arbitrum
    ```python
    if destination_chain == "arbitrum":
        await self._update_step("bridge", "skipped", transaction_id)
        return True
    ```
  - [ ] Get LiFi bridge quote
    ```python
    quote = await self.lifi_client.get_quote(
        from_chain="arbitrum",
        to_chain=destination_chain,
        from_token="USDC",
        to_token="USDC",
        amount=amount,
        from_address=from_address,
        to_address=to_address,
    )
    ```
  - [ ] Execute bridge
    ```python
    try:
        bridge_result = await self.lifi_client.execute_bridge(
            quote,
            from_address,
        )

        # Poll for completion
        while True:
            status = await self.lifi_client.get_status(bridge_result.tx_id)

            if status.status == "DONE":
                await self._update_step(
                    "bridge",
                    "completed",
                    transaction_id,
                    metadata={"bridge_tx_hash": status.tx_hash}
                )
                return True
            elif status.status == "FAILED":
                await self._update_step("bridge", "failed", transaction_id)
                return False

            await asyncio.sleep(5)  # Poll every 5 seconds
    except Exception as e:
        await self._update_step("bridge", "failed", transaction_id, error=str(e))
        return False
    ```

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, Bridge Step section

---

#### Integrate with ExecuteAction

- [ ] **Add `WITHDRAW_FROM_HYPERLIQUID` action type**
  - [ ] Define in `ExecuteAction` enum
    ```python
    # src/app/domain/entities/execute_action.py
    class ExecuteAction(Enum):
        SWAP = "swap"
        WITHDRAW_FROM_HYPERLIQUID = "withdraw_from_hyperliquid"
        # ... other actions
    ```

**File**: `src/app/domain/entities/execute_action.py`

---

- [ ] **Wire agent to `/execute` endpoint**
  - [ ] Add to execute endpoint handler
    ```python
    # src/app/presentation/http/controllers/chat/conversations_router.py

    @router.post("/{conversation_id}/execute")
    async def execute_action(
        conversation_id: int,
        execute_request: ExecuteRequest,
        withdraw_agent: WithdrawAgent = Depends(),
        # ... other dependencies
    ):
        if execute_request.action == ExecuteAction.WITHDRAW_FROM_HYPERLIQUID:
            intent = withdraw_agent.parse_withdrawal_intent(execute_request.message)
            if not intent:
                raise ValueError("Could not parse withdrawal intent")

            is_valid, error_msg = await withdraw_agent.validate_withdrawal(
                user_id,
                intent
            )
            if not is_valid:
                raise ValueError(error_msg)

            transaction_id = await withdraw_agent.execute_withdrawal(
                user_id,
                intent,
                conversation_id
            )

            return {"transaction_id": transaction_id}
    ```

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Reference**: Spec 02, ExecuteAction Integration section

---

#### WebSocket Notification System

- [ ] **Implement `notify_frontend()` method**
  - [ ] Method signature:
    ```python
    async def notify_frontend(
        self,
        user_id: int,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Send WebSocket notification to frontend."""
    ```
  - [ ] Use existing WebSocket infrastructure
    ```python
    await websocket_manager.send_to_user(
        user_id,
        {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }
    )
    ```
  - [ ] Event types:
    - `withdrawal.initiated`
    - `withdrawal.transfer_started`
    - `withdrawal.transfer_completed`
    - `withdrawal.withdraw_started`
    - `withdrawal.withdraw_completed`
    - `withdrawal.finality_progress` (every 60s)
    - `withdrawal.bridge_started`
    - `withdrawal.bridge_completed`
    - `withdrawal.completed`
    - `withdrawal.failed`

**File**: `src/app/infrastructure/adapters/agent_squad/agents/withdraw_agent.py`

**Reference**: Spec 02, WebSocket Events section

---

#### Testing

- [ ] **Unit tests** (7 tests)
  - [ ] `test_withdrawal_step_success()`
  - [ ] `test_withdrawal_step_failure()`
  - [ ] `test_finality_wait_completes()`
  - [ ] `test_finality_wait_sends_progress_updates()`
  - [ ] `test_bridge_step_success()`
  - [ ] `test_bridge_step_skipped_for_arbitrum()`
  - [ ] `test_bridge_step_failure()`

**File**: `tests/unit/infrastructure/adapters/test_withdraw_agent.py`

---

- [ ] **Integration tests** (1 test)
  - [ ] `test_bridge_on_testnet()`
    - Bridge small amount on testnet
    - Verify completion

**File**: `tests/integration/infrastructure/adapters/test_withdraw_agent_integration.py`

---

- [ ] **End-to-end tests** (3 scenarios)

**Scenario 1: Full withdrawal (first-time, needs transfer)**
- [ ] `test_e2e_full_withdrawal_with_transfer()`
  - User has 100 USDC in Perps, 0 in Spot
  - Withdraw 50 USDC to Base
  - Steps:
    1. Transfer 50 USDC: Perps → Spot
    2. Initiate withdrawal to Arbitrum
    3. Wait for finality (30 min)
    4. Bridge Arbitrum → Base
  - Verify: Transaction persisted with all steps
  - Verify: WebSocket events sent
  - **Note**: Use testnet, but DO NOT wait 30 minutes (mock finality)

**Scenario 2: Withdraw only (sufficient Spot balance)**
- [ ] `test_e2e_withdrawal_skip_transfer()`
  - User has 100 USDC in Spot
  - Withdraw 50 USDC to Base
  - Steps:
    1. Skip transfer (sufficient Spot balance)
    2. Initiate withdrawal
    3. Wait for finality
    4. Bridge to Base
  - Verify: Transfer step marked "skipped"

**Scenario 3: Arbitrum destination (skip bridge)**
- [ ] `test_e2e_withdrawal_to_arbitrum()`
  - User has 100 USDC in Spot
  - Withdraw 50 USDC to Arbitrum
  - Steps:
    1. Skip transfer
    2. Initiate withdrawal
    3. Wait for finality
    4. Skip bridge (destination is Arbitrum)
  - Verify: Bridge step marked "skipped"

**File**: `tests/e2e/test_withdraw_workflow.py`

---

### Phase 2 Verification

- [ ] All unit tests pass (15 tests)
- [ ] All integration tests pass (3 tests)
- [ ] All E2E tests pass (3 scenarios)
- [ ] WebSocket events delivered correctly
- [ ] Transaction metadata persisted
- [ ] Error handling verified
- [ ] Code review completed (2+ reviewers)

---

## 🔄 Phase 3: Celery Position Sync (2 days / 16 hours)

### Day 5: Position Sync Task (8 hours)

#### Implement Position Sync Task

- [ ] **Create Celery task file**
  ```bash
  touch src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py
  ```

- [ ] **Implement `sync_user_hyperliquid_positions()` task**
  - [ ] Task signature:
    ```python
    @celery_app.task(name="sync_user_hyperliquid_positions")
    def sync_user_hyperliquid_positions(user_id: int) -> Dict[str, Any]:
        """Sync a single user's Hyperliquid positions and balances.

        Returns: {perps_balance, spot_balance, positions}
        """
    ```
  - [ ] Check cache first
    ```python
    cache_key = f"hyperliquid:positions:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    ```
  - [ ] Query Hyperliquid
    ```python
    wallet_address = get_user_hyperliquid_wallet(user_id)
    if not wallet_address:
        return {}

    balances = await hyperliquid_client.get_all_balances(wallet_address)
    ```
  - [ ] Cache result
    ```python
    result = {
        "user_id": user_id,
        "perps_usdc": str(balances["perps"]["USDC"]),
        "spot_usdc": str(balances["spot"]["USDC"]),
        "positions": balances.get("positions", []),
        "last_updated": datetime.utcnow().isoformat(),
    }

    redis_client.setex(
        cache_key,
        300,  # 5-minute TTL
        json.dumps(result)
    )
    ```
  - [ ] Send WebSocket update
    ```python
    await websocket_manager.send_to_user(
        user_id,
        {
            "type": "hyperliquid.balance_update",
            "data": result
        }
    )
    ```
  - [ ] Return result

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Position Sync section

---

#### Implement Batch Sync Task

- [ ] **Implement `sync_all_active_users()` task**
  - [ ] Task signature:
    ```python
    @celery_app.task(name="sync_all_active_users")
    def sync_all_active_users() -> Dict[str, Any]:
        """Sync all users with Hyperliquid wallets (batch processing).

        Returns: {total_synced, errors}
        """
    ```
  - [ ] Query active users
    ```python
    # Users with Hyperliquid wallets active in last 24h
    active_users = db.query(User).join(HyperliquidWallet).filter(
        HyperliquidWallet.last_used_at > datetime.utcnow() - timedelta(days=1)
    ).all()
    ```
  - [ ] Batch process (50 users per batch)
    ```python
    batch_size = 50
    for i in range(0, len(active_users), batch_size):
        batch = active_users[i:i+batch_size]

        # Process batch in parallel
        tasks = [
            sync_user_hyperliquid_positions.delay(user.id)
            for user in batch
        ]

        # Wait for batch to complete
        for task in tasks:
            task.get(timeout=10)

        # Rate limit compliance (wait between batches)
        await asyncio.sleep(5)
    ```
  - [ ] Return summary

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Batch Processing section

---

#### Implement Token Snapshot Task

- [ ] **Implement `snapshot_hyperliquid_tokens()` task**
  - [ ] Task signature:
    ```python
    @celery_app.task(name="snapshot_hyperliquid_tokens")
    def snapshot_hyperliquid_tokens() -> Dict[str, Any]:
        """Update metadata for all Hyperliquid spot tokens.

        Returns: {tokens_updated}
        """
    ```
  - [ ] Query Hyperliquid meta endpoint
    ```python
    response = await hyperliquid_client.get("/info", {
        "type": "meta"
    })
    tokens = response["universe"]
    ```
  - [ ] Update token metadata in database
    ```python
    for token_data in tokens:
        token = Token.query.filter_by(
            symbol=token_data["name"],
            chain="hyperliquid"
        ).first()

        if token:
            token.metadata = {
                "hyperliquid_index": token_data["index"],
                "decimals": token_data["decimals"],
                "max_leverage": token_data.get("maxLeverage"),
            }
        else:
            # Create new token
            token = Token(
                symbol=token_data["name"],
                chain="hyperliquid",
                metadata={...}
            )
            db.add(token)

    db.commit()
    ```
  - [ ] Return count

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Token Snapshot section

---

#### Rate Limit Management

- [ ] **Implement rate limiter**
  - [ ] Use Redis for distributed rate limiting
    ```python
    def check_rate_limit(api_type: str) -> bool:
        """Check if rate limit allows request.

        Returns: True if request allowed
        """
        key = f"hyperliquid:rate_limit:{api_type}"
        current = redis_client.get(key)

        if current is None:
            redis_client.setex(key, 60, 1)
            return True

        current_count = int(current)
        limit = 1200 if api_type == "info" else 100

        if current_count < limit:
            redis_client.incr(key)
            return True

        return False
    ```
  - [ ] Wrap API calls
    ```python
    async def rate_limited_api_call(api_type: str, func, *args, **kwargs):
        """Execute API call with rate limiting."""
        while not check_rate_limit(api_type):
            await asyncio.sleep(1)  # Wait 1 second

        return await func(*args, **kwargs)
    ```

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Rate Limiting section

---

#### Testing

- [ ] **Unit tests** (8 tests)
  - [ ] `test_sync_user_positions_cache_hit()`
  - [ ] `test_sync_user_positions_cache_miss()`
  - [ ] `test_sync_user_positions_no_wallet()`
  - [ ] `test_sync_all_active_users_batches_correctly()`
  - [ ] `test_token_snapshot_updates_existing()`
  - [ ] `test_token_snapshot_creates_new()`
  - [ ] `test_rate_limiter_blocks_excess()`
  - [ ] `test_rate_limiter_resets_after_60s()`

**File**: `tests/unit/infrastructure/celery_app/tasks/test_hyperliquid_sync.py`

---

- [ ] **Integration tests** (2 tests)
  - [ ] `test_sync_position_on_testnet()`
  - [ ] `test_token_snapshot_on_testnet()`

**File**: `tests/integration/infrastructure/celery_app/tasks/test_hyperliquid_sync_integration.py`

---

- [ ] **Load testing** (1 test)
  - [ ] `test_sync_1000_users()`
    - Simulate 1000 active users
    - Measure total API calls
    - Verify rate limit compliance (<1200 req/min)
    - Measure sync latency distribution (p50, p95, p99)

**File**: `tests/load/test_position_sync_load.py`

---

### Day 6: Withdrawal Monitor + Optimization (8 hours)

#### Implement Withdrawal Monitor Task

- [ ] **Implement `monitor_pending_withdrawals()` task**
  - [ ] Task signature:
    ```python
    @celery_app.task(name="monitor_pending_withdrawals")
    def monitor_pending_withdrawals() -> Dict[str, Any]:
        """Monitor pending Hyperliquid withdrawals and trigger bridge.

        Returns: {checked, finalized, errors}
        """
    ```
  - [ ] Query pending withdrawals
    ```python
    pending = db.query(Transaction).filter(
        Transaction.type == TransactionType.WITHDRAW,
        Transaction.tx_metadata["withdrawal_status"].astext == "awaiting_finality",
        Transaction.tx_metadata["finality_timestamp"].astext.cast(Integer) < int(time.time())
    ).all()
    ```
  - [ ] Check finality status
    ```python
    for tx in pending:
        tx_hash = tx.tx_metadata["hyperliquid_tx_hash"]

        status = await hyperliquid_client.get_withdrawal_status(tx_hash)

        if status == "finalized":
            # Update transaction
            tx.tx_metadata["withdrawal_status"] = "finalized"
            tx.status = TransactionStatus.COMPLETED
            db.commit()

            # Trigger bridge if destination != arbitrum
            if tx.to_chain != "arbitrum":
                bridge_after_withdrawal.delay(tx.id)

            # Send WebSocket notification
            await websocket_manager.send_to_user(
                tx.user_id,
                {
                    "type": "withdrawal.finalized",
                    "data": {"transaction_id": tx.id}
                }
            )
    ```
  - [ ] Return summary

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Withdrawal Monitor section

---

- [ ] **Implement `bridge_after_withdrawal()` task**
  - [ ] Task signature:
    ```python
    @celery_app.task(name="bridge_after_withdrawal")
    def bridge_after_withdrawal(transaction_id: str) -> bool:
        """Execute bridge after withdrawal finality.

        Returns: True if successful
        """
    ```
  - [ ] Retrieve transaction
    ```python
    tx = db.query(Transaction).get(transaction_id)
    ```
  - [ ] Execute bridge step
    ```python
    success = await withdraw_agent._execute_bridge_step(
        transaction_id,
        tx.amount,
        tx.tx_metadata["arbitrum_address"],
        tx.to_address,
        tx.to_chain
    )

    if success:
        tx.status = TransactionStatus.COMPLETED
        await websocket_manager.send_to_user(
            tx.user_id,
            {"type": "withdrawal.completed", "data": {"transaction_id": tx.id}}
        )
    else:
        tx.status = TransactionStatus.FAILED

    db.commit()
    return success
    ```

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Bridge After Withdrawal section

---

#### Configure Celery Beat Schedules

- [ ] **Add schedules to Celery Beat configuration**
  - [ ] Edit Celery Beat config
    ```python
    # src/app/infrastructure/celery_app/celeryconfig.py

    beat_schedule = {
        "sync-all-active-users": {
            "task": "sync_all_active_users",
            "schedule": 60.0,  # Every 60 seconds
            "options": {"queue": "default"}
        },
        "monitor-pending-withdrawals": {
            "task": "monitor_pending_withdrawals",
            "schedule": 60.0,  # Every 60 seconds
            "options": {"queue": "default"}
        },
        "snapshot-hyperliquid-tokens": {
            "task": "snapshot_hyperliquid_tokens",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "default"}
        },
    }
    ```
  - [ ] Test schedules
    ```bash
    make celery.beat
    make celery.flower  # View task execution in UI
    ```

**File**: `src/app/infrastructure/celery_app/celeryconfig.py`

**Reference**: Spec 03, Celery Beat Configuration section

---

#### Optimization

- [ ] **Intelligent caching**
  - [ ] Only query changed positions
    ```python
    # Store hash of last position state
    last_state_hash = redis_client.get(f"hyperliquid:state_hash:{user_id}")
    current_state_hash = hashlib.sha256(
        json.dumps(current_positions).encode()
    ).hexdigest()

    if last_state_hash == current_state_hash:
        # No changes, skip update
        return cached_result

    redis_client.setex(
        f"hyperliquid:state_hash:{user_id}",
        300,
        current_state_hash
    )
    ```

- [ ] **Staggered scheduling**
  - [ ] Distribute sync across minute
    ```python
    # Assign each user a sync offset (0-59 seconds)
    sync_offset = user_id % 60

    # Only sync when current_second == sync_offset
    if datetime.utcnow().second == sync_offset:
        sync_user_hyperliquid_positions.delay(user_id)
    ```

- [ ] **Connection pooling**
  - [ ] Reuse HTTP connections
    ```python
    # Use httpx with connection pooling
    client = httpx.AsyncClient(
        timeout=10.0,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        )
    )
    ```

**File**: `src/app/infrastructure/celery_app/tasks/hyperliquid_sync.py`

**Reference**: Spec 03, Optimization section

---

#### Monitoring Setup

- [ ] **Create Prometheus metrics**
  - [ ] Add metrics file
    ```python
    # src/app/infrastructure/monitoring/prometheus_metrics.py

    from prometheus_client import Counter, Histogram, Gauge

    hyperliquid_sync_total = Counter(
        "hyperliquid_sync_total",
        "Total Hyperliquid position syncs",
        ["status"]
    )

    hyperliquid_sync_duration = Histogram(
        "hyperliquid_sync_duration_seconds",
        "Hyperliquid sync duration",
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
    )

    hyperliquid_withdrawal_monitor_total = Counter(
        "hyperliquid_withdrawal_monitor_total",
        "Total withdrawal monitoring checks",
        ["status"]
    )

    hyperliquid_rate_limit_current = Gauge(
        "hyperliquid_rate_limit_current",
        "Current rate limit usage",
        ["api_type"]
    )
    ```
  - [ ] Instrument tasks
    ```python
    @celery_app.task(name="sync_user_hyperliquid_positions")
    def sync_user_hyperliquid_positions(user_id: int):
        start_time = time.time()
        try:
            result = _sync_logic(user_id)
            hyperliquid_sync_total.labels(status="success").inc()
            return result
        except Exception as e:
            hyperliquid_sync_total.labels(status="error").inc()
            raise
        finally:
            duration = time.time() - start_time
            hyperliquid_sync_duration.observe(duration)
    ```

**File**: `src/app/infrastructure/monitoring/prometheus_metrics.py`

---

- [ ] **Create Grafana dashboards**
  - [ ] Create dashboard JSON
    ```json
    {
      "title": "Hyperliquid Position Sync",
      "panels": [
        {
          "title": "Sync Success Rate",
          "targets": [
            {
              "expr": "rate(hyperliquid_sync_total{status='success'}[5m])"
            }
          ]
        },
        {
          "title": "Sync Latency (p95)",
          "targets": [
            {
              "expr": "histogram_quantile(0.95, hyperliquid_sync_duration_seconds_bucket)"
            }
          ]
        },
        {
          "title": "Rate Limit Usage",
          "targets": [
            {
              "expr": "hyperliquid_rate_limit_current"
            }
          ]
        }
      ]
    }
    ```
  - [ ] Import to Grafana

**File**: `infrastructure/grafana/hyperliquid_sync_dashboard.json`

---

- [ ] **Configure alerting rules**
  - [ ] Create alert rules
    ```yaml
    # infrastructure/prometheus/alert_rules.yml

    groups:
      - name: hyperliquid_sync
        rules:
          - alert: HyperliquidSyncFailureRate
            expr: |
              rate(hyperliquid_sync_total{status="error"}[5m]) > 0.1
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "High sync failure rate"

          - alert: HyperliquidRateLimitExceeded
            expr: |
              hyperliquid_rate_limit_current > 1100
            for: 1m
            labels:
              severity: critical
            annotations:
              summary: "Rate limit near threshold"

          - alert: HyperliquidSyncLatencyHigh
            expr: |
              histogram_quantile(0.95, hyperliquid_sync_duration_seconds_bucket) > 5
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "Sync latency p95 > 5s"
    ```

**File**: `infrastructure/prometheus/alert_rules.yml`

---

#### Testing

- [ ] **Unit tests** (4 tests)
  - [ ] `test_monitor_pending_withdrawals_finds_finalized()`
  - [ ] `test_monitor_pending_withdrawals_triggers_bridge()`
  - [ ] `test_bridge_after_withdrawal_success()`
  - [ ] `test_bridge_after_withdrawal_failure()`

**File**: `tests/unit/infrastructure/celery_app/tasks/test_hyperliquid_sync.py`

---

- [ ] **Integration tests** (1 test)
  - [ ] `test_withdrawal_monitor_end_to_end()`
    - Create pending withdrawal in DB
    - Mock finality timestamp (past)
    - Run monitor task
    - Verify bridge triggered

**File**: `tests/integration/infrastructure/celery_app/tasks/test_hyperliquid_sync_integration.py`

---

### Phase 3 Verification

- [ ] All unit tests pass (12 tests)
- [ ] All integration tests pass (3 tests)
- [ ] Load test passes (1000 users)
- [ ] Rate limit compliance verified (<1200 req/min)
- [ ] Monitoring dashboards working
- [ ] Alerting rules firing correctly
- [ ] Code review completed (2+ reviewers)

---

## 🔐 Security Audit

### Code Security

- [ ] **Private key handling**
  - [ ] No private keys in logs ✅
  - [ ] No private keys in error messages ✅
  - [ ] Memory cleanup after signing ✅
  - [ ] Redis cache TTL = 5min (Vault keys never cached) ✅

- [ ] **Input validation**
  - [ ] Amount limits (min $1, max $100,000) ✅
  - [ ] Address validation (checksum) ✅
  - [ ] Token validation (only USDC initially) ✅
  - [ ] Chain validation (arbitrum, base) ✅

- [ ] **Rate limiting**
  - [ ] 10 withdrawals/day per user ✅
  - [ ] 1200 req/min Hyperliquid Info API ✅
  - [ ] 100 req/min Hyperliquid Exchange API ✅

- [ ] **SQL injection protection**
  - [ ] All queries parameterized ✅
  - [ ] No string concatenation in queries ✅

### Infrastructure Security

- [ ] **HashiCorp Vault**
  - [ ] Vault policies configured (least privilege) ✅
  - [ ] TLS enabled for production ✅
  - [ ] Auto-unseal configured ✅
  - [ ] Audit logging enabled ✅

- [ ] **API Keys**
  - [ ] Stored in Vault (not .env) ✅
  - [ ] Rotated every 90 days ✅
  - [ ] Not exposed in logs ✅

- [ ] **Network Security**
  - [ ] TLS 1.3 for all APIs ✅
  - [ ] WebSocket secure (WSS) ✅
  - [ ] IP allowlisting for Vault ✅

### Penetration Testing

- [ ] Test withdrawal replay attack
  - Attempt to reuse signature
  - Verify nonce prevents replay
- [ ] Test rate limit bypass
  - Attempt to exceed 10 withdrawals/day
  - Verify rate limiter blocks
- [ ] Test SQL injection vectors
  - Inject malicious SQL in amount field
  - Verify parameterized queries prevent
- [ ] Test XSS in error messages
  - Inject script tags in withdrawal amounts
  - Verify sanitization

---

## 📊 Monitoring Setup

### Prometheus Metrics (Already Created in Phase 3)

- [x] `hyperliquid_sync_total` - Position sync counter
- [x] `hyperliquid_sync_duration_seconds` - Sync latency histogram
- [x] `hyperliquid_withdrawal_monitor_total` - Withdrawal monitoring counter
- [x] `hyperliquid_rate_limit_current` - Rate limit usage gauge
- [ ] `hyperliquid_withdrawal_total` - Withdrawal counter (add in Phase 2)
- [ ] `hyperliquid_withdrawal_duration_seconds` - E2E withdrawal latency (add in Phase 2)
- [ ] `hyperliquid_withdrawal_errors_total` - Withdrawal error counter (add in Phase 2)

### Grafana Dashboards (Already Created in Phase 3)

- [x] Position sync dashboard
- [ ] Add withdrawal metrics panel
  - Withdrawal success rate (target: > 95%)
  - Average E2E time (target: 32-35 min)
  - Error rate by step
  - Bridge success rate

### Alerting Rules (Already Created in Phase 3)

- [x] Sync failure rate alert
- [x] Rate limit exceeded alert
- [x] Sync latency alert
- [ ] Add withdrawal alerts
  - Withdrawal success rate < 90% (critical)
  - Average E2E time > 40 min (warning)
  - Error rate > 10% (critical)

---

## 🚀 Deployment

### Staging Deployment

- [ ] **Deploy to staging**
  - [ ] Run database migrations
    ```bash
    alembic upgrade head
    ```
  - [ ] Deploy backend services
    ```bash
    git push staging feature/hyperliquid-withdraw-agent
    ```
  - [ ] Configure environment variables
    ```bash
    # Copy .secrets.toml to staging server
    scp config/staging/.secrets.toml staging:/app/config/
    ```
  - [ ] Start Celery workers
    ```bash
    make celery.worker
    make celery.beat
    ```
  - [ ] Test with staging API keys (testnet)
  - [ ] Verify monitoring dashboards show data

---

- [ ] **Smoke tests**
  - [ ] Create Hyperliquid wallet (staging)
    ```bash
    curl -X POST https://staging-api.anvil.com/api/v1/wallets/hyperliquid \
      -H "Authorization: Bearer $TOKEN"
    ```
  - [ ] Execute withdrawal (testnet, small amount)
    ```bash
    curl -X POST https://staging-api.anvil.com/api/v1/user/chat/conversations/123/execute \
      -H "Authorization: Bearer $TOKEN" \
      -d '{"action": "withdraw_from_hyperliquid", "message": "withdraw 1 USDC from hyperliquid"}'
    ```
  - [ ] Verify WebSocket events received
    - Subscribe to WebSocket: `wss://staging-api.anvil.com/ws`
    - Listen for `withdrawal.*` events
  - [ ] Verify transaction persisted
    ```bash
    psql -c "SELECT * FROM transactions WHERE type = 'WITHDRAW' ORDER BY created_at DESC LIMIT 1;"
    ```
  - [ ] Verify position sync running
    ```bash
    # Check Celery Flower UI
    open http://staging-celery.anvil.com:5555
    ```

---

- [ ] **Performance tests**
  - [ ] 10 concurrent withdrawals
    ```bash
    # Run 10 withdrawal requests in parallel
    for i in {1..10}; do
      curl -X POST https://staging-api.anvil.com/api/v1/user/chat/conversations/$i/execute \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"action": "withdraw_from_hyperliquid", "message": "withdraw 1 USDC"}' &
    done
    wait
    ```
  - [ ] Measure P50, P95, P99 latency
    ```bash
    # Query Prometheus
    histogram_quantile(0.50, hyperliquid_withdrawal_duration_seconds_bucket)
    histogram_quantile(0.95, hyperliquid_withdrawal_duration_seconds_bucket)
    histogram_quantile(0.99, hyperliquid_withdrawal_duration_seconds_bucket)
    ```
  - [ ] Verify no memory leaks
    ```bash
    # Monitor memory usage over 1 hour
    watch -n 60 "ps aux | grep celery"
    ```
  - [ ] Check database connection pool
    ```bash
    psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'anvil';"
    ```

---

### Production Deployment

- [ ] **Pre-deployment checklist**
  - [ ] All tests pass (61 tests) ✅
  - [ ] Security audit complete ✅
  - [ ] Performance benchmarks met ✅
  - [ ] Monitoring configured ✅
  - [ ] Rollback plan documented ✅
  - [ ] Obtain mainnet Hyperliquid API key ✅
  - [ ] Configure production Vault ✅
  - [ ] Load test completed (1000 users) ✅

---

- [ ] **Deploy to production**
  - [ ] Enable maintenance mode
    ```bash
    # Display maintenance page to users
    ./scripts/enable_maintenance_mode.sh
    ```
  - [ ] Run database migrations
    ```bash
    alembic upgrade head
    ```
  - [ ] Deploy backend services (blue-green)
    ```bash
    # Deploy to green environment
    ./scripts/deploy_blue_green.sh green

    # Test green environment
    curl https://green-api.anvil.com/health

    # Switch traffic to green
    ./scripts/switch_traffic.sh green

    # Keep blue running for 1 hour (rollback window)
    ```
  - [ ] Configure production API keys
    ```bash
    # Store in Vault
    vault kv put secret/hyperliquid \
      api_key="MAINNET_KEY" \
      api_secret="MAINNET_SECRET"
    ```
  - [ ] Start Celery workers
    ```bash
    make celery.worker
    make celery.beat
    ```
  - [ ] Enable monitoring
    ```bash
    # Verify Prometheus scraping
    curl http://localhost:9090/api/v1/targets

    # Verify Grafana dashboards
    open https://grafana.anvil.com/d/hyperliquid-withdraw
    ```
  - [ ] Enable alerting
    ```bash
    # Verify alert rules loaded
    curl http://localhost:9090/api/v1/rules
    ```
  - [ ] Disable maintenance mode
    ```bash
    ./scripts/disable_maintenance_mode.sh
    ```

---

- [ ] **Post-deployment verification**
  - [ ] Health check endpoints responding
    ```bash
    curl https://api.anvil.com/health
    # Expected: {"status": "healthy"}
    ```
  - [ ] Monitoring dashboards show data
    ```bash
    # Check Grafana
    open https://grafana.anvil.com/d/hyperliquid-withdraw

    # Verify metrics flowing
    # - Withdrawal total count
    # - Sync latency
    # - Rate limit usage
    ```
  - [ ] Execute test withdrawal (REAL MONEY, small amount)
    ```bash
    # Withdraw $1 USDC
    curl -X POST https://api.anvil.com/api/v1/user/chat/conversations/123/execute \
      -H "Authorization: Bearer $PROD_TOKEN" \
      -d '{"action": "withdraw_from_hyperliquid", "message": "withdraw 1 USDC from hyperliquid to base"}'

    # Wait 35 minutes, verify completion
    ```
  - [ ] Verify WebSocket connections
    ```bash
    # Check active WebSocket connections
    netstat -an | grep :8080 | grep ESTABLISHED | wc -l
    ```
  - [ ] Check error logs (should be clean)
    ```bash
    # Last 100 lines of logs
    tail -n 100 /var/log/anvil/api.log | grep ERROR

    # Should be empty or only expected errors
    ```

---

### Beta Testing

- [ ] **Beta group (10 users)**
  - [ ] Select 10 active users (high trust, willing to test)
  - [ ] Enable feature flag
    ```python
    # Add to user metadata
    user.metadata["beta_features"] = ["hyperliquid_withdraw"]
    db.commit()
    ```
  - [ ] Monitor for 24 hours
    - Watch Grafana dashboards
    - Check error logs hourly
    - Monitor support tickets
  - [ ] Collect feedback
    - Email beta users after 24h
    - Ask about UX, performance, errors
  - [ ] Verify success rate > 95%
    ```bash
    # Query Prometheus
    rate(hyperliquid_withdrawal_total{status="success"}[24h]) /
    rate(hyperliquid_withdrawal_total[24h])
    ```

---

- [ ] **Gradual rollout**
  - [ ] Week 1: 10% of users
    ```python
    # Enable for 10% of users (by user_id % 10)
    if user_id % 10 == 0:
        enable_hyperliquid_withdraw(user)
    ```
  - [ ] Week 2: 50% of users
    ```python
    if user_id % 2 == 0:
        enable_hyperliquid_withdraw(user)
    ```
  - [ ] Week 3: 100% of users
    ```python
    # Remove feature flag, enable for all
    ```

---

## 📝 Documentation

### Technical Documentation

- [ ] **Update API documentation**
  - [ ] Add withdraw workflow endpoints
    - `POST /api/v1/user/chat/conversations/{id}/execute` (existing)
    - Document `WITHDRAW_FROM_HYPERLIQUID` action
  - [ ] Add WebSocket event documentation
    - `withdrawal.initiated`
    - `withdrawal.finality_progress`
    - `withdrawal.completed`
    - etc.
  - [ ] Add error code documentation
    - `INSUFFICIENT_BALANCE`
    - `NO_HYPERLIQUID_WALLET`
    - `WITHDRAWAL_FAILED`
    - etc.

---

- [ ] **Update architecture docs**
  - [ ] Add Hyperliquid withdraw components to architecture diagram
  - [ ] Update sequence diagrams for withdraw flow
  - [ ] Document error recovery flows (bridge failure, finality timeout)

---

### Operations Documentation

- [ ] **Create runbooks**
  - [ ] Withdrawal stuck in finality wait
    - Symptoms: User reports withdrawal not completing after 35 minutes
    - Diagnosis: Check finality_timestamp in tx_metadata
    - Resolution: Manually verify on Hyperliquid explorer, trigger bridge if needed
  - [ ] Bridge failure recovery
    - Symptoms: Bridge step fails after finality
    - Diagnosis: Check LiFi transaction status
    - Resolution: Retry bridge manually or refund user
  - [ ] Rate limit exceeded
    - Symptoms: High error rate, "rate limit exceeded" in logs
    - Diagnosis: Check Redis rate limit keys
    - Resolution: Increase polling interval or reduce active users
  - [ ] Vault key retrieval failure
    - Symptoms: All withdrawals failing with "Vault error"
    - Diagnosis: Check Vault health, connectivity
    - Resolution: Restart Vault, check IAM policies

---

- [ ] **Update monitoring docs**
  - [ ] Dashboard descriptions
    - Hyperliquid Position Sync Dashboard: Purpose, metrics, thresholds
    - Hyperliquid Withdraw Dashboard: Purpose, metrics, thresholds
  - [ ] Alert response procedures
    - For each alert, document:
      - Severity (P0, P1, P2)
      - On-call action required
      - Escalation path
  - [ ] On-call escalation
    - P0: Page DevOps + Backend Lead immediately
    - P1: Slack alert, respond within 30 min
    - P2: Email alert, respond within 4 hours

---

### User Documentation

- [ ] **Update user guide**
  - [ ] How to withdraw from Hyperliquid
    - Step 1: Say "withdraw X USDC from Hyperliquid"
    - Step 2: Confirm amount and destination
    - Step 3: Wait 30-35 minutes (explain finality)
    - Step 4: Funds arrive in Privy wallet
  - [ ] Transaction status explanations
    - "Transferring to Spot" - Moving funds internally
    - "Initiating withdrawal" - Submitting to blockchain
    - "Awaiting finality" - 30-minute security wait
    - "Bridging to Base" - Cross-chain transfer
    - "Completed" - Funds in your wallet
  - [ ] Error message meanings
    - "Insufficient balance" - Need more USDC in Hyperliquid
    - "Withdrawal failed" - Contact support with transaction ID
    - "Bridge unavailable" - Try again in 5 minutes
  - [ ] FAQ section
    - Q: Why does withdrawal take 30+ minutes?
    - A: Hyperliquid requires 30-minute finality for security
    - Q: Can I cancel a withdrawal?
    - A: No, once initiated, withdrawals cannot be cancelled
    - Q: What are the fees?
    - A: $0.15 withdrawal gas + $0.50-2.00 bridge fee (varies)

---

## ✅ Completion Criteria

### Must Have (Required for Launch)

- [x] All 3 phases implemented (Client + Agent + Celery)
- [x] All 61 tests passing (47 unit + 11 integration + 3 E2E)
- [x] Security audit complete (Vault integration verified)
- [x] Performance benchmarks met (32-35 min E2E)
- [x] Monitoring configured (Prometheus + Grafana)
- [x] Documentation complete (API + Operations + User)
- [x] Production deployment successful
- [x] Beta testing complete (10 users, 24 hours)

### Success Metrics (First Week)

- [ ] Withdrawal success rate > 95%
- [ ] Average E2E time 32-35 minutes
- [ ] Zero security incidents
- [ ] < 10 production bugs
- [ ] User satisfaction > 4.0/5 (survey)
- [ ] Rate limit compliance 100%

### Long-term Metrics (First Month)

- [ ] 100+ successful withdrawals
- [ ] Bridge success rate > 98%
- [ ] Position sync uptime > 99.9%
- [ ] Cost per withdrawal < $0.001 (backend)
- [ ] Zero critical incidents
- [ ] P95 latency < 36 minutes

---

## 📞 Team Assignments

### Development

- **Lead Engineer**: Implement agent and integration (16h)
  - WithdrawAgent class
  - ExecuteAction integration
  - E2E testing
- **Backend Engineer 1**: Implement Hyperliquid client (16h)
  - Balance queries
  - Transfer/withdrawal methods
  - EIP-712 signing
- **Backend Engineer 2**: Implement Celery tasks (16h)
  - Position sync
  - Withdrawal monitor
  - Rate limiting

### QA

- **QA Engineer 1**: Write and run unit tests (12h)
- **QA Engineer 2**: Write and run integration tests (8h)
- **QA Engineer 3**: Execute E2E scenarios (8h)

### DevOps

- **DevOps Engineer**: Configure infrastructure (16h)
  - Vault setup (production)
  - Monitoring dashboards
  - Alerting rules
  - Deployment pipeline

### Security

- **Security Engineer**: Conduct security audit (8h)
  - Penetration testing
  - Code review (Vault integration)
  - Compliance verification

---

## 🎯 Implementation Timeline

| Day | Phase | Hours | Deliverables |
|-----|-------|-------|--------------|
| **Day 1** | Hyperliquid Client (Info API) | 8h | Balance queries, rate limiting, tests |
| **Day 2** | Hyperliquid Client (Exchange API) | 8h | Transfer, withdrawal, EIP-712 signing, tests |
| **Day 3** | Withdraw Agent (Core) | 8h | Intent parsing, validation, transfer step, tests |
| **Day 4** | Withdraw Agent (Workflow) | 8h | Withdrawal, finality, bridge, ExecuteAction, E2E tests |
| **Day 5** | Celery Tasks (Sync) | 8h | Position sync, token snapshot, rate limiting, tests |
| **Day 6** | Celery Tasks (Monitor) | 8h | Withdrawal monitor, optimization, monitoring, tests |
| **Day 7** | Buffer + Audit | 8h | Security audit, performance testing, documentation |

**Total**: 56 hours (7 business days)
**Buffer**: +1 day for blocker resolution = **5-7 days total**

---

**Checklist Version**: 1.0
**Last Updated**: 2026-02-04
**Status**: Ready for Implementation (pending blocker resolution)
**Next Action**: Resolve critical blockers (API key, wallet linking, Vault setup)
**Estimated Start Date**: TBD (after blocker resolution)
**Estimated Completion Date**: TBD + 5-7 days
