# Plan de Implementación - Integraciones DeFi/NFT

## Resumen Ejecutivo

Este plan organiza la implementación de 6 integraciones siguiendo el orden de prioridad establecido:
- **Alta Prioridad**: Core DeFi (Curve, Hyperliquid, Morpho)
- **Media Prioridad**: Cross-chain (LayerZero, Axelar)
- **Baja Prioridad**: NFTs (OpenSea)

**Total estimado**: 92 tasks, ~117 archivos, ~15-20 días de desarrollo

---

## 🔴 FASE 1: Alta Prioridad - Core DeFi

### Sprint 1.1: Curve Finance (3-4 días)
**Objetivo**: Completar stack de DEXs para stablecoins

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | CurveGateway port | `domain/ports/curve_gateway.py` | - |
| 1.2 | Pool entity + VOs | `domain/entities/curve/`, `domain/value_objects/curve/` | - |
| 1.3 | Gauge entity | `domain/entities/curve/gauge.py` | 1.2 |
| 2.1 | Curve exceptions | `domain/exceptions/curve.py` | - |
| 3.1 | CurveAdapter | `infrastructure/adapters/external/curve_adapter.py` | 1.1, 1.2, 1.3 |
| 4.1-4.4 | Queries (GetPools, GetPoolAPY, GetGauges, GetTVL) | `application/queries/curve/` | 3.1 |
| 5.1 | GetSwapQuote command | `application/commands/curve/` | 3.1 |
| 6.1-6.2 | HTTP Router + Schemas | `presentation/http/controllers/defi/curve_*` | 4.x, 5.1 |
| 7.1-7.2 | DI Provider + Registration | `setup/ioc/curve.py` | 6.x |
| 8.1 | Configuration | `config/local/config.toml` | - |
| 9.1-9.2 | Tests | `tests/` | All |

**Entregables**:
- `GET /api/v1/defi/curve/pools` - Lista de pools con TVL/APY
- `GET /api/v1/defi/curve/pools/{address}` - Detalle de pool
- `GET /api/v1/defi/curve/pools/{address}/apy` - APY breakdown
- `POST /api/v1/defi/curve/quote` - Swap quotes
- `GET /api/v1/defi/curve/gauges` - Gauge rewards
- `GET /api/v1/defi/curve/tvl` - TVL analytics

---

### Sprint 1.2: Hyperliquid (4-5 días)
**Objetivo**: Añadir derivados/perpetuos al Trading Agent

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | PerpetualGateway port | `domain/ports/perpetual_gateway.py` | - |
| 1.2-1.4 | Market, Position, Liquidation entities | `domain/entities/perpetual/` | - |
| 1.5 | FundingRate, OrderBook, RiskMetrics VOs | `domain/value_objects/perpetual/` | - |
| 2.1 | Perpetual exceptions | `domain/exceptions/perpetual.py` | - |
| 3.1 | HyperliquidAdapter | `infrastructure/adapters/external/hyperliquid_adapter.py` | 1.x |
| 4.1-4.5 | Queries (Markets, OrderBook, Funding, Liquidations, Positions) | `application/queries/perpetual/` | 3.1 |
| 5.1 | CalculateRisk command | `application/commands/perpetual/` | 3.1 |
| 6.1-6.2 | HTTP Router + Schemas | `presentation/http/controllers/defi/hyperliquid_*` | 4.x, 5.1 |
| 7.1-7.2 | DI Provider + Registration | `setup/ioc/hyperliquid.py` | 6.x |
| 8.1 | Configuration | `config/local/config.toml` | - |
| 9.1-9.2 | Tests | `tests/` | All |

**Entregables**:
- `GET /api/v1/defi/hyperliquid/markets` - Perpetual markets
- `GET /api/v1/defi/hyperliquid/markets/{symbol}/orderbook` - Order book
- `GET /api/v1/defi/hyperliquid/funding` - Funding rates + opportunities
- `GET /api/v1/defi/hyperliquid/liquidations` - Liquidation events
- `GET /api/v1/defi/hyperliquid/positions/{address}` - User positions
- `POST /api/v1/defi/hyperliquid/risk/calculate` - Risk calculator

---

### Sprint 1.3: Morpho Protocol (5-6 días)
**Objetivo**: Vaults de lending con yield optimization

⚠️ **Nota**: Requiere crear MorphoClient nuevo (GraphQL/Subgraph)

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | MorphoGateway port | `domain/ports/morpho_gateway.py` | - |
| 1.2-1.4 | Vault, Market, Position entities | `domain/entities/lending/` | - |
| 1.5 | VaultAPY, RiskTier, MarketAllocation VOs | `domain/value_objects/lending/` | - |
| 2.1 | Morpho exceptions | `domain/exceptions/morpho.py` | - |
| **3.1** | **MorphoClient (NEW)** | `infrastructure/adapters/external/morpho_client.py` | - |
| 4.1 | MorphoAdapter | `infrastructure/adapters/external/morpho_adapter.py` | 3.1, 1.x |
| 5.1-5.6 | Queries (Vaults, Details, APY, Markets, Positions, CompareYields) | `application/queries/morpho/` | 4.1 |
| 6.1-6.2 | HTTP Router + Schemas | `presentation/http/controllers/defi/morpho_*` | 5.x |
| 7.1-7.2 | DI Provider + Registration | `setup/ioc/morpho.py` | 6.x |
| 8.1 | Configuration | `config/local/config.toml` | - |
| 9.1-9.3 | Tests (Client + Adapter + Integration) | `tests/` | All |

**Entregables**:
- `GET /api/v1/defi/morpho/vaults` - Vaults con yield + top opportunities
- `GET /api/v1/defi/morpho/vaults/{address}` - Vault details + allocations
- `GET /api/v1/defi/morpho/vaults/{address}/apy` - APY breakdown
- `GET /api/v1/defi/morpho/markets` - Morpho Blue markets
- `GET /api/v1/defi/morpho/positions/{user}` - User positions + earnings
- `GET /api/v1/defi/morpho/compare` - Yield comparison cross-protocol

---

## 🟡 FASE 2: Media Prioridad - Cross-chain

### Sprint 2.1: LayerZero (3-4 días)
**Objetivo**: Cross-chain message tracking (complementa LI.FI)

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | LayerZeroGateway port | `domain/ports/layerzero_gateway.py` | - |
| 1.2-1.3 | LZMessage, OFTTransfer entities | `domain/entities/cross_chain/` | - |
| 1.4 | MessageStatus, LZChain, MessageFee VOs | `domain/value_objects/cross_chain/` | - |
| 2.1 | LayerZero exceptions | `domain/exceptions/layerzero.py` | - |
| 3.1 | LayerZeroAdapter | `infrastructure/adapters/external/layerzero_adapter.py` | 1.x |
| 4.1-4.5 | Queries (TrackMessage, History, Chains, Fees, OFT) | `application/queries/layerzero/` | 3.1 |
| 5.1-5.2 | HTTP Router + Schemas | `presentation/http/controllers/defi/layerzero_*` | 4.x |
| 6.1-6.2 | DI Provider + Registration | `setup/ioc/layerzero.py` | 5.x |
| 7.1 | Configuration | `config/local/config.toml` | - |
| 8.1-8.2 | Tests | `tests/` | All |

**Entregables**:
- `GET /api/v1/defi/layerzero/message/{tx_hash}` - Track message status
- `GET /api/v1/defi/layerzero/messages/{address}` - Message history
- `GET /api/v1/defi/layerzero/chains` - Supported chains
- `GET /api/v1/defi/layerzero/fees/estimate` - Fee estimation
- `GET /api/v1/defi/layerzero/oft/{address}` - OFT transfers

---

### Sprint 2.2: Axelar Network (3-4 días)
**Objetivo**: Cross-chain bridging avanzado con GMP

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | AxelarGateway port | `domain/ports/axelar_gateway.py` | - |
| 1.2 | AxelarTransfer entity | `domain/entities/bridge/` | - |
| 1.3 | TransferStatus, BridgeRoute, TransferEstimate VOs | `domain/value_objects/bridge/` | - |
| 2.1 | Axelar exceptions | `domain/exceptions/axelar.py` | - |
| 3.1 | AxelarAdapter (+ express service) | `infrastructure/adapters/external/axelar_adapter.py` | 1.x |
| 4.1-4.5 | Queries (Routes, Estimate, Track, Chains, Tokens) | `application/queries/axelar/` | 3.1 |
| 5.1-5.2 | HTTP Router + Schemas | `presentation/http/controllers/defi/axelar_*` | 4.x |
| 6.1-6.2 | DI Provider + Registration | `setup/ioc/axelar.py` | 5.x |
| 7.1 | Configuration | `config/local/config.toml` | - |
| 8.1-8.2 | Tests | `tests/` | All |

**Entregables**:
- `GET /api/v1/defi/axelar/routes` - Bridge routes (standard + express)
- `GET /api/v1/defi/axelar/estimate` - Transfer estimate + recommendation
- `GET /api/v1/defi/axelar/transfer/{tx_hash}` - Track transfer
- `GET /api/v1/defi/axelar/chains` - Supported chains
- `GET /api/v1/defi/axelar/tokens/{chain}` - Supported tokens

---

## 🟢 FASE 3: Baja Prioridad - NFTs

### Sprint 3.1: OpenSea (3-4 días)
**Objetivo**: Expandir a vertical NFT

| Task ID | Descripción | Archivos | Dependencias |
|---------|-------------|----------|--------------|
| 1.1 | NFTMarketplaceGateway port | `domain/ports/nft_marketplace_gateway.py` | - |
| 1.2-1.3 | NFTAsset, NFTCollection entities | `domain/entities/nft/` | - |
| 1.4 | CollectionStats, NFTTrait, NFTListing VOs | `domain/value_objects/nft/` | - |
| 2.1 | NFT exceptions | `domain/exceptions/nft.py` | - |
| 3.1 | OpenSeaAdapter | `infrastructure/adapters/external/opensea_adapter.py` | 1.x |
| 4.1-4.5 | Queries (Portfolio, Collection, Stats, Details, Listings) | `application/queries/nft/` | 3.1 |
| 5.1-5.2 | HTTP Router + Schemas | `presentation/http/controllers/nft/opensea_*` | 4.x |
| 6.1-6.2 | DI Provider + Registration | `setup/ioc/opensea.py` | 5.x |
| 7.1 | Configuration | `config/local/config.toml` | - |
| 8.1-8.2 | Tests | `tests/` | All |

**Entregables**:
- `GET /api/v1/nft/portfolio/{address}` - NFT portfolio + valuation
- `GET /api/v1/nft/collections/{slug}` - Collection info
- `GET /api/v1/nft/collections/{slug}/stats` - Market stats + sentiment
- `GET /api/v1/nft/assets/{contract}/{token_id}` - NFT details
- `GET /api/v1/nft/collections/{slug}/listings` - Active listings
- `GET /api/v1/nft/collections/{slug}/floor` - Floor price

---

## 📅 Timeline Estimado

```
Semana 1-2: FASE 1 - Alta Prioridad
├── Sprint 1.1: Curve Finance        [Días 1-4]
├── Sprint 1.2: Hyperliquid          [Días 5-9]
└── Sprint 1.3: Morpho Protocol      [Días 10-15]

Semana 3: FASE 2 - Media Prioridad
├── Sprint 2.1: LayerZero            [Días 16-19]
└── Sprint 2.2: Axelar Network       [Días 20-23]

Semana 4: FASE 3 - Baja Prioridad
└── Sprint 3.1: OpenSea              [Días 24-27]

Buffer/QA:                            [Días 28-30]
```

---

## 📊 Métricas por Fase

| Fase | Integraciones | Tasks | Archivos | Endpoints |
|------|---------------|-------|----------|-----------|
| **Alta** | Curve, Hyperliquid, Morpho | 50 | ~61 | 18 |
| **Media** | LayerZero, Axelar | 28 | ~37 | 10 |
| **Baja** | OpenSea | 14 | ~19 | 6 |
| **Total** | 6 | **92** | **~117** | **34** |

---

## 🔄 Orden de Ejecución por Sprint

### Patrón de Implementación (cada sprint):

```
1. Domain Layer (Día 1)
   ├── Port interface
   ├── Entities
   ├── Value Objects
   └── Exceptions

2. Infrastructure Layer (Día 2)
   └── Adapter (+ Client si es nuevo)

3. Application Layer (Día 2-3)
   ├── Queries
   └── Commands

4. Presentation Layer (Día 3)
   ├── HTTP Router
   └── Pydantic Schemas

5. Setup & Config (Día 3-4)
   ├── DI Provider
   ├── App Factory registration
   └── TOML configuration

6. Testing (Día 4)
   ├── Unit tests
   └── Integration tests
```

---

## ✅ Checklist de Progreso

### FASE 1: Alta Prioridad
- [ ] **Curve Finance**
  - [ ] Domain Layer (1.1-1.3, 2.1)
  - [ ] Infrastructure Layer (3.1)
  - [ ] Application Layer (4.1-4.4, 5.1)
  - [ ] Presentation Layer (6.1-6.2)
  - [ ] Setup & Config (7.1-7.2, 8.1)
  - [ ] Testing (9.1-9.2)

- [ ] **Hyperliquid**
  - [ ] Domain Layer (1.1-1.5, 2.1)
  - [ ] Infrastructure Layer (3.1)
  - [ ] Application Layer (4.1-4.5, 5.1)
  - [ ] Presentation Layer (6.1-6.2)
  - [ ] Setup & Config (7.1-7.2, 8.1)
  - [ ] Testing (9.1-9.2)

- [ ] **Morpho Protocol**
  - [ ] Domain Layer (1.1-1.5, 2.1)
  - [ ] Infrastructure Layer - Client (3.1)
  - [ ] Infrastructure Layer - Adapter (4.1)
  - [ ] Application Layer (5.1-5.6)
  - [ ] Presentation Layer (6.1-6.2)
  - [ ] Setup & Config (7.1-7.2, 8.1)
  - [ ] Testing (9.1-9.3)

### FASE 2: Media Prioridad
- [ ] **LayerZero**
  - [ ] Domain Layer (1.1-1.4, 2.1)
  - [ ] Infrastructure Layer (3.1)
  - [ ] Application Layer (4.1-4.5)
  - [ ] Presentation Layer (5.1-5.2)
  - [ ] Setup & Config (6.1-6.2, 7.1)
  - [ ] Testing (8.1-8.2)

- [ ] **Axelar Network**
  - [ ] Domain Layer (1.1-1.3, 2.1)
  - [ ] Infrastructure Layer (3.1)
  - [ ] Application Layer (4.1-4.5)
  - [ ] Presentation Layer (5.1-5.2)
  - [ ] Setup & Config (6.1-6.2, 7.1)
  - [ ] Testing (8.1-8.2)

### FASE 3: Baja Prioridad
- [ ] **OpenSea**
  - [ ] Domain Layer (1.1-1.4, 2.1)
  - [ ] Infrastructure Layer (3.1)
  - [ ] Application Layer (4.1-4.5)
  - [ ] Presentation Layer (5.1-5.2)
  - [ ] Setup & Config (6.1-6.2, 7.1)
  - [ ] Testing (8.1-8.2)

---

## 🚀 Comenzar Implementación

Para iniciar la implementación, ejecutar las tareas del primer sprint (Curve Finance) en orden:

```bash
# Ver tareas pendientes
cat .spec-workflow/specs/curve-integration/tasks.md

# Implementar Task 1.1 primero
# Cada task incluye un _Prompt detallado para guiar la implementación
```

**Próximo paso**: ¿Comenzar implementación de Sprint 1.1 (Curve Finance)?
