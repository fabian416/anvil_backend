# DeFi Protocol Adapters Guide

This document describes the DeFi protocol adapters implemented in the Anvil Backend, following the hexagonal architecture pattern.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Available Adapters](#available-adapters)
3. [Implementation Pattern](#implementation-pattern)
4. [Testing Strategy](#testing-strategy)
5. [Adding New Adapters](#adding-new-adapters)

## Architecture Overview

### Hexagonal Architecture Pattern

DeFi adapters follow the hexagonal (ports and adapters) architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Domain Layer                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │   Entities       │  │  Value Objects   │  │    Ports      │ │
│  │ - Pool           │  │ - PoolAPY        │  │ (Interfaces)  │ │
│  │ - Position       │  │ - SwapQuote      │  │ - CurveGateway│ │
│  │ - Market         │  │ - TVLData        │  │ - AaveGateway │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Adapters                               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ CurveAdapter│ │ AaveAdapter│  │ LayerZeroAdapter   │  │  │
│  │  └──────┬─────┘  └──────┬─────┘  └────────┬───────────┘  │  │
│  │         │               │                  │              │  │
│  │  ┌──────▼─────┐  ┌──────▼─────┐  ┌────────▼───────────┐  │  │
│  │  │ CurveClient│  │ AaveClient │  │ LayerZeroClient    │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Domain Ports** (Interfaces): Define contracts in `src/app/domain/ports/`
2. **Adapters**: Implement ports in `src/app/infrastructure/adapters/external/`
3. **Clients**: API wrappers in `src/app/infrastructure/adapters/external/`
4. **Caching**: `ExternalAPICache` for performance optimization

## Available Adapters

### Curve Finance Adapter

**Purpose**: DEX liquidity pools, swaps, and yield optimization

**Location**: `src/app/infrastructure/adapters/external/curve_adapter.py`

**Capabilities**:
- Get pool information and TVL
- Calculate pool APYs
- Get swap quotes
- Monitor gauges and emissions

**Example Usage**:
```python
from app.infrastructure.adapters.external.curve_adapter import CurveAdapter
from app.infrastructure.adapters.external.curve_client import CurveClient

# Initialize
client = CurveClient(api_key="your_api_key")
adapter = CurveAdapter(client=client, cache=cache)

# Get pools
pools = await adapter.get_pools(chain="ethereum")

# Get swap quote
quote = await adapter.get_swap_quote(
    from_token="USDC",
    to_token="DAI",
    amount=Decimal("1000"),
)
```

### Aave V3 Adapter

**Purpose**: Lending/borrowing protocol integration

**Location**: `src/app/infrastructure/adapters/external/aave_adapter.py`

**Capabilities**:
- Get market data (supply/borrow rates)
- Monitor user positions
- Calculate health factors
- Track protocol TVL and stats

**Example Usage**:
```python
from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

# Uses fallback data when API unavailable
adapter = AaveAdapter(api_key="your_api_key", cache=cache)

# Get markets
markets = await adapter.get_markets(chain="ethereum")

# Get user position
position = await adapter.get_position(
    wallet_address="0x...",
    chain="ethereum",
)
```

### Axelar Bridge Adapter

**Purpose**: Cross-chain bridging via Axelar Network

**Location**: `src/app/infrastructure/adapters/external/axelar_adapter.py`

**Capabilities**:
- Get available bridge routes
- Estimate transfer costs and time
- Track transfer status
- Get supported chains

**Example Usage**:
```python
from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

adapter = AxelarAdapter(client=client, cache=cache)

# Get routes
routes = await adapter.get_routes(
    source_chain="ethereum",
    dest_chain="polygon",
)

# Estimate transfer
estimate = await adapter.estimate_transfer(
    source_chain="ethereum",
    dest_chain="polygon",
    asset="USDC",
    amount=Decimal("1000"),
)
```

### LayerZero Adapter

**Purpose**: Cross-chain messaging via LayerZero Protocol

**Location**: `src/app/infrastructure/adapters/external/layerzero_adapter.py`

**Capabilities**:
- Get supported chains
- Estimate message fees
- Track cross-chain messages
- Monitor OFT (Omnichain Fungible Token) transfers

**Example Usage**:
```python
from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter

adapter = LayerZeroAdapter(client=client, cache=cache)

# Estimate fees
fees = await adapter.estimate_fees(
    source_chain_id=1,  # Ethereum
    dest_chain_id=137,  # Polygon
    payload_size=256,
)

# Track message
message = await adapter.track_message(tx_hash="0x...")
```

### Hyperliquid Adapter

**Purpose**: Perpetual futures trading

**Location**: `src/app/infrastructure/adapters/external/hyperliquid_adapter.py`

**Capabilities**:
- Get perpetual markets
- Fetch funding rates
- Get order book depth
- Monitor user positions

### Morpho Adapter

**Purpose**: Optimized lending aggregation

**Location**: `src/app/infrastructure/adapters/external/morpho_adapter.py`

**Capabilities**:
- Get vault APYs
- Monitor vaults
- Track user positions

### OpenSea Adapter

**Purpose**: NFT marketplace integration

**Location**: `src/app/infrastructure/adapters/external/opensea_adapter.py`

**Capabilities**:
- Get NFTs by owner
- Get collection stats
- Get floor prices
- Get active listings

## Implementation Pattern

### Adapter Structure

```python
"""
Protocol Adapter Template.

Implements the ProtocolGateway port using the ProtocolClient
with caching support via ExternalAPICache.
"""

from decimal import Decimal
from typing import List, Optional

from app.domain.ports.protocol_gateway import ProtocolGateway
from app.domain.entities.protocol.entity import Entity
from app.domain.value_objects.protocol.value_object import ValueObject
from app.domain.exceptions.protocol import ProtocolAPIError
from app.infrastructure.cache.external_api_cache import ExternalAPICache

import logging

logger = logging.getLogger(__name__)


class ProtocolAdapter(ProtocolGateway):
    """
    Protocol implementation of ProtocolGateway.

    Handles:
    - Data transformation from client models to domain entities
    - Caching with configurable TTLs
    - Error mapping from API errors to domain exceptions
    """

    DEFAULT_CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        client: ProtocolClient,
        cache: ExternalAPICache,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        self._client = client
        self._cache = cache
        self._cache_ttl = cache_ttl

    async def get_data(self, param: str) -> List[Entity]:
        """
        Get data with caching.
        
        Args:
            param: Query parameter
            
        Returns:
            List of domain entities
            
        Raises:
            ProtocolAPIError: If API call fails
        """
        cache_key = f"protocol:data:{param}"
        
        # Try cache first
        cached = await self._cache.get(cache_key)
        if cached:
            return self._transform_to_entities(cached)
        
        try:
            # Call client
            response = await self._client.get_data(param)
            
            # Cache response
            await self._cache.set(cache_key, response, ttl=self._cache_ttl)
            
            # Transform to domain entities
            return self._transform_to_entities(response)
            
        except Exception as e:
            logger.error(f"Protocol API error: {e}")
            raise ProtocolAPIError(f"Failed to fetch data: {e}") from e

    def _transform_to_entities(self, data: List[dict]) -> List[Entity]:
        """Transform API response to domain entities."""
        return [
            Entity(
                id=item["id"],
                name=item["name"],
                # ... map other fields
            )
            for item in data
        ]
```

### Client Structure

```python
"""
Protocol API Client - Stub/Full implementation.

Provides access to Protocol APIs.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
import httpx


@dataclass
class ApiResponse:
    """API response data structure."""
    field1: str
    field2: Decimal
    # ... other fields


class ProtocolClient:
    """
    Protocol API client.
    
    Provides access to protocol data and operations.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.protocol.io",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        headers = {}
        if api_key:
            headers["X-API-KEY"] = api_key
        self.client = httpx.AsyncClient(timeout=timeout, headers=headers)
    
    async def get_data(self, param: str) -> List[ApiResponse]:
        """Get data from API."""
        response = await self.client.get(
            f"{self.base_url}/data",
            params={"param": param},
        )
        response.raise_for_status()
        return [ApiResponse(**item) for item in response.json()]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

## Testing Strategy

### Unit Tests

Unit tests mock the client and cache:

```python
"""
Unit tests for Protocol adapter.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_client():
    """Create a mocked ProtocolClient."""
    client = MagicMock()
    client.get_data = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestProtocolAdapterStructure:
    """Tests for adapter structure and protocol compliance."""

    def test_adapter_imports(self):
        """Test adapter can be imported."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        assert ProtocolAdapter is not None

    def test_adapter_implements_gateway(self):
        """Test adapter implements gateway protocol."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        from app.domain.ports.protocol_gateway import ProtocolGateway
        
        assert hasattr(ProtocolAdapter, 'get_data')

    def test_adapter_init(self, mock_client, mock_cache):
        """Test adapter initialization."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        
        adapter = ProtocolAdapter(client=mock_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestProtocolAdapterGetData:
    """Tests for get_data method."""

    @pytest.mark.asyncio
    async def test_get_data_calls_client(self, mock_client, mock_cache):
        """Test get_data calls the client."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        
        mock_client.get_data.return_value = []
        adapter = ProtocolAdapter(client=mock_client, cache=mock_cache)
        
        await adapter.get_data("test")
        
        mock_client.get_data.assert_called()

    @pytest.mark.asyncio
    async def test_get_data_uses_cache(self, mock_client, mock_cache):
        """Test get_data uses cache when available."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        
        mock_cache.get.return_value = [{"id": "1", "name": "cached"}]
        adapter = ProtocolAdapter(client=mock_client, cache=mock_cache)
        
        result = await adapter.get_data("test")
        
        mock_client.get_data.assert_not_called()
        assert len(result) > 0
```

### Integration Tests

Integration tests verify the full adapter flow:

```python
"""
Integration tests for Protocol adapter.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.integration
class TestProtocolAdapterIntegration:
    """Integration tests for Protocol adapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mock dependencies."""
        from app.infrastructure.adapters.external.protocol_adapter import ProtocolAdapter
        from app.infrastructure.adapters.external.protocol_client import ProtocolClient
        
        client = MagicMock(spec=ProtocolClient)
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        
        return ProtocolAdapter(client=client, cache=cache)

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, adapter):
        """Test complete data retrieval flow."""
        adapter._client.get_data = AsyncMock(return_value=[
            {"id": "1", "name": "Test"},
        ])
        
        result = await adapter.get_data("param")
        
        assert len(result) == 1
        assert result[0].id == "1"
```

## Adding New Adapters

### Step 1: Define Domain Port

Create the gateway interface in `src/app/domain/ports/`:

```python
# src/app/domain/ports/new_protocol_gateway.py
from typing import Protocol, List
from app.domain.entities.new_protocol.entity import Entity


class NewProtocolGateway(Protocol):
    """Port for New Protocol integration."""
    
    async def get_data(self, param: str) -> List[Entity]: ...
    async def get_stats(self) -> dict: ...
```

### Step 2: Create Client

Create the API client in `src/app/infrastructure/adapters/external/`:

```python
# src/app/infrastructure/adapters/external/new_protocol_client.py
# Follow the client template above
```

### Step 3: Implement Adapter

Create the adapter in `src/app/infrastructure/adapters/external/`:

```python
# src/app/infrastructure/adapters/external/new_protocol_adapter.py
# Follow the adapter template above
```

### Step 4: Register in DI Container

Add provider in `src/app/setup/ioc/`:

```python
# src/app/setup/ioc/new_protocol.py
from dishka import Provider, provide, Scope

from app.domain.ports.new_protocol_gateway import NewProtocolGateway
from app.infrastructure.adapters.external.new_protocol_adapter import NewProtocolAdapter
from app.infrastructure.adapters.external.new_protocol_client import NewProtocolClient


class NewProtocolProvider(Provider):
    """DI provider for New Protocol integration."""

    @provide(scope=Scope.APP)
    def provide_client(self, settings: AppSettings) -> NewProtocolClient:
        return NewProtocolClient(api_key=settings.integrations.new_protocol_api_key)

    @provide(scope=Scope.APP)
    def provide_gateway(
        self,
        client: NewProtocolClient,
        cache: ExternalAPICache,
    ) -> NewProtocolGateway:
        return NewProtocolAdapter(client=client, cache=cache)
```

### Step 5: Add Tests

Create test files:
- `tests/unit/infrastructure/adapters/test_new_protocol_adapter.py`
- `tests/integration/defi/test_new_protocol_integration.py`

### Step 6: Update Documentation

Update this guide with the new adapter information.

---

## Reference

### Configuration

DeFi adapter settings are in `config/local/config.toml`:

```toml
[integrations]
# API keys for DeFi protocols
curve_api_key = ""
aave_api_key = ""
thegraph_api_key = ""
opensea_api_key = ""
```

### Error Codes

| Code | Description |
|------|-------------|
| `DEFI_001` | Protocol API unavailable |
| `DEFI_002` | Invalid request parameters |
| `DEFI_003` | Rate limit exceeded |
| `DEFI_004` | Authentication failed |

### Cache TTLs

| Data Type | Default TTL |
|-----------|-------------|
| Pool data | 5 minutes |
| APY data | 1 minute |
| Market data | 2 minutes |
| User positions | 30 seconds |
| Static data | 1 hour |
