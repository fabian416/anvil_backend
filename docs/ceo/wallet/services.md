# Wallets & Transactions - Services Documentation

**Last Updated**: 2026-01-26
**Module**: Wallets & Transactions
**Architecture**: Hexagonal (Clean Architecture)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Domain Services](#domain-services)
3. [Application Services](#application-services)
   - [Command Handlers](#command-handlers)
   - [Query Services](#query-services)
   - [Infrastructure Handlers](#infrastructure-handlers)
4. [Infrastructure Services](#infrastructure-services)
   - [Repositories](#repositories)
   - [Gateways](#gateways)
   - [External Integrations](#external-integrations)
5. [Service Dependencies](#service-dependencies)
6. [Service Patterns](#service-patterns)

---

## Architecture Overview

The Wallets & Transactions module follows **Hexagonal Architecture** principles with strict layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (HTTP Controllers, Schemas, Middleware)                     │
│  - wallet/router.py, transaction/router.py                  │
│  - admin/wallet/*, admin/transactions_router.py             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Commands, Queries, Interactors)                           │
│  - commands/wallet/: SaveSwapTransaction, ExportWallet      │
│  - queries/wallet/: GetPrivyWalletDetails, ListWallets      │
│  - handlers/: GetMyWalletsHandler, LogTransactionHandler    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  (Entities, Value Objects, Domain Services, Ports)          │
│  - entities/: Wallet, Transaction                           │
│  - ports/: WalletRepository, TransactionRepository          │
│  - services/: (Pure business logic)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  (Adapters, Database, External APIs)                        │
│  - adapters/: SqlaWalletRepository, SqlaTransactionRepo     │
│  - privy/: PrivyClient, HPKEDecryptor                       │
│  - persistence_sqla/mappings/: wallet.py, transaction.py    │
└─────────────────────────────────────────────────────────────┘
```

**Key Principles**:
- **Dependency Inversion**: Outer layers depend on inner layers via ports (interfaces)
- **Domain Independence**: Domain layer has no dependencies on frameworks
- **Port-Adapter Pattern**: External dependencies accessed via ports + adapters
- **CQRS**: Commands (writes) separated from Queries (reads)

---

## Domain Services

Domain services contain **pure business logic** with no infrastructure dependencies.

### Currently No Pure Domain Services

The wallet and transaction logic is primarily **data-oriented** rather than **business-logic-heavy**:
- Wallet operations are CRUD + Privy API interactions
- Transaction operations are CRUD + blockchain status tracking

**Future Candidates for Domain Services**:
- **WalletPolicyService**: Complex policy evaluation for multi-sig wallets
- **TransactionValidationService**: Business rules for transaction limits, compliance
- **PortfolioCalculationService**: Wallet balance aggregation, PnL calculations

**Example Domain Service Pattern** (if needed):
```python
# src/app/domain/services/wallet_policy.py

class WalletPolicyService:
    """
    Domain service for evaluating wallet access policies.

    Pure business logic - no infrastructure dependencies.
    """

    def can_execute_transaction(
        self,
        wallet: Wallet,
        transaction_amount: Decimal,
        user_role: UserRole
    ) -> tuple[bool, str | None]:
        """
        Check if a transaction can be executed based on wallet policies.

        Returns:
            (can_execute, reason_if_not)
        """
        # Business Rule 1: Check wallet status
        if wallet.status != WalletStatus.ACTIVE:
            return False, "Wallet is not active"

        # Business Rule 2: Check amount limits based on policies
        for policy_id in wallet.policy_ids:
            policy = self._get_policy(policy_id)  # Would be injected
            if transaction_amount > policy.max_amount:
                return False, f"Exceeds policy limit: {policy.max_amount}"

        # Business Rule 3: Check additional signers requirement
        if wallet.additional_signers and user_role != UserRole.ADMIN:
            return False, "Additional signer approval required"

        return True, None
```

---

## Application Services

### Command Handlers

Command handlers implement **write operations** and **business-critical reads** following CQRS pattern.

---

#### SaveSwapTransactionHandler

**Purpose**: Persist completed swap transactions to database after successful on-chain execution.

**Location**: `/src/app/application/commands/wallet/save_swap_transaction.py` (lines 51-177)

**Responsibilities**:
- Validate swap transaction data (amounts, chain, tokens)
- Create `Transaction` domain entity with type=SWAP
- Persist to database via `TransactionRepository`
- Generate transaction metadata (conversation context, exchange rate)

**Dependencies**:
- `TransactionRepository` (port): Database persistence

**Dependents**:
- `POST /api/v1/wallet/swaps/complete` controller

**Key Methods**:

```python
class SaveSwapTransactionHandler:
    def __init__(self, transaction_repository: TransactionRepository):
        self._transaction_repository = transaction_repository

    async def handle(
        self, command: SaveSwapTransactionCommand
    ) -> SaveSwapTransactionResult:
        """
        Handle save swap transaction command.

        Args:
            command: SaveSwapTransactionCommand with swap details

        Returns:
            SaveSwapTransactionResult with transaction ID

        Raises:
            ValueError: If amounts are invalid or chain unknown
        """
```

**Business Logic Flow**:

1. **Amount Validation**:
```python
# Line 88-95: Validate amounts are positive decimals
from_amount_decimal = Decimal(command.from_amount)
to_amount_decimal = Decimal(command.to_amount)

if from_amount_decimal <= 0 or to_amount_decimal <= 0:
    raise ValueError("Amounts must be positive")
```

2. **Chain Mapping**:
```python
# Line 98-109: Map chain name to ChainType enum
try:
    chain = ChainType[command.chain.upper()]
except KeyError:
    chain_mapping = {
        "ethereum": ChainType.ETHEREUM,
        "base": ChainType.BASE,
        "polygon": ChainType.POLYGON,
        "arbitrum": ChainType.ARBITRUM,
        "optimism": ChainType.OPTIMISM,
    }
    chain = chain_mapping.get(command.chain.lower(), ChainType.BASE)
```

3. **Metadata Construction**:
```python
# Line 112-118: Build transaction metadata
metadata = {
    "conversation_id": command.conversation_id,
}

if command.exchange_rate:
    metadata["exchange_rate"] = command.exchange_rate
```

4. **Entity Creation**:
```python
# Line 136-162: Create Transaction entity
transaction = Transaction(
    id_=TransactionId(0),  # Auto-generated by DB
    user_id=UserId(command.user_id),
    wallet_id=WalletId(0),  # Resolved by repository
    to_address=None,  # Not applicable for swaps
    type=TransactionType.SWAP,
    chain=chain,
    asset_in=command.from_token,
    amount_in=from_amount_decimal,
    asset_out=command.to_token,
    amount_out=to_amount_decimal,
    fee_usd=Decimal(command.gas_fee_usd) if command.gas_fee_usd else None,
    tx_hash=command.tx_hash,
    status=TransactionStatus.SUCCESS,  # Already completed on-chain
    dex_aggregator="0x",  # Using 0x Protocol
    slippage=Decimal(command.slippage) if command.slippage else None,
    tx_metadata=metadata,
    created_at=CreatedAt.now()
)
```

5. **Persistence**:
```python
# Line 165: Save to database
saved_transaction = await self._transaction_repository.save(transaction)
```

**Integration Points**:
- **Input**: Frontend POST request after Privy + 0x swap execution
- **Output**: Database transaction record for history/analytics

---

#### ExportWallet

**Purpose**: Export embedded wallet private key via Privy API using HPKE encryption.

**Location**: `/src/app/application/commands/wallet/export_wallet.py` (lines 41-140)

**Responsibilities**:
- Generate HPKE key pair for secure transfer
- Call Privy API to export wallet (encrypted)
- Decrypt private key using HPKE
- Return decrypted private key to user

**Dependencies**:
- `PrivyClient` (infrastructure): Privy API integration
- `HPKEDecryptor` (infrastructure): Encryption/decryption

**Dependents**:
- `POST /api/v1/wallet/export` controller

**Security Critical**: Private keys are NEVER logged or persisted.

**Key Methods**:

```python
class ExportWallet:
    __slots__ = ("_privy_client",)

    def __init__(self, privy_client: PrivyClient) -> None:
        self._privy_client = privy_client

    async def execute(
        self,
        wallet_id: str,
        wallet_address: str | None = None,
    ) -> ExportWalletResult:
        """
        Export wallet private key.

        Args:
            wallet_id: Privy wallet ID
            wallet_address: Optional address for verification

        Returns:
            ExportWalletResult with decrypted private key

        Raises:
            WalletNotFoundError: Wallet doesn't exist
            WalletExportError: Export failed
        """
```

**HPKE Encryption Flow**:

1. **Generate Key Pair**:
```python
# Line 84-86: Generate ephemeral HPKE key pair
decryptor = HPKEDecryptor()
key_pair = decryptor.get_or_create_key_pair()
```

2. **Fetch Wallet Info** (verification):
```python
# Line 90-98: Get wallet info from Privy
wallet_info = await self._privy_client.get_wallet(wallet_id)
actual_address = wallet_info.get("address", "")

# Verify address if provided
if wallet_address and actual_address.lower() != wallet_address.lower():
    raise WalletExportError(f"Address mismatch")
```

3. **Call Privy Export API**:
```python
# Line 101-105: Export wallet (encrypted with public key)
export_response = await self._privy_client.export_wallet(
    wallet_id=wallet_id,
    recipient_public_key_b64=key_pair.public_key_b64,
)
```

4. **Decrypt Private Key**:
```python
# Line 110-114: Decrypt using HPKE (NEVER logged)
private_key = decryptor.decrypt(
    ciphertext_b64=export_response.ciphertext,
    encapsulated_key_b64=export_response.encapsulated_key,
)
```

5. **Return Result**:
```python
# Line 122-127: Return decrypted private key
return ExportWalletResult(
    wallet_id=wallet_id,
    address=actual_address,
    private_key=private_key,  # SENSITIVE - handle with care
    chain_type=chain_type,
)
```

**Security Considerations**:
- HPKE ensures end-to-end encryption during transfer
- Private key only exists in memory, never persisted
- Audit trail records export timestamp
- Only wallet owner can export (verified in controller)

---

#### UpdatePrivyWallet

**Purpose**: Update wallet configuration in Privy (policy IDs, owner, additional signers).

**Location**: `/src/app/application/commands/wallet/update_privy_wallet.py`

**Responsibilities**:
- Validate update request (admin-only)
- Send update request to Privy API
- Fetch updated wallet configuration
- Sync changes to local database
- Record last sync timestamp

**Dependencies**:
- `PrivyClient` (infrastructure): Privy API integration
- `WalletRepository` (port): Local database sync
- `GetPrivyWalletDetails` (query): Fetch updated details

**Dependents**:
- `PATCH /api/v1/admin/wallets/{privy_wallet_id}` controller

**Key Methods**:

```python
class UpdatePrivyWallet:
    async def execute(
        self, request: UpdatePrivyWalletRequest
    ) -> UpdatePrivyWalletResult:
        """
        Update wallet configuration in Privy.

        Args:
            request: UpdatePrivyWalletRequest with changes

        Returns:
            UpdatePrivyWalletResult with success flag and updated details

        Raises:
            WalletNotFoundError: Wallet doesn't exist
            WalletUpdateError: Privy API error
        """
```

**Update Flow**:

1. **Validate Admin Access**:
```python
# Authorization check in controller
current_user = await current_user_service.get_current_user()
authorize(CanManageRole(), ...)
```

2. **Call Privy API**:
```python
# Update wallet configuration
await self._privy_client.update_wallet(
    wallet_id=request.privy_wallet_id,
    policy_ids=request.policy_ids,
    owner=request.owner,
    additional_signers=request.additional_signers
)
```

3. **Fetch Updated Details**:
```python
# Get updated wallet details from Privy
wallet_details = await self._get_wallet_details_query.execute(
    GetPrivyWalletDetailsRequest(privy_wallet_id=request.privy_wallet_id)
)
```

4. **Sync to Local DB**:
```python
# Update local database with new configuration
local_wallet = await self._wallet_repository.get_by_privy_wallet_id(
    request.privy_wallet_id
)

if local_wallet:
    local_wallet.policy_ids = wallet_details.policy_ids
    local_wallet.owner_type = wallet_details.owner_type
    local_wallet.owner_id = wallet_details.owner_id
    local_wallet.additional_signers = [...]
    local_wallet.last_privy_sync_at = datetime.now(UTC)

    await self._wallet_repository.update(local_wallet)
```

5. **Return Result**:
```python
return UpdatePrivyWalletResult(
    success=True,
    wallet_details=wallet_details,
    changes_applied={
        "policy_ids": request.policy_ids,
        "owner_id": request.owner_id,
        ...
    }
)
```

---

### Query Services

Query services implement **optimized read operations** with dedicated query models (CQRS).

---

#### ListWalletsQueryService

**Purpose**: List all wallets with pagination, sorting, and search (admin-only).

**Location**: `/src/app/application/queries/list_wallets.py` (lines 49-124)

**Responsibilities**:
- Authorize admin access
- Build query parameters (pagination, sorting, search)
- Execute query via `WalletQueryGateway`
- Return paginated wallet list with total count

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `WalletQueryGateway` (port): Database read access

**Dependents**:
- `GET /api/v1/admin/wallets` controller

**Key Methods**:

```python
class ListWalletsQueryService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_query_gateway: WalletQueryGateway,
    ):
        self._current_user_service = current_user_service
        self._wallet_query_gateway = wallet_query_gateway

    async def execute(
        self, request_data: ListWalletsRequest
    ) -> ListWalletsResponse:
        """
        Execute list wallets query.

        Args:
            request_data: ListWalletsRequest with pagination/sorting/search

        Returns:
            ListWalletsResponse with wallets and total count

        Raises:
            AuthenticationError: User not authenticated
            AuthorizationError: User not admin
            SortingError: Invalid sorting field
        """
```

**Query Flow**:

1. **Authorization**:
```python
# Line 80-89: Verify admin access
current_user = await self._current_user_service.get_current_user()

authorize(
    CanManageRole(),
    context=RoleManagementContext(
        subject=current_user,
        target_role=UserRole.USER,
    ),
)
```

2. **Build Query Parameters**:
```python
# Line 98-108: Construct query params
wallet_list_params = WalletListParams(
    pagination=Pagination(
        limit=request_data.limit,
        offset=request_data.offset,
    ),
    sorting=WalletListSorting(
        sorting_field=request_data.sorting_field,
        sorting_order=request_data.sorting_order,
    ),
    search=request_data.search,
)
```

3. **Execute Query**:
```python
# Line 110-116: Query via gateway
wallets = await self._wallet_query_gateway.read_all(wallet_list_params)

if wallets is None:
    raise SortingError("Invalid sorting field.")

total = await self._wallet_query_gateway.count_all(search=request_data.search)
```

4. **Return Response**:
```python
# Line 121-122: Build response
return ListWalletsResponse(wallets=wallets, total=total)
```

**Search Functionality**:
- Searches across: address, user email, user name, privy_wallet_id
- Case-insensitive partial matching
- Implemented in `WalletReaderSqla` adapter

---

#### GetPrivyWalletDetails

**Purpose**: Retrieve detailed wallet information combining local DB and live Privy API data.

**Location**: `/src/app/application/queries/wallet/get_privy_wallet_details.py` (lines 97-265)

**Responsibilities**:
- Authorize admin access
- Fetch local wallet data from database
- Fetch live wallet data from Privy API
- Merge data and update local cache
- Return combined admin-facing DTO

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `WalletRepository` (port): Local database access
- `PrivyClient` (infrastructure): Privy API access

**Dependents**:
- `GET /api/v1/admin/wallets/{privy_wallet_id}` controller
- `UpdatePrivyWallet` command (for fetching updated details)

**Key Methods**:

```python
class GetPrivyWalletDetails:
    __slots__ = (
        "_current_user_service",
        "_privy_client",
        "_wallet_repository",
    )

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_repository: WalletRepository,
        privy_client: PrivyClient,
    ) -> None:
        ...

    async def execute(
        self, request: GetPrivyWalletDetailsRequest
    ) -> AdminWalletDetailsDTO:
        """
        Get detailed wallet info for admin management.

        Args:
            request: GetPrivyWalletDetailsRequest with privy_wallet_id

        Returns:
            AdminWalletDetailsDTO with combined data

        Raises:
            AuthorizationError: User not admin
            WalletNotFoundError: Wallet doesn't exist
            WalletQueryError: Error fetching data
        """
```

**Data Merging Flow**:

1. **Authorization**:
```python
# Line 146-153: Verify admin access
current_user = await self._current_user_service.get_current_user()

authorize(
    CanManageRole(),
    context=RoleManagementContext(
        subject=current_user,
        target_role=UserRole.USER,
    ),
)
```

2. **Fetch Local Data**:
```python
# Line 156-159: Get from local DB
local_wallet = await self._wallet_repository.get_by_privy_wallet_id(
    request.privy_wallet_id
)
```

3. **Fetch Privy Data**:
```python
# Line 162-174: Get from Privy API
try:
    privy_wallet = await self._privy_client.get_wallet(
        request.privy_wallet_id
    )
except PrivyWalletNotFoundError:
    if local_wallet is None:
        raise WalletNotFoundError(...)
    # Wallet exists locally but not in Privy
    privy_wallet = None
```

4. **Merge Data**:
```python
# Line 177-229: Build DTO with merged data
metadata = privy_wallet.metadata if privy_wallet else {}

dto = AdminWalletDetailsDTO(
    # Prefer Privy data for current state
    address=privy_wallet.address if privy_wallet else local_wallet.address,
    chain_type=privy_wallet.chain_type.value if privy_wallet else local_wallet.default_chain.value,

    # Prefer Privy for configuration
    policy_ids=metadata.get("policy_ids", []) or (local_wallet.policy_ids if local_wallet else []),
    owner_type=metadata.get("owner_type") or (local_wallet.owner_type if local_wallet else None),

    # Local data for user association
    local_wallet_id=local_wallet.id_.value if local_wallet else None,
    user_id=local_wallet.user_id.value if local_wallet else None,

    # Timestamps
    created_at=privy_wallet.created_at if privy_wallet else local_wallet.created_at.value,
    last_privy_sync_at=datetime.now(UTC),

    # Raw data for debugging
    privy_raw_data=metadata.get("raw", {})
)
```

5. **Update Local Cache**:
```python
# Line 232-249: Sync Privy data to local DB
if local_wallet and privy_wallet:
    local_wallet.policy_ids = metadata.get("policy_ids", [])
    local_wallet.owner_type = metadata.get("owner_type")
    local_wallet.owner_id = metadata.get("owner_id")
    local_wallet.additional_signers = [...]
    local_wallet.last_privy_sync_at = datetime.now(UTC)

    await self._wallet_repository.update(local_wallet)
```

**Graceful Degradation**:
- If Privy API fails but wallet exists locally → returns local data
- If wallet doesn't exist in Privy or DB → raises WalletNotFoundError

---

### Infrastructure Handlers

Infrastructure handlers bridge authentication and application logic (special case in this architecture).

---

#### GetMyWalletsHandler

**Purpose**: Get all wallets for authenticated user from local DB and Privy API.

**Location**: `/src/app/infrastructure/auth/handlers/wallet_me.py` (lines 83-326)

**Responsibilities**:
- Get current authenticated user
- Fetch wallets from Privy API (if not offline mode)
- Fetch imported wallets from local DB
- Fetch cached Privy wallets from local DB (offline capability)
- Deduplicate wallets by address
- Return unified wallet list

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `EmbeddedWalletProviderPort` (port): Privy API access
- `WalletRepository` (port): Local database access
- `PrivySettings` (config): Wallet source mode configuration

**Dependents**:
- `GET /api/v1/wallet/me` controller

**Wallet Source Modes**:

1. **PRIVY Mode**:
   - Prefer Privy API for live data
   - Use local DB as cache/analytics store
   - Don't persist Privy wallets to DB

2. **HYBRID Mode** (recommended):
   - Use Privy when available
   - Always persist to local DB
   - Offline capability when Privy unavailable

3. **LOCAL Mode**:
   - No Privy calls
   - DB-only mode for offline environments

**Key Methods**:

```python
class GetMyWalletsHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_provider: EmbeddedWalletProviderPort,
        wallet_repository: WalletRepository,
        privy_settings: PrivySettings,
    ):
        self._current_user_service = current_user_service
        self._wallet_provider = wallet_provider
        self._wallet_repository = wallet_repository
        self._source_mode = privy_settings.wallets_source_mode

    @property
    def is_offline_mode(self) -> bool:
        return self._source_mode == WalletSourceMode.LOCAL

    @property
    def should_call_privy(self) -> bool:
        return self._source_mode in (WalletSourceMode.PRIVY, WalletSourceMode.HYBRID)

    @property
    def should_persist_to_db(self) -> bool:
        return self._source_mode in (WalletSourceMode.HYBRID, WalletSourceMode.LOCAL)

    async def execute(self) -> WalletsResponse:
        """Get all wallets for current user."""
```

**Aggregation Flow**:

1. **Get Current User**:
```python
# Line 138-150: Get user and primary wallet
user = await self._current_user_service.get_current_user()

primary_address = user.primary_wallet_address.value if user.primary_wallet_address else None
privy_user_id = user.privy_user_id.value if user.privy_user_id else None
user_id = UserId(user.id_.value)
```

2. **Fetch from Privy** (if not offline):
```python
# Line 153-202: Fetch from Privy API
if privy_user_id and self.should_call_privy:
    try:
        privy_wallets = await self._wallet_provider.list_user_wallets(privy_user_id)
        privy_connected = True

        for pw in privy_wallets:
            wallets.append(WalletResponse(..., source="privy"))
            seen_addresses.add(pw.address.lower())

            # In hybrid mode, persist to local DB
            if self.should_persist_to_db:
                await self._wallet_repository.upsert(
                    user_id=user_id,
                    address=pw.address,
                    provider=WalletProvider.PRIVY,
                    privy_wallet_id=pw.wallet_id,
                    chain_type=pw.chain_type.value
                )

    except WalletProviderError as e:
        message = f"Could not fetch wallets from Privy: {e}"
```

3. **Fetch Imported Wallets from DB**:
```python
# Line 211-244: Fetch imported wallets
local_imported_wallets = await self._wallet_repository.get_by_user_and_provider(
    user_id=user_id,
    provider=WalletProvider.IMPORTED,
)

for lw in local_imported_wallets:
    if lw.address.lower() not in seen_addresses:
        wallets.append(WalletResponse(..., source="local"))
        seen_addresses.add(lw.address.lower())
```

4. **Fetch Cached Privy Wallets** (offline mode):
```python
# Line 257-296: Fetch cached Privy wallets from DB
if self.is_offline_mode or (self.should_persist_to_db and not privy_connected):
    local_privy_wallets = await self._wallet_repository.get_by_user_and_provider(
        user_id=user_id,
        provider=WalletProvider.PRIVY,
    )

    for lw in local_privy_wallets:
        if lw.address.lower() not in seen_addresses:
            wallets.append(WalletResponse(..., source="local"))
            seen_addresses.add(lw.address.lower())
```

5. **Add Primary Wallet** (if missing):
```python
# Line 299-314: Add primary wallet if not in any list
if primary_address:
    primary_lower = primary_address.lower()
    if primary_lower not in seen_addresses:
        wallets.append(WalletResponse(
            wallet_id=f"local_{user.id_.value}",
            address=primary_address,
            chain_type="ethereum",
            wallet_type="external",
            is_primary=True,
            source="local",
            created_at=None
        ))
```

6. **Sort and Return**:
```python
# Line 317: Ensure primary wallet is first
wallets.sort(key=lambda w: (not w.is_primary, w.address))

return WalletsResponse(...)
```

**Deduplication Logic**:
- Uses `seen_addresses` set to track wallet addresses
- Case-insensitive comparison (all addresses lowercased)
- Skips duplicates from subsequent sources

---

#### SyncWalletsHandler

**Purpose**: Sync wallets from frontend (Privy SDK) to backend database.

**Location**: `/src/app/infrastructure/auth/handlers/wallet_me.py` (lines 329-458)

**Responsibilities**:
- Get current authenticated user
- Parse wallet data from frontend (legacy + new format)
- Persist imported wallets to local database
- Return synced wallet list

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `WalletRepository` (port): Database persistence

**Dependents**:
- `POST /api/v1/wallet/sync` controller

**Key Methods**:

```python
class SyncWalletsHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._wallet_repository = wallet_repository

    async def execute(
        self, wallet_data: list[dict[str, str | None]]
    ) -> WalletsResponse:
        """
        Sync wallets from frontend.

        Args:
            wallet_data: List of wallet dicts with keys:
                - address (required)
                - chain_type (optional, default: ethereum)
                - wallet_type (optional, default: unknown)
                - privy_wallet_id (optional)

        Returns:
            WalletsResponse with synced wallets
        """
```

**Sync Flow**:

1. **Get Current User**:
```python
# Line 371-378: Get user and prepare tracking
user = await self._current_user_service.get_current_user()
user_id = UserId(user.id_.value)

wallets: list[WalletResponse] = []
primary_address = user.primary_wallet_address.value if user.primary_wallet_address else None
imported_count = 0
persisted_count = 0
```

2. **Process Each Wallet**:
```python
# Line 382-437: Process wallet data
for i, wallet_info in enumerate(wallet_data):
    address = wallet_info.get("address", "")
    if not address:
        continue

    chain_type_str = wallet_info.get("chain_type", "ethereum") or "ethereum"
    wallet_type = wallet_info.get("wallet_type", "unknown") or "unknown"
    privy_wallet_id = wallet_info.get("privy_wallet_id")

    is_primary = (
        primary_address and address.lower() == primary_address.lower()
    ) or (primary_address is None and i == 0)

    # Persist imported wallets to database
    if wallet_type == "imported":
        imported_count += 1
        try:
            await self._wallet_repository.upsert(
                user_id=user_id,
                address=address,
                provider=WalletProvider.IMPORTED,
                privy_wallet_id=privy_wallet_id,
                chain_type=chain_type_str
            )
            persisted_count += 1
        except DataMapperError as e:
            logger.error(f"Failed to persist imported wallet: {e}")

    # Generate wallet_id
    wallet_id = privy_wallet_id
    if not wallet_id:
        if wallet_type == "imported":
            wallet_id = f"imported:{address.lower()}"
        else:
            wallet_id = f"synced_{i}"

    wallets.append(WalletResponse(..., source="frontend"))
```

3. **Build Message**:
```python
# Line 440-449: Build response message
message = "Wallets synced from frontend"
if imported_count > 0:
    message = (
        f"Wallets synced from frontend "
        f"({imported_count} imported, {persisted_count} persisted)"
    )

    logger.info(
        f"User {user.id_.value} synced {len(wallets)} wallets "
        f"({imported_count} imported, {persisted_count} persisted to DB)"
    )
```

4. **Return Response**:
```python
# Line 451-458: Build response
return WalletsResponse(
    user_id=user.id_.value,
    privy_user_id=user.privy_user_id.value if user.privy_user_id else None,
    wallets=wallets,
    primary_wallet_address=primary_address,
    privy_connected=False,  # Not fetching from Privy in sync
    message=message
)
```

**Wallet Type Handling**:
- **Imported Wallets**: Persisted to database with `provider=IMPORTED`
- **Embedded Wallets**: Not persisted (will be synced from Privy on next /me call)
- **External Wallets**: Not persisted (ephemeral browser connections)

---

#### LogTransactionHandler

**Purpose**: Log transactions sent from frontend via Privy for history and auditing.

**Location**: `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 104-391)

**Responsibilities**:
- Get current authenticated user
- Check for duplicate transactions
- Find wallet by address and user
- Create Transaction entity for sender
- Save sender's transaction to database
- Create Transaction entity for receiver (if registered user)
- Save receiver's transaction to database

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `TransactionRepository` (port): Database persistence
- `WalletRepository` (port): Wallet lookup

**Dependents**:
- `POST /api/v1/user/transactions` controller

**Dual Transaction Logging**:

The handler creates **two transaction records** for each on-chain transaction:
1. **Sender's Record**: User who sent the transaction
2. **Receiver's Record**: User who received the transaction (if registered)

This allows the same transaction to appear in both users' history.

**Key Methods**:

```python
class LogTransactionHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_repository: TransactionRepository,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._transaction_repository = transaction_repository
        self._wallet_repository = wallet_repository

    async def execute(
        self, input_data: LogTransactionInput
    ) -> LogTransactionResult:
        """
        Log transaction to database.

        Creates transaction record for sender.
        Also creates record for receiver if they're a registered user.

        Args:
            input_data: LogTransactionInput with transaction details

        Returns:
            LogTransactionResult with created transaction info

        Raises:
            WalletNotFoundForTransactionError: Sender wallet not found
            TransactionLogError: Logging failed
        """
```

**Logging Flow**:

1. **Get Current User**:
```python
# Line 142-143: Get authenticated user
user = await self._current_user_service.get_current_user()
user_id = UserId(user.id_.value)
```

2. **Check for Duplicates**:
```python
# Line 150-170: Check if transaction already logged for this user
existing = await self._transaction_repository.get_by_user_and_tx_hash(
    user_id=user_id,
    tx_hash=input_data.tx_hash
)

if existing:
    logger.info("Transaction already exists, returning existing record")
    return LogTransactionResult(
        id=existing.id_.value,
        tx_hash=existing.tx_hash,
        status=existing.status.name.lower(),
        chain=existing.chain.value,
        tx_type=existing.type.name.lower(),
        from_address=input_data.from_address,
        to_address=input_data.to_address,
        created_at=existing.created_at.value.isoformat()
    )
```

3. **Find Wallet**:
```python
# Line 173-194: Find wallet by address and user
wallet = await self._wallet_repository.get_by_user_and_address(
    user_id=user_id,
    address=input_data.from_address
)

# Fallback: try address-only lookup
if not wallet:
    wallet = await self._wallet_repository.get_by_address(input_data.from_address)

if not wallet:
    raise WalletNotFoundForTransactionError(
        f"Wallet {input_data.from_address[:10]}... not found. "
        f"Please sync your wallets first."
    )
```

4. **Map Chain and Type**:
```python
# Line 196-200: Map chain ID to ChainType
chain = CHAIN_ID_MAP.get(input_data.chain_id, ChainType.ETHEREUM)

# Map transaction type
tx_type = TX_TYPE_MAP.get(input_data.tx_type.lower(), TransactionType.SEND)
```

5. **Convert Wei to ETH**:
```python
# Line 203-213: Convert value from Wei to ETH
if input_data.value:
    wei_value = Decimal(input_data.value)
    # 1 ETH = 10^18 Wei
    amount_in = wei_value / Decimal("1000000000000000000")
else:
    amount_in = None
```

6. **Create Sender's Transaction**:
```python
# Line 219-244: Create transaction entity for sender
transaction = Transaction(
    id_=TransactionId(0),
    user_id=user_id,
    wallet_id=wallet.id_,
    to_address=input_data.to_address.lower() if input_data.to_address else None,
    type=tx_type,
    chain=chain,
    asset_in=input_data.asset_symbol or "ETH",
    amount_in=amount_in,
    tx_hash=input_data.tx_hash.lower(),
    status=TransactionStatus.PENDING,
    created_at=CreatedAt(datetime.now(UTC))
)
```

7. **Save Sender's Transaction**:
```python
# Line 248-253: Save to database
saved_tx = await self._transaction_repository.save(transaction)

logger.info(
    f"Transaction logged for sender: id={saved_tx.id_.value}, "
    f"hash={input_data.tx_hash[:16]}..."
)
```

8. **Log Receiver's Transaction**:
```python
# Line 256-264: Also log for receiver
await self._log_receiver_transaction(
    input_data=input_data,
    sender_user_id=user_id,
    to_address=to_address,
    chain=chain,
    tx_type=tx_type,
    amount_in=amount_in
)
```

**Receiver Transaction Logic** (lines 281-391):

```python
async def _log_receiver_transaction(
    self, *, input_data, sender_user_id, to_address, chain, tx_type, amount_in
):
    if not to_address:
        return  # Skip if no recipient

    # Look up receiver's wallet
    receiver_wallet = await self._wallet_repository.get_by_address(to_address)

    if not receiver_wallet:
        return  # Receiver not registered

    receiver_user_id = receiver_wallet.user_id

    # Don't create duplicate if sender == receiver
    if receiver_user_id.value == sender_user_id.value:
        return

    # Check if receiver already has this transaction
    existing_receiver_tx = await self._transaction_repository.get_by_user_and_tx_hash(
        user_id=receiver_user_id,
        tx_hash=input_data.tx_hash
    )
    if existing_receiver_tx:
        return

    # Create receiver's transaction
    receiver_tx = Transaction(
        id_=TransactionId(0),
        user_id=receiver_user_id,
        wallet_id=receiver_wallet.id_,
        to_address=to_address,
        type=tx_type,
        chain=chain,
        asset_in=input_data.asset_symbol or "ETH",
        amount_in=amount_in,
        tx_hash=input_data.tx_hash.lower(),
        status=TransactionStatus.PENDING,
        tx_metadata={
            "receiver_view": True,
            "from_address": input_data.from_address.lower()
        },
        created_at=CreatedAt(datetime.now(UTC))
    )

    await self._transaction_repository.save(receiver_tx)

    logger.info(
        f"Transaction logged for receiver: id={saved_receiver_tx.id_.value}, "
        f"user={receiver_user_id.value}"
    )
```

**Metadata Distinction**:
- **Sender's Transaction**: No special metadata
- **Receiver's Transaction**: `{"receiver_view": True, "from_address": "0x..."}`

This metadata allows the frontend to display "Received from 0x..." vs "Sent to 0x...".

---

#### GetTransactionHistoryHandler

**Purpose**: Get transaction history for authenticated user with filtering.

**Location**: `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 454-575)

**Responsibilities**:
- Get current authenticated user
- Parse filter parameters (chain, status, tx_type)
- Execute query via `TransactionRepository`
- Convert to response format with explorer URLs
- Return paginated transaction history

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `TransactionRepository` (port): Database queries

**Dependents**:
- `GET /api/v1/user/transactions` controller

**Key Methods**:

```python
class GetTransactionHistoryHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_repository: TransactionRepository,
    ):
        self._current_user_service = current_user_service
        self._transaction_repository = transaction_repository

    async def execute(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: str | None = None,
        status: str | None = None,
        tx_type: str | None = None,
    ) -> TransactionHistoryResult:
        """Get transaction history for current user."""
```

**Query Flow**:

1. **Get Current User**:
```python
# Line 491-492: Get authenticated user
user = await self._current_user_service.get_current_user()
user_id = UserId(user.id_.value)
```

2. **Parse Filters**:
```python
# Line 494-511: Parse filter parameters
chain_filter = ChainType(chain.lower()) if chain else None

status_filter = None
if status:
    status_map = {
        "pending": TransactionStatus.PENDING,
        "success": TransactionStatus.SUCCESS,
        "failed": TransactionStatus.FAILED,
    }
    status_filter = status_map.get(status.lower())

type_filter = TX_TYPE_MAP.get(tx_type.lower()) if tx_type else None
```

3. **Execute Query**:
```python
# Line 514-521: Get transactions
transactions = await self._transaction_repository.get_by_user_id(
    user_id,
    limit=limit,
    offset=offset,
    chain=chain_filter,
    status=status_filter,
    tx_type=type_filter
)
```

4. **Get Total Count**:
```python
# Line 524-529: Get total for pagination
total = await self._transaction_repository.count_by_user_id(
    user_id,
    chain=chain_filter,
    status=status_filter,
    tx_type=type_filter
)
```

5. **Convert to Response**:
```python
# Line 532-567: Build response items
items = []
for tx in transactions:
    # Determine if incoming transaction
    is_incoming = bool(tx.tx_metadata and tx.tx_metadata.get("receiver_view"))
    from_address = tx.tx_metadata.get("from_address") if is_incoming else None

    items.append(TransactionHistoryItem(
        id=tx.id_.value,
        tx_hash=tx.tx_hash,
        type=tx.type.name.lower(),
        chain=tx.chain.value,
        status=tx.status.name.lower(),
        to_address=tx.to_address,
        asset_in=tx.asset_in,
        amount_in=str(tx.amount_in) if tx.amount_in else None,
        asset_out=tx.asset_out,
        amount_out=str(tx.amount_out) if tx.amount_out else None,
        fee_usd=str(tx.fee_usd) if tx.fee_usd else None,
        block_number=tx.block_number,
        confirmed_at=tx.confirmed_at.isoformat() if tx.confirmed_at else None,
        created_at=tx.created_at.value.isoformat(),
        explorer_url=get_explorer_url(tx.chain, tx.tx_hash),
        gas_used=tx.gas_used,
        gas_price=tx.gas_price,
        is_incoming=is_incoming,
        from_address=from_address
    ))
```

**Explorer URL Generation**:
```python
# Helper function (lines 432-451)
EXPLORER_URLS = {
    ChainType.ETHEREUM: "https://etherscan.io/tx/{tx_hash}",
    ChainType.ARBITRUM: "https://arbiscan.io/tx/{tx_hash}",
    ChainType.BASE: "https://basescan.org/tx/{tx_hash}",
    ChainType.POLYGON: "https://polygonscan.com/tx/{tx_hash}",
    ChainType.OPTIMISM: "https://optimistic.etherscan.io/tx/{tx_hash}",
    ChainType.BITCOIN: "https://mempool.space/tx/{tx_hash}",
    ChainType.BITCOIN_TESTNET: "https://mempool.space/testnet/tx/{tx_hash}"
}

def get_explorer_url(chain: ChainType, tx_hash: str | None) -> str | None:
    if not tx_hash:
        return None
    template = EXPLORER_URLS.get(chain)
    if not template:
        return None
    return template.format(tx_hash=tx_hash)
```

---

#### GetAdminTransactionHistoryHandler

**Purpose**: Get transaction history for any wallet/user (admin-only).

**Location**: `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 590-848)

**Responsibilities**:
- Verify admin access
- Support three query modes: global, wallet-scoped, user-scoped
- Parse filter parameters
- Execute query via `TransactionRepository`
- Return paginated transaction history

**Dependencies**:
- `CurrentUserService` (application): Get authenticated user
- `TransactionRepository` (port): Database queries
- `WalletRepository` (port): Wallet lookup (for wallet-scoped queries)

**Dependents**:
- `GET /api/v1/admin/transactions` controller

**Query Modes**:

1. **Global Scope** (no `wallet_address` or `user_id`):
   - Returns all transactions across all users
   - Uses `get_all()` repository method

2. **Wallet-Scoped** (`wallet_address` provided):
   - Returns transactions for specific wallet only
   - Looks up wallet by address
   - Uses `get_by_wallet_id()` repository method

3. **User-Scoped** (`user_id` provided):
   - Returns transactions across all user's wallets
   - Uses `get_by_user_id()` repository method

**Key Methods**:

```python
class GetAdminTransactionHistoryHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_repository: TransactionRepository,
        wallet_repository: WalletRepository,
    ):
        ...

    async def execute(
        self,
        *,
        wallet_address: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        chain: str | None = None,
        status: str | None = None,
        tx_type: str | None = None,
    ) -> AdminTransactionHistoryResult:
        """Get transaction history scoped by wallet or user."""
```

**Authorization and Mode Selection**:

```python
# Line 636-638: Verify admin access
current_user = await self._current_user_service.get_current_user()
if current_user.role != UserRole.ADMIN:
    raise AuthorizationError("Admin access required")

# Line 659: Normalize wallet address
normalized_wallet = wallet_address.lower() if wallet_address else None

# Mode selection based on parameters:
# 1. No filters → Global scope
# 2. wallet_address → Wallet-scoped
# 3. user_id → User-scoped
```

**Global Scope Query** (lines 664-719):
```python
if not normalized_wallet and not user_id:
    transactions = await self._transaction_repository.get_all(
        limit=limit,
        offset=offset,
        chain=chain_filter,
        status=status_filter,
        tx_type=type_filter
    )

    total = await self._transaction_repository.count_all_filtered(...)

    return AdminTransactionHistoryResult(
        wallet_address=None,
        user_id=None,
        transactions=items,
        total=total,
        limit=limit,
        offset=offset
    )
```

**Wallet-Scoped Query** (lines 721-790):
```python
if normalized_wallet:
    wallet = await self._wallet_repository.get_by_address(normalized_wallet)

    if not wallet:
        return AdminTransactionHistoryResult(
            wallet_address=normalized_wallet,
            user_id=None,
            transactions=[],
            total=0,
            limit=limit,
            offset=offset
        )

    transactions = await self._transaction_repository.get_by_wallet_id(
        wallet.id_,
        limit=limit,
        offset=offset,
        chain=chain_filter,
        status=status_filter,
        tx_type=type_filter
    )

    total = await self._transaction_repository.count_by_wallet_id(...)

    return AdminTransactionHistoryResult(
        wallet_address=normalized_wallet,
        user_id=wallet.user_id.value,
        transactions=items,
        total=total,
        limit=limit,
        offset=offset
    )
```

**User-Scoped Query** (lines 792-848):
```python
user_id_vo = UserId(user_id)

transactions = await self._transaction_repository.get_by_user_id(
    user_id_vo,
    limit=limit,
    offset=offset,
    chain=chain_filter,
    status=status_filter,
    tx_type=type_filter
)

total = await self._transaction_repository.count_by_user_id(...)

return AdminTransactionHistoryResult(
    wallet_address=None,
    user_id=user_id_vo.value,
    transactions=items,
    total=total,
    limit=limit,
    offset=offset
)
```

---

## Infrastructure Services

### Repositories

Repositories implement **data persistence and retrieval** following the Repository pattern.

---

#### SqlaWalletRepository

**Purpose**: SQLAlchemy implementation of `WalletRepository` port.

**Location**: `/src/app/infrastructure/adapters/wallet_repository_sqla.py` (lines 31-500+)

**Responsibilities**:
- CRUD operations for wallets in PostgreSQL
- Convert database rows to `Wallet` entities
- Support for Privy configuration fields (policy_ids, additional_signers)
- Upsert operations for wallet syncing
- Analytics methods for admin metrics

**Implements Port**: `WalletRepository` from `/src/app/domain/ports/wallet/wallet_repository.py`

**Key Methods**:

```python
class SqlaWalletRepository(WalletRepository):
    def __init__(self, session: MainAsyncSession):
        map_wallet_tables()  # Ensure SQLAlchemy mappings exist
        self._session = session

    # ============================================================
    # Read Operations
    # ============================================================

    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None:
        """Get wallet by ID."""

    async def get_by_address(self, address: str) -> Wallet | None:
        """Get wallet by blockchain address (case-insensitive)."""

    async def get_by_privy_wallet_id(self, privy_wallet_id: str) -> Wallet | None:
        """Get wallet by Privy wallet ID."""

    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]:
        """Get all wallets for a specific user."""

    async def get_by_user_and_address(
        self, user_id: UserId, address: str
    ) -> Wallet | None:
        """Get wallet by user ID and address combination."""

    async def get_by_user_and_provider(
        self, user_id: UserId, provider: WalletProvider
    ) -> list[Wallet]:
        """Get all wallets for a user with specific provider."""

    # ============================================================
    # Write Operations
    # ============================================================

    async def save(self, wallet: Wallet) -> Wallet:
        """Save a new wallet to database."""

    async def update(self, wallet: Wallet) -> Wallet:
        """Update an existing wallet."""

    async def delete(self, wallet_id: WalletId) -> None:
        """Delete a wallet (soft delete by setting status)."""

    # ============================================================
    # Upsert Operations
    # ============================================================

    async def upsert(
        self,
        user_id: UserId,
        address: str,
        provider: WalletProvider,
        privy_wallet_id: str | None = None,
        chain_type: str = "ethereum"
    ) -> Wallet:
        """Insert or update wallet (PostgreSQL ON CONFLICT)."""

    # ============================================================
    # Analytics
    # ============================================================

    async def mark_exported(self, privy_wallet_id: str) -> None:
        """Record export timestamp for audit trail."""

    async def count_by_provider(self, provider: WalletProvider) -> int:
        """Count wallets by provider (for admin metrics)."""
```

**Row-to-Entity Conversion** (lines 42-113):

```python
def _row_to_wallet(self, row: dict[str, Any]) -> Wallet:
    """Convert database row to Wallet entity."""
    # Parse chain type
    chain_str = row.get("default_chain")
    try:
        default_chain = ChainType(chain_str) if chain_str else ChainType.ETHEREUM
    except ValueError:
        default_chain = ChainType.ETHEREUM

    # Parse provider
    provider_str = row.get("provider")
    try:
        provider = WalletProvider(provider_str) if provider_str else WalletProvider.PRIVY
    except ValueError:
        provider = WalletProvider.PRIVY

    # Parse status
    status_val = row.get("status", WalletStatus.ACTIVE.value)
    try:
        status = WalletStatus(status_val)
    except ValueError:
        status = WalletStatus.ACTIVE

    # Parse policy_ids (JSON array)
    policy_ids_raw = row.get("policy_ids")
    policy_ids = policy_ids_raw if isinstance(policy_ids_raw, list) else []

    # Parse additional_signers (JSON array of objects)
    additional_signers_raw = row.get("additional_signers")
    additional_signers = []
    if isinstance(additional_signers_raw, list):
        for signer_data in additional_signers_raw:
            if isinstance(signer_data, dict):
                additional_signers.append(AdditionalSigner.from_dict(signer_data))

    return Wallet(
        id_=WalletId(row["id"]),
        user_id=UserId(row["user_id"]),
        privy_wallet_id=row.get("privy_wallet_id"),
        address=row["address"],
        provider=provider,
        default_chain=default_chain,
        status=status,
        created_at=CreatedAt(row.get("created_at")),
        updated_at=UpdatedAt(row.get("updated_at")),
        policy_ids=policy_ids,
        owner_type=row.get("owner_type"),
        owner_id=row.get("owner_id"),
        additional_signers=additional_signers,
        exported_at=row.get("exported_at"),
        imported_at=row.get("imported_at"),
        last_privy_sync_at=row.get("last_privy_sync_at")
    )
```

**Upsert Implementation** (PostgreSQL `ON CONFLICT`):

```python
async def upsert(
    self,
    user_id: UserId,
    address: str,
    provider: WalletProvider,
    privy_wallet_id: str | None = None,
    chain_type: str = "ethereum"
) -> Wallet:
    """Insert or update wallet using PostgreSQL ON CONFLICT."""
    try:
        table = self._get_table()

        # PostgreSQL upsert (ON CONFLICT UPDATE)
        stmt = pg_insert(table).values(
            user_id=user_id.value,
            address=address.lower(),
            provider=provider.value,
            privy_wallet_id=privy_wallet_id,
            default_chain=chain_type,
            status=WalletStatus.ACTIVE.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        ).on_conflict_do_update(
            constraint='unique_user_wallet_address',
            set_={
                'provider': provider.value,
                'privy_wallet_id': privy_wallet_id,
                'default_chain': chain_type,
                'updated_at': datetime.now(UTC)
            }
        ).returning(table.c.id)

        result = await self._session.execute(stmt)
        wallet_id = result.scalar_one()
        await self._session.commit()

        # Fetch and return the wallet
        return await self.get_by_id(WalletId(wallet_id))

    except SQLAlchemyError as error:
        await self._session.rollback()
        raise DataMapperError(DB_QUERY_FAILED) from error
```

**Database Schema** (from `/src/app/infrastructure/persistence_sqla/mappings/wallet.py`):

```python
# Table: wallets
id = Integer (primary key, autoincrement)
user_id = Integer (foreign key to users.id, cascade delete)
privy_wallet_id = String(255) (unique, nullable, index)
address = String(42) (not null, index)
provider = Enum(WalletProvider) (default: PRIVY)
default_chain = Enum(ChainType) (default: ARBITRUM)
status = Integer (default: ACTIVE)

# Privy configuration fields
policy_ids = JSON (nullable, array of strings)
owner_type = String(50) (nullable)
owner_id = String(255) (nullable)
additional_signers = JSON (nullable, array of objects)
exported_at = DateTime(timezone=True) (nullable)
imported_at = DateTime(timezone=True) (nullable)
last_privy_sync_at = DateTime(timezone=True) (nullable)

# Timestamps
created_at = DateTime(timezone=True) (server default: CURRENT_TIMESTAMP)
updated_at = DateTime(timezone=True) (server default: CURRENT_TIMESTAMP, on update)

# Constraints
UNIQUE (user_id, address)  # Prevent duplicate wallets for same user
```

---

#### SqlaTransactionRepository

**Purpose**: SQLAlchemy implementation of `TransactionRepository` port.

**Location**: `/src/app/infrastructure/adapters/transaction_repository_sqla.py` (lines 32-700+)

**Responsibilities**:
- CRUD operations for transactions in PostgreSQL
- Convert database rows to `Transaction` entities
- Support filtering by user, wallet, chain, status, type
- Pagination and counting queries
- Pending transaction queries (for confirmation worker)

**Implements Port**: `TransactionRepository` from `/src/app/domain/transactions/ports/transaction/transaction_repository.py`

**Key Methods**:

```python
class SqlaTransactionRepository(TransactionRepository):
    def __init__(self, session: MainAsyncSession):
        map_transaction_table()
        self._session = session

    # ============================================================
    # Read Operations
    # ============================================================

    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None:
        """Get transaction by ID."""

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction | None:
        """Get transaction by blockchain hash (returns first match)."""

    async def get_by_user_and_tx_hash(
        self, user_id: UserId, tx_hash: str
    ) -> Transaction | None:
        """Get transaction by user ID and hash combination."""

    async def get_by_user_id(
        self,
        user_id: UserId,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """Get transactions for a user with optional filters."""

    async def get_by_wallet_id(
        self,
        wallet_id: WalletId,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """Get transactions for a specific wallet."""

    async def get_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """Get all transactions (admin global view)."""

    async def get_pending_transactions(
        self,
        *,
        limit: int = 100,
        older_than_seconds: int | None = None,
    ) -> list[Transaction]:
        """Get pending transactions for confirmation worker."""

    # ============================================================
    # Write Operations
    # ============================================================

    async def save(self, transaction: Transaction) -> Transaction:
        """Save a new transaction to database."""

    async def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction."""

    async def update_status(
        self,
        transaction_id: TransactionId,
        status: TransactionStatus,
        block_number: int | None = None,
        confirmed_at: datetime | None = None,
        gas_used: int | None = None,
        gas_price: int | None = None,
    ) -> None:
        """Update transaction status and confirmation data."""

    # ============================================================
    # Count Operations
    # ============================================================

    async def count_by_user_id(
        self,
        user_id: UserId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """Count transactions for a user."""

    async def count_by_wallet_id(
        self,
        wallet_id: WalletId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """Count transactions for a wallet."""

    async def count_all_filtered(
        self,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """Count all transactions with filters (admin)."""
```

**Row-to-Entity Conversion** (lines 43-127):

```python
def _row_to_transaction(self, row: dict[str, Any]) -> Transaction:
    """Convert database row to Transaction entity."""
    # Parse chain type
    chain_val = row.get("chain")
    try:
        if isinstance(chain_val, ChainType):
            chain = chain_val
        elif isinstance(chain_val, str):
            chain = ChainType(chain_val)
        else:
            chain = ChainType.ETHEREUM
    except ValueError:
        chain = ChainType.ETHEREUM

    # Parse transaction type
    type_val = row.get("type")
    try:
        if isinstance(type_val, TransactionType):
            tx_type = type_val
        elif isinstance(type_val, int):
            tx_type = TransactionType(type_val)
        else:
            tx_type = TransactionType.SEND
    except ValueError:
        tx_type = TransactionType.SEND

    # Parse status
    status_val = row.get("status")
    try:
        if isinstance(status_val, TransactionStatus):
            status = status_val
        elif isinstance(status_val, int):
            status = TransactionStatus(status_val)
        else:
            status = TransactionStatus.PENDING
    except ValueError:
        status = TransactionStatus.PENDING

    # Parse decimal values
    def parse_decimal(val: Any) -> Decimal | None:
        if val is None:
            return None
        if isinstance(val, Decimal):
            return val
        return Decimal(str(val))

    return Transaction(
        id_=TransactionId(row["id"]),
        user_id=UserId(row["user_id"]),
        wallet_id=WalletId(row["wallet_id"]),
        to_address=row.get("to_address"),
        type=tx_type,
        chain=chain,
        asset_in=row.get("asset_in"),
        amount_in=parse_decimal(row.get("amount_in")),
        asset_out=row.get("asset_out"),
        amount_out=parse_decimal(row.get("amount_out")),
        fee=parse_decimal(row.get("fee")),
        fee_usd=parse_decimal(row.get("fee_usd")),
        tx_hash=row.get("tx_hash"),
        status=status,
        dex_aggregator=row.get("dex_aggregator"),
        dex_route=row.get("dex_route"),
        slippage=parse_decimal(row.get("slippage")),
        error_message=row.get("error_message"),
        block_number=row.get("block_number"),
        confirmed_at=row.get("confirmed_at"),
        created_at=CreatedAt(row.get("created_at")),
        gas_used=int(row.get("gas_used")) if row.get("gas_used") else None,
        gas_price=int(row.get("gas_price")) if row.get("gas_price") else None,
        tx_metadata=row.get("tx_metadata")
    )
```

**Pending Transactions Query** (for Celery confirmation worker):

```python
async def get_pending_transactions(
    self,
    *,
    limit: int = 100,
    older_than_seconds: int | None = None,
) -> list[Transaction]:
    """Get pending transactions that need confirmation."""
    try:
        table = self._get_table()
        conditions = [
            table.c.status == TransactionStatus.PENDING.value,
            table.c.tx_hash.isnot(None),  # Must have tx_hash
        ]

        if older_than_seconds is not None:
            cutoff = datetime.now(UTC) - timedelta(seconds=older_than_seconds)
            conditions.append(table.c.created_at < cutoff)

        stmt = (
            select(table)
            .where(and_(*conditions))
            .order_by(table.c.created_at.asc())  # Oldest first
            .limit(limit)
        )

        rows = (await self._session.execute(stmt)).mappings().all()
        return [self._row_to_transaction(dict(row)) for row in rows]

    except SQLAlchemyError as error:
        raise DataMapperError(DB_QUERY_FAILED) from error
```

**Database Schema** (from `/src/app/infrastructure/persistence_sqla/mappings/transaction.py`):

```python
# Table: transactions
id = Integer (primary key, autoincrement)
user_id = Integer (foreign key to users.id, cascade delete, index)
wallet_id = Integer (foreign key to wallets.id, cascade delete, index)

# Core transaction details
to_address = String(42) (nullable, index)
type = Integer (not null, index)  # 0=SWAP, 1=FUND, 5=SEND, etc.
chain = Enum(ChainType) (not null, index)

# Asset details
asset_in = String(20) (nullable)
amount_in = Numeric(30, 18) (nullable)
asset_out = String(20) (nullable)
amount_out = Numeric(30, 18) (nullable)

# Fees
fee = Numeric(30, 18) (nullable)
fee_usd = Numeric(10, 2) (nullable)

# On-chain data
tx_hash = String(66) (nullable, index)  # NOT globally unique
status = Integer (default: 0, not null, index)  # 0=PENDING, 1=SUCCESS, 2=FAILED

# DEX/Swap details
dex_aggregator = String(50) (nullable)
dex_route = JSON (nullable)
slippage = Numeric(5, 2) (nullable)
error_message = Text (nullable)

# Confirmation data
block_number = Integer (nullable, index)
confirmed_at = DateTime(timezone=True) (nullable)

# Timestamps
created_at = DateTime(timezone=True) (server default: CURRENT_TIMESTAMP, index)

# Analytics fields
gas_used = BigInteger (nullable)
gas_price = BigInteger (nullable)
tx_metadata = JSON (nullable)

# Constraints
UNIQUE (user_id, tx_hash)  # Same tx can appear for different users
```

---

### Gateways

Gateways provide **read-optimized queries** for CQRS pattern.

---

#### WalletReaderSqla (WalletQueryGateway)

**Purpose**: Read-optimized wallet queries with JOINs to user table.

**Location**: `/src/app/infrastructure/adapters/wallet_reader_sqla.py`

**Responsibilities**:
- Execute complex read queries with user data
- Support pagination, sorting, and search
- Return query models (not domain entities)
- Used by admin list wallets endpoint

**Implements Port**: `WalletQueryGateway` from `/src/app/application/common/ports/wallet_query_gateway.py`

**Key Methods**:

```python
class WalletReaderSqla(WalletQueryGateway):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def read_all(
        self, params: WalletListParams
    ) -> list[WalletQueryModel] | None:
        """
        Read all wallets with pagination, sorting, and search.

        Joins with users table to include owner information.

        Returns:
            List of WalletQueryModel or None if sorting field invalid
        """
        # Build query with JOIN
        query = (
            select(
                wallets_table,
                users_table.c.email.label("user_email"),
                users_table.c.name.label("user_name")
            )
            .select_from(wallets_table)
            .join(users_table, wallets_table.c.user_id == users_table.c.id)
        )

        # Apply search filter
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    wallets_table.c.address.ilike(search_term),
                    users_table.c.email.ilike(search_term),
                    users_table.c.name.ilike(search_term),
                    wallets_table.c.privy_wallet_id == params.search
                )
            )

        # Apply sorting
        sort_field = getattr(wallets_table.c, params.sorting.sorting_field, None)
        if not sort_field:
            return None  # Invalid sorting field

        if params.sorting.sorting_order == SortingOrder.DESC:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.limit(params.pagination.limit).offset(params.pagination.offset)

        # Execute query
        result = await self._session.execute(query)
        rows = result.mappings().all()

        # Convert to query models
        return [
            WalletQueryModel(
                id=row["id"],
                user_id=row["user_id"],
                privy_wallet_id=row["privy_wallet_id"],
                address=row["address"],
                provider=row["provider"],
                default_chain=row["default_chain"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                user_email=row["user_email"],
                user_name=row["user_name"]
            )
            for row in rows
        ]

    async def count_all(self, search: str | None = None) -> int:
        """Count wallets matching search criteria."""
        query = select(func.count(wallets_table.c.id))

        if search:
            search_term = f"%{search}%"
            query = query.select_from(wallets_table).join(
                users_table, wallets_table.c.user_id == users_table.c.id
            ).where(
                or_(
                    wallets_table.c.address.ilike(search_term),
                    users_table.c.email.ilike(search_term),
                    users_table.c.name.ilike(search_term),
                    wallets_table.c.privy_wallet_id == search
                )
            )

        result = await self._session.execute(query)
        return result.scalar_one()
```

**Query Model vs Entity**:
- **Query Model** (`WalletQueryModel`): Flat DTO with user info, optimized for display
- **Entity** (`Wallet`): Rich domain object with behavior and value objects

---

### External Integrations

---

#### PrivyClient

**Purpose**: HTTP client for Privy API integration.

**Location**: `/src/app/infrastructure/privy/client.py`

**Responsibilities**:
- Authenticate with Privy API (app ID + app secret)
- Fetch user wallets from Privy
- Get wallet details
- Export wallet private key (encrypted)
- Update wallet configuration
- Error handling and retries

**Configuration**: Loaded from `config/local/config.toml` under `[privy]` section

**Key Methods**:

```python
class PrivyClient:
    def __init__(self, app_id: str, app_secret: str):
        self._app_id = app_id
        self._app_secret = app_secret
        self._base_url = "https://auth.privy.io/api/v1"
        self._session = httpx.AsyncClient()

    async def list_user_wallets(
        self, privy_user_id: str
    ) -> list[PrivyWalletInfo]:
        """Fetch all wallets for a Privy user."""
        url = f"{self._base_url}/users/{privy_user_id}/wallets"
        headers = self._auth_headers()

        response = await self._session.get(url, headers=headers)

        if response.status_code == 404:
            raise UserNotFoundError(f"User {privy_user_id} not found")

        response.raise_for_status()

        data = response.json()
        return [
            PrivyWalletInfo(
                wallet_id=w["id"],
                address=w["address"],
                chain_type=ChainType(w["chain_type"]),
                wallet_type=WalletType(w["wallet_type"]),
                created_at=datetime.fromisoformat(w["created_at"]),
                is_recoverable=w.get("recoverable", True)
            )
            for w in data.get("wallets", [])
        ]

    async def get_wallet(self, wallet_id: str) -> dict:
        """Get wallet details by ID."""
        url = f"{self._base_url}/wallets/{wallet_id}"
        headers = self._auth_headers()

        response = await self._session.get(url, headers=headers)

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet {wallet_id} not found")

        response.raise_for_status()
        return response.json()

    async def export_wallet(
        self,
        wallet_id: str,
        recipient_public_key_b64: str,
    ) -> ExportWalletResponse:
        """Export wallet private key (HPKE encrypted)."""
        url = f"{self._base_url}/wallets/{wallet_id}/export"
        headers = self._auth_headers()

        payload = {
            "recipient_public_key": recipient_public_key_b64
        }

        response = await self._session.post(url, headers=headers, json=payload)

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet {wallet_id} not found")

        response.raise_for_status()

        data = response.json()
        return ExportWalletResponse(
            ciphertext=data["ciphertext"],
            encapsulated_key=data["encapsulated_key"]
        )

    async def update_wallet(
        self,
        wallet_id: str,
        policy_ids: list[str] | None = None,
        owner: dict | None = None,
        additional_signers: list[dict] | None = None,
    ) -> dict:
        """Update wallet configuration."""
        url = f"{self._base_url}/wallets/{wallet_id}"
        headers = self._auth_headers()

        payload = {}
        if policy_ids is not None:
            payload["policy_ids"] = policy_ids
        if owner is not None:
            payload["owner"] = owner
        if additional_signers is not None:
            payload["additional_signers"] = additional_signers

        response = await self._session.patch(url, headers=headers, json=payload)

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet {wallet_id} not found")

        response.raise_for_status()
        return response.json()

    def _auth_headers(self) -> dict:
        """Build authorization headers for Privy API."""
        return {
            "privy-app-id": self._app_id,
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/json"
        }

    def _encode_credentials(self) -> str:
        """Base64 encode app_id:app_secret."""
        credentials = f"{self._app_id}:{self._app_secret}"
        return base64.b64encode(credentials.encode()).decode()
```

**Error Handling**:
```python
class PrivyClientError(Exception):
    """Base Privy API error."""

class PrivyWalletNotFoundError(PrivyClientError):
    """Wallet not found in Privy."""

class UserNotFoundError(PrivyClientError):
    """User not found in Privy."""

class WalletProviderError(Exception):
    """General wallet provider error."""
```

---

#### HPKEDecryptor

**Purpose**: HPKE (Hybrid Public Key Encryption) for secure wallet export.

**Location**: `/src/app/infrastructure/privy/hpke.py`

**Responsibilities**:
- Generate HPKE key pairs (X25519 + ChaCha20Poly1305)
- Decrypt wallet private keys from Privy
- Secure key management (ephemeral keys)

**HPKE Standard**: RFC 9180 (Hybrid Public Key Encryption)

**Key Methods**:

```python
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class HPKEDecryptor:
    def __init__(self):
        self._private_key = None
        self._public_key = None

    def get_or_create_key_pair(self) -> HPKEKeyPair:
        """Generate ephemeral HPKE key pair."""
        if self._private_key is None:
            self._private_key = X25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()

        # Export public key as base64
        public_key_bytes = self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        public_key_b64 = base64.b64encode(public_key_bytes).decode()

        return HPKEKeyPair(
            private_key=self._private_key,
            public_key_b64=public_key_b64
        )

    def decrypt(
        self,
        ciphertext_b64: str,
        encapsulated_key_b64: str,
    ) -> str:
        """
        Decrypt ciphertext using HPKE.

        Args:
            ciphertext_b64: Base64-encoded ciphertext from Privy
            encapsulated_key_b64: Base64-encoded ephemeral public key

        Returns:
            Decrypted private key (hex string)
        """
        # Decode base64
        ciphertext = base64.b64decode(ciphertext_b64)
        encapsulated_key = base64.b64decode(encapsulated_key_b64)

        # Perform HPKE decryption
        # (Simplified - actual implementation uses pyhpke library)
        shared_secret = self._private_key.exchange(
            X25519PublicKey.from_public_bytes(encapsulated_key)
        )

        # Derive encryption key from shared secret
        # Decrypt using ChaCha20Poly1305
        decrypted = decrypt_with_chacha20poly1305(ciphertext, shared_secret)

        # Return as hex string
        return decrypted.hex()
```

**Security Properties**:
- **Ephemeral Keys**: Private key only exists in memory
- **Perfect Forward Secrecy**: New key pair for each export
- **Authenticated Encryption**: ChaCha20Poly1305 provides integrity
- **No Key Storage**: Keys discarded after use

---

## Service Dependencies

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                        Controllers                           │
│  (wallet/router, transaction/router, admin/*)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Handlers                       │
│  SaveSwapTransactionHandler ────┐                           │
│  ExportWallet ───────────────┐  │                           │
│  GetMyWalletsHandler ─────┐  │  │                           │
│  LogTransactionHandler ─┐ │  │  │                           │
└─────────────────────────┼─┼──┼──┼───────────────────────────┘
                          │ │  │  │
                          ▼ ▼  ▼  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Domain Ports                              │
│  TransactionRepository ◄─────────────┐                      │
│  WalletRepository ◄──────────────┐   │                      │
│  EmbeddedWalletProviderPort ◄─┐  │   │                      │
└───────────────────────────────┼──┼───┼───────────────────── ┘
                                │  │   │
                                ▼  ▼   ▼
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Adapters                       │
│  SqlaTransactionRepository                                   │
│  SqlaWalletRepository                                        │
│  PrivyClient + HPKEDecryptor                                 │
└─────────────────────────────────────────────────────────────┘
```

### Dishka Dependency Injection

Services are wired together via Dishka providers:

```python
# src/app/setup/ioc/providers.py

from dishka import Provider, Scope, provide

class WalletProvider(Provider):
    scope = Scope.REQUEST

    # Infrastructure
    wallet_repository = provide(
        source=SqlaWalletRepository,
        provides=WalletRepository
    )

    transaction_repository = provide(
        source=SqlaTransactionRepository,
        provides=TransactionRepository
    )

    wallet_provider = provide(
        source=PrivyClientAdapter,
        provides=EmbeddedWalletProviderPort
    )

    # Application Handlers
    get_my_wallets_handler = provide(GetMyWalletsHandler)
    sync_wallets_handler = provide(SyncWalletsHandler)
    log_transaction_handler = provide(LogTransactionHandler)
    get_transaction_history_handler = provide(GetTransactionHistoryHandler)

    # Commands
    save_swap_transaction_handler = provide(SaveSwapTransactionHandler)
    export_wallet = provide(ExportWallet)
    update_privy_wallet = provide(UpdatePrivyWallet)

    # Queries
    list_wallets_query = provide(ListWalletsQueryService)
    get_wallet_details_query = provide(GetPrivyWalletDetails)
```

**Scope Explanation**:
- `Scope.REQUEST`: New instance per HTTP request
- `Scope.APP`: Singleton for application lifetime
- `Scope.SESSION`: Per database session (SQLAlchemy)

---

## Service Patterns

### Pattern 1: Command Handler Pattern

Commands encapsulate **write operations** with clear input/output contracts.

**Structure**:
```python
# Command (input)
@dataclass(frozen=True)
class SaveSwapTransactionCommand:
    user_id: int
    tx_hash: str
    chain: str
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    # ... additional fields

# Result (output)
@dataclass(frozen=True)
class SaveSwapTransactionResult:
    transaction_id: int
    tx_hash: str

# Handler
class SaveSwapTransactionHandler:
    def __init__(self, transaction_repository: TransactionRepository):
        self._transaction_repository = transaction_repository

    async def handle(
        self, command: SaveSwapTransactionCommand
    ) -> SaveSwapTransactionResult:
        # 1. Validate
        # 2. Create entity
        # 3. Persist
        # 4. Return result
```

**Benefits**:
- Clear contracts (type-safe)
- Single responsibility
- Easy to test (mock repository)
- Audit trail (command history)

---

### Pattern 2: Query Service Pattern

Query services implement **read operations** with optimized queries.

**Structure**:
```python
# Request (input)
@dataclass(frozen=True)
class ListWalletsRequest:
    limit: int
    offset: int
    sorting_field: str
    sorting_order: SortingOrder
    search: str | None = None

# Response (output)
class ListWalletsResponse(TypedDict):
    wallets: list[WalletQueryModel]
    total: int

# Query Service
class ListWalletsQueryService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_query_gateway: WalletQueryGateway,
    ):
        ...

    async def execute(
        self, request: ListWalletsRequest
    ) -> ListWalletsResponse:
        # 1. Authorize
        # 2. Build query params
        # 3. Execute via gateway
        # 4. Return response
```

**Benefits**:
- Read-optimized (JOINs, projections)
- Separate from write model (CQRS)
- Pagination-friendly
- Search and filtering support

---

### Pattern 3: Repository Pattern

Repositories abstract **data persistence** from business logic.

**Port (Interface)**:
```python
# src/app/domain/ports/wallet/wallet_repository.py

class WalletRepository(ABC):
    @abstractmethod
    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None:
        pass

    @abstractmethod
    async def save(self, wallet: Wallet) -> Wallet:
        pass

    @abstractmethod
    async def update(self, wallet: Wallet) -> Wallet:
        pass
```

**Adapter (Implementation)**:
```python
# src/app/infrastructure/adapters/wallet_repository_sqla.py

class SqlaWalletRepository(WalletRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None:
        # SQLAlchemy implementation
        ...

    async def save(self, wallet: Wallet) -> Wallet:
        # SQLAlchemy implementation
        ...
```

**Benefits**:
- Technology independence (can swap PostgreSQL → MongoDB)
- Testability (mock repository)
- Clear boundaries (domain doesn't know about SQL)

---

### Pattern 4: Port-Adapter Pattern

Ports define **interfaces for external dependencies**, adapters implement them.

**Port**:
```python
# src/app/domain/ports/wallet/embedded_wallet_provider.py

class EmbeddedWalletProviderPort(ABC):
    @abstractmethod
    async def list_user_wallets(
        self, privy_user_id: str
    ) -> list[PrivyWalletInfo]:
        pass

    @abstractmethod
    async def export_wallet(
        self, wallet_id: str, public_key: str
    ) -> ExportResponse:
        pass
```

**Adapter**:
```python
# src/app/infrastructure/adapters/privy_client_adapter.py

class PrivyClientAdapter(EmbeddedWalletProviderPort):
    def __init__(self, privy_client: PrivyClient):
        self._privy_client = privy_client

    async def list_user_wallets(
        self, privy_user_id: str
    ) -> list[PrivyWalletInfo]:
        # Calls PrivyClient, handles errors, converts to domain models
        ...
```

**Benefits**:
- Framework independence
- Easy to swap implementations (e.g., Privy → AWS KMS)
- Testability (mock adapter)

---

## Summary

The Wallets & Transactions module services follow **Hexagonal Architecture** with:

**Domain Layer**:
- No services yet (data-oriented operations)
- Future candidates: WalletPolicyService, TransactionValidationService

**Application Layer**:
- **Commands**: SaveSwapTransactionHandler, ExportWallet, UpdatePrivyWallet
- **Queries**: ListWalletsQueryService, GetPrivyWalletDetails
- **Handlers**: GetMyWalletsHandler, LogTransactionHandler, GetTransactionHistoryHandler

**Infrastructure Layer**:
- **Repositories**: SqlaWalletRepository, SqlaTransactionRepository
- **Gateways**: WalletReaderSqla (CQRS read side)
- **External**: PrivyClient, HPKEDecryptor

**Key Patterns**:
- Command-Query Responsibility Segregation (CQRS)
- Repository Pattern
- Port-Adapter Pattern
- Dependency Injection (Dishka)

**Next Steps**: See `celery.md` for background task documentation.
