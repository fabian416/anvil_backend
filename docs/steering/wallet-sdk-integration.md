# Wallet SDK Integration - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

Anvil Backend implementa una integración completa con **Privy SDK** para gestión de wallets, soportando:

1. **Multi-Chain Support**: Ethereum, Solana, Bitcoin, Polygon, Arbitrum, Optimism, Base
2. **Multiple Wallet Types**: Embedded, External, Imported, Server-Controlled
3. **Provider Abstraction**: Port-Adapter pattern para cambiar proveedores fácilmente
4. **Offline Capability**: Modo híbrido con persistencia local para alta disponibilidad

---

## Architecture Overview

### Provider Abstraction Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  Interactors: ExportWallet, GetMyWallets, SyncWallets           │
│  Uses: EmbeddedWalletProviderPort (abstract interface)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DOMAIN LAYER (Ports)                            │
├─────────────────────────────────────────────────────────────────┤
│  EmbeddedWalletProviderPort     │    WalletRepository           │
│  (External Provider Interface)  │    (Database Persistence)     │
└─────────────────────────────────┴───────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  PrivyClient                    │    WalletRepositorySqla       │
│  (Privy API Implementation)     │    (PostgreSQL Adapter)       │
└─────────────────────────────────┴───────────────────────────────┘
```

### Wallet Source Modes

El sistema soporta tres modos de operación configurables:

| Mode | Description | Use Case |
|------|-------------|----------|
| **PRIVY** | Privy API as primary source, DB as cache | Production (default) |
| **HYBRID** | Privy when available, always persist to DB | High availability |
| **LOCAL** | DB-only, no Privy calls | Offline/air-gapped |

```toml
# config/local/config.toml
[privy]
APP_ID = "your-privy-app-id"
API_BASE_URL = "https://api.privy.io"
WALLETS_SOURCE_MODE = "hybrid"  # privy, hybrid, or local
```

---

## Supported Blockchains

### Chain Types

```python
class ChainType(str, Enum):
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    OTHER = "other"
```

### Chain-Specific Features

| Chain | Wallet Creation | Transactions | Export | Notes |
|-------|-----------------|--------------|--------|-------|
| Ethereum | Frontend + Backend | ✅ | ✅ | Primary chain |
| Polygon | Frontend + Backend | ✅ | ✅ | Same wallet as ETH |
| Arbitrum | Frontend + Backend | ✅ | ✅ | Same wallet as ETH |
| Optimism | Frontend + Backend | ✅ | ✅ | Same wallet as ETH |
| Base | Frontend + Backend | ✅ | ✅ | Same wallet as ETH |
| Solana | Frontend + Backend | ✅ | ✅ | Separate wallet |
| Bitcoin | **Backend Only** | ✅ | ✅ | Requires server-side creation |

---

## Wallet Types

### Classification

```python
class WalletType(str, Enum):
    EMBEDDED = "embedded"        # Privy-managed wallet
    EXTERNAL = "external"        # User-owned (MetaMask, Phantom)
    SERVER_CONTROLLED = "server" # Backend-controlled
    IMPORTED = "imported"        # Via private key import
```

### Provider Types

```python
class WalletProvider(Enum):
    PRIVY = "privy"       # Privy embedded wallet
    EXTERNAL = "external" # Browser extension wallet
    IMPORTED = "imported" # Imported via private key
```

---

## API Endpoints

### User Wallet Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/wallet/me` | GET | ✅ | Get all user wallets |
| `/wallet/sync` | POST | ✅ | Sync wallets from frontend |
| `/wallet/export` | POST | ✅ | Export wallet private key |

### Bitcoin Wallet Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/user/bitcoin/wallets/create` | POST | ✅ | Create Bitcoin wallet |
| `/user/bitcoin/wallets/me` | GET | ✅ | Get Bitcoin wallet |
| `/user/bitcoin/transactions` | POST | ✅ | Log Bitcoin transaction |
| `/user/bitcoin/transactions` | GET | ✅ | Get transaction history |

### Admin Wallet Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/admin/wallet` | GET | 🔒 Admin | List all wallets |
| `/admin/wallet/{id}` | GET | 🔒 Admin | Get wallet details |
| `/admin/wallet/{id}` | PATCH | 🔒 Admin | Update wallet config |

---

## Get My Wallets

**Endpoint**: `GET /api/v1/wallet/me`

Combina datos de múltiples fuentes:
1. **Privy API**: Wallets del proveedor
2. **Local DB**: Wallets importados y cache
3. **User Record**: Primary wallet address

### Request

```bash
curl -X GET http://localhost:8000/api/v1/wallet/me \
  -H "Authorization: Bearer <access_token>"
```

### Response

```json
{
  "user_id": 123,
  "privy_user_id": "did:privy:abc123",
  "wallets": [
    {
      "wallet_id": "wallet_xyz",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "is_primary": true,
      "source": "privy",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "wallet_id": "imported:0xabc...",
      "address": "0xabcdef1234567890abcdef1234567890abcdef12",
      "chain_type": "ethereum",
      "wallet_type": "imported",
      "is_primary": false,
      "source": "local",
      "created_at": "2024-01-20T15:45:00Z"
    }
  ],
  "primary_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "privy_connected": true,
  "message": null
}
```

---

## Sync Wallets from Frontend

**Endpoint**: `POST /api/v1/wallet/sync`

El frontend envía la lista de wallets conectados para persistencia.

### Request

```json
{
  "wallets": [
    {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "privy_wallet_id": "wallet_xyz"
    },
    {
      "address": "0xabcdef1234567890abcdef1234567890abcdef12",
      "chain_type": "ethereum",
      "wallet_type": "imported",
      "privy_wallet_id": null
    }
  ]
}
```

### Response

```json
{
  "user_id": 123,
  "privy_user_id": "did:privy:abc123",
  "wallets": [...],
  "primary_wallet_address": "0x123...",
  "privy_connected": false,
  "message": "Wallets synced from frontend (2 imported, 2 persisted)"
}
```

---

## Export Wallet Private Key

**Endpoint**: `POST /api/v1/wallet/export`

Exporta la clave privada de un wallet embebido usando HPKE encryption.

### Security Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Backend    │     │   Privy API  │     │    User      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │  1. Generate HPKE  │                    │
       │  key pair          │                    │
       │                    │                    │
       │  2. Send public    │                    │
       │  key to Privy ────►│                    │
       │                    │                    │
       │  3. Privy encrypts │                    │
       │  private key ◄─────│                    │
       │                    │                    │
       │  4. Decrypt with   │                    │
       │  HPKE private key  │                    │
       │                    │                    │
       │  5. Return plain   │                    │
       │  private key ──────────────────────────►│
       ▼                    ▼                    ▼
```

### Request

```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "wallet_address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7"
}
```

### Response

```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7",
  "private_key": "0x1a2b3c4d5e6f...",
  "chain_type": "ethereum"
}
```

### HPKE Configuration

Privy uses HPKE with:
- **KEM**: DHKEM_P256_HKDF_SHA256
- **KDF**: HKDF_SHA256
- **AEAD**: CHACHA20_POLY1305

```python
from pyhpke import AEADId, CipherSuite, KDFId, KEMId

suite = CipherSuite.new(
    KEMId.DHKEM_P256_HKDF_SHA256,
    KDFId.HKDF_SHA256,
    AEADId.CHACHA20_POLY1305,
)
```

---

## Bitcoin Wallet Creation

Bitcoin wallets **must be created server-side** due to Privy SDK limitations.

### Create Bitcoin Wallet

**Endpoint**: `POST /api/v1/user/bitcoin/wallets/create`

```bash
curl -X POST http://localhost:8000/api/v1/user/bitcoin/wallets/create \
  -H "Authorization: Bearer <access_token>"
```

### Response

```json
{
  "wallet_id": 42,
  "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "chain": "bitcoin",
  "privy_wallet_id": "wallet_abc123",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Bitcoin Address Validation

```python
# Supported Bitcoin address formats
BTC_P2PKH_PATTERN = r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"     # Legacy
BTC_P2SH_PATTERN = r"^3[a-km-zA-HJ-NP-Z1-9]{25,34}$"        # SegWit compatible
BTC_BECH32_PATTERN = r"^bc1[a-z0-9]{39,59}$"                # Native SegWit
BTC_BECH32M_PATTERN = r"^bc1p[a-z0-9]{58}$"                 # Taproot

# Testnet patterns
BTC_TESTNET_P2PKH = r"^[mn][a-km-zA-HJ-NP-Z1-9]{25,34}$"
BTC_TESTNET_P2SH = r"^2[a-km-zA-HJ-NP-Z1-9]{25,34}$"
BTC_TESTNET_BECH32 = r"^tb1[a-z0-9]{39,59}$"
```

---

## Bitcoin Transaction Logging

### Log Transaction

**Endpoint**: `POST /api/v1/user/bitcoin/transactions`

```json
{
  "tx_hash": "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
  "from_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "to_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
  "amount_btc": "0.001",
  "fee_btc": "0.00001",
  "network": "bitcoin"
}
```

### Response

```json
{
  "id": 123,
  "tx_hash": "a1075db55d416d3...f5d48d",
  "status": "pending",
  "chain": "bitcoin",
  "from_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "to_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
  "amount_btc": "0.001",
  "created_at": "2024-01-15T10:30:00Z",
  "explorer_url": "https://mempool.space/tx/a1075db55d416d3..."
}
```

---

## Privy Client Interface

### EmbeddedWalletProviderPort (Abstract Interface)

```python
@runtime_checkable
class EmbeddedWalletProviderPort(Protocol):
    """Abstract interface for wallet providers."""
    
    @property
    def provider_name(self) -> str: ...
    
    # Token Verification
    async def verify_token(self, access_token: str) -> TokenVerificationResult: ...
    
    # User Operations
    async def get_user(self, user_id: str) -> UserInfo: ...
    async def get_user_by_email(self, email: str) -> UserInfo | None: ...
    async def get_user_by_wallet_address(self, address: str) -> UserInfo | None: ...
    
    # Wallet Operations
    async def get_wallet(self, wallet_id: str) -> WalletInfo: ...
    async def get_wallet_by_address(self, address: str, chain: ChainType) -> WalletInfo | None: ...
    async def list_wallets(self, cursor: str | None, limit: int, chain: ChainType | None) -> WalletListResult: ...
    async def list_user_wallets(self, user_id: str) -> list[WalletInfo]: ...
    
    # Wallet Creation
    async def create_wallet_for_user(self, user_id: str, chain: ChainType) -> WalletInfo: ...
    
    # Health Check
    async def health_check(self) -> dict: ...
    
    # Lifecycle
    async def close(self) -> None: ...
```

### PrivyClient (Implementation)

```python
class PrivyClient(EmbeddedWalletProviderPort):
    """HTTP client for Privy API."""
    
    def __init__(self, settings: PrivySettings):
        self._settings = settings
        self._http_client: httpx.AsyncClient | None = None
    
    async def get_user(self, user_id: str) -> UserInfo:
        """GET /v1/users/{user_id}"""
        ...
    
    async def list_user_wallets(self, user_id: str) -> list[WalletInfo]:
        """List all wallets for a user."""
        ...
    
    async def create_wallet_for_user(self, user_id: str, chain: ChainType) -> WalletInfo:
        """POST /v1/wallets - Create wallet."""
        ...
    
    async def export_wallet(self, wallet_id: str, public_key: str) -> WalletExportResponse:
        """POST /v1/wallets/{id}/export - Export encrypted private key."""
        ...
```

---

## Database Schema

### Wallet Entity

```python
@dataclass(eq=False, kw_only=True)
class Wallet(Entity[WalletId]):
    user_id: UserId
    privy_wallet_id: str | None     # Can be None for imported
    address: str
    provider: WalletProvider        # PRIVY, EXTERNAL, IMPORTED
    default_chain: ChainType
    status: WalletStatus
    created_at: CreatedAt
    updated_at: UpdatedAt
    
    # Privy configuration fields
    policy_ids: list[str]
    owner_type: str | None
    owner_id: str | None
    additional_signers: list[AdditionalSigner]
    exported_at: datetime | None
    imported_at: datetime | None
    last_privy_sync_at: datetime | None
```

### Database Table

```sql
CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    privy_wallet_id VARCHAR(255),
    address VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    default_chain VARCHAR(50) NOT NULL DEFAULT 'ethereum',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Privy config fields
    policy_ids JSONB DEFAULT '[]',
    owner_type VARCHAR(50),
    owner_id VARCHAR(255),
    additional_signers JSONB DEFAULT '[]',
    exported_at TIMESTAMP,
    imported_at TIMESTAMP,
    last_privy_sync_at TIMESTAMP,
    
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    UNIQUE(user_id, address)
);

CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_privy_wallet_id ON wallets(privy_wallet_id);
```

---

## Wallet Repository Interface

```python
class WalletRepository(Protocol):
    """Repository for wallet persistence."""
    
    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None: ...
    async def get_by_address(self, address: str) -> Wallet | None: ...
    async def get_by_privy_wallet_id(self, privy_id: str) -> Wallet | None: ...
    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]: ...
    async def get_by_user_and_provider(self, user_id: UserId, provider: WalletProvider) -> list[Wallet]: ...
    
    async def save(self, wallet: Wallet) -> Wallet: ...
    async def update(self, wallet: Wallet) -> Wallet: ...
    async def upsert(self, user_id: UserId, address: str, provider: WalletProvider, ...) -> Wallet: ...
    async def delete(self, wallet_id: WalletId) -> bool: ...
    
    async def mark_exported(self, privy_wallet_id: str) -> bool: ...
    
    # Analytics
    async def count_all(self) -> int: ...
    async def count_by_provider(self, provider: WalletProvider) -> int: ...
    async def get_wallet_counts_by_provider(self) -> dict[str, int]: ...
```

---

## Configuration

### Privy Settings

```toml
# config/local/config.toml
[privy]
APP_ID = "your-privy-app-id"
API_BASE_URL = "https://api.privy.io"
WALLETS_SOURCE_MODE = "hybrid"

# config/local/.secrets.toml
[privy]
APP_SECRET = "your-privy-app-secret"
```

### Python Config Class

```python
class PrivySettings(BaseModel):
    app_id: str = Field(..., alias="APP_ID")
    app_secret: str = Field(default="", alias="APP_SECRET")
    api_base_url: str = Field(default="https://api.privy.io", alias="API_BASE_URL")
    wallets_source_mode: WalletSourceMode = Field(default=WalletSourceMode.HYBRID)
    
    @property
    def basic_auth_credentials(self) -> str:
        """Base64-encoded Basic Auth credentials."""
        credentials = f"{self.app_id}:{self.app_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    @property
    def is_offline_mode(self) -> bool:
        return self.wallets_source_mode == WalletSourceMode.LOCAL
    
    @property
    def should_call_privy(self) -> bool:
        return self.wallets_source_mode in (WalletSourceMode.PRIVY, WalletSourceMode.HYBRID)
```

---

## Error Handling

### Wallet Provider Errors

```python
class WalletProviderError(Exception):
    """Base exception for wallet provider errors."""
    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")

class WalletNotFoundError(WalletProviderError):
    """Wallet not found in the provider."""

class AuthenticationError(WalletProviderError):
    """Provider credentials invalid."""

class RateLimitError(WalletProviderError):
    """Rate limit exceeded."""
    def __init__(self, message: str, provider: str, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(message, provider)

class UserNotFoundError(WalletProviderError):
    """User not found in the provider."""
```

### HTTP Error Mapping

| Error | HTTP Status | Response |
|-------|-------------|----------|
| `AuthenticationError` | 401 | Unauthorized |
| `WalletNotFoundError` | 404 | Not Found |
| `RateLimitError` | 429 | Too Many Requests |
| `WalletProviderError` | 503 | Service Unavailable |

---

## Security Considerations

### Private Key Handling

- **Never logged**: Private keys are never written to logs
- **Never stored**: Private keys are not persisted
- **HPKE encryption**: Secure transfer from Privy
- **Ownership verification**: User must own the wallet to export

### Export Audit Trail

```python
# Mark wallet as exported for audit
await wallet_repository.mark_exported(wallet_id)
```

- `exported_at` timestamp recorded in DB
- Enables compliance and security auditing

### Wallet Ownership Verification

```python
# Before export, verify ownership
user_wallets = await wallet_provider.list_user_wallets(privy_user_id)
user_wallet_ids = {w.wallet_id for w in user_wallets}

if request.wallet_id not in user_wallet_ids:
    raise HTTPException(
        status_code=403,
        detail="Wallet does not belong to the authenticated user"
    )
```

---

## Frontend Integration

### Privy SDK Setup (React)

```typescript
import { PrivyProvider } from '@privy-io/react-auth';

function App() {
  return (
    <PrivyProvider
      appId="your-privy-app-id"
      config={{
        loginMethods: ['wallet', 'email', 'google', 'apple'],
        appearance: {
          theme: 'dark',
        },
        embeddedWallets: {
          createOnLogin: 'users-without-wallets',
        },
      }}
    >
      <YourApp />
    </PrivyProvider>
  );
}
```

### Sync Wallets to Backend

```typescript
import { useWallets } from '@privy-io/react-auth';

function WalletSync() {
  const { wallets } = useWallets();
  
  useEffect(() => {
    const syncWallets = async () => {
      await fetch('/api/v1/wallet/sync', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallets: wallets.map(w => ({
            address: w.address,
            chain_type: w.chainType,
            wallet_type: w.walletClientType === 'privy' ? 'embedded' : 'external',
            privy_wallet_id: w.id,
          })),
        }),
      });
    };
    
    if (wallets.length > 0) {
      syncWallets();
    }
  }, [wallets]);
  
  return null;
}
```

---

## Switching Wallet Providers

The port-adapter pattern allows easy provider switching:

### 1. Implement the Port

```python
# infrastructure/wallet_providers/dynamic/client.py
class DynamicClient(EmbeddedWalletProviderPort):
    """Dynamic.xyz wallet provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "dynamic"
    
    async def get_user(self, user_id: str) -> UserInfo:
        # Dynamic API implementation
        ...
```

### 2. Update Dependency Injection

```python
# setup/ioc/infrastructure.py
@provide
def get_wallet_provider(
    privy_client: PrivyClient,  # or DynamicClient
) -> EmbeddedWalletProviderPort:
    return privy_client
```

---

## Key Files Reference

| Layer | File | Purpose |
|-------|------|---------|
| Domain | `ports/wallet/embedded_wallet_provider.py` | Provider interface |
| Domain | `ports/wallet/wallet_repository.py` | Repository interface |
| Domain | `entities/wallet.py` | Wallet entity |
| Domain | `enums/wallet_provider.py` | Provider types |
| Infrastructure | `privy/client.py` | Privy API client |
| Infrastructure | `privy/hpke.py` | HPKE encryption |
| Infrastructure | `auth/handlers/wallet_me.py` | Wallet handlers |
| Presentation | `controllers/wallet/router.py` | Wallet routes |
| Presentation | `controllers/wallet/my_wallets.py` | Get/Sync endpoints |
| Presentation | `controllers/wallet/export_wallet.py` | Export endpoint |
| Presentation | `controllers/bitcoin/router.py` | Bitcoin endpoints |
| Config | `config/privy.py` | Privy settings |

---

## Testing

### Test Wallet Endpoints

```bash
# Get wallets
curl http://localhost:8000/api/v1/wallet/me \
  -H "Authorization: Bearer <token>"

# Sync wallets
curl -X POST http://localhost:8000/api/v1/wallet/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"wallets": [{"address": "0x...", "chain_type": "ethereum", "wallet_type": "embedded"}]}'

# Create Bitcoin wallet
curl -X POST http://localhost:8000/api/v1/user/bitcoin/wallets/create \
  -H "Authorization: Bearer <token>"
```

### Privy Health Check

```python
health = await privy_client.health_check()
# {"status": "healthy", "latency_ms": 150, "message": "Privy API is responding"}
```

---

**Last Updated**: January 2, 2026
