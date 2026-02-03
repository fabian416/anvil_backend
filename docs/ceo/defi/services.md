# DeFi Operations Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The DeFi Operations module follows hexagonal architecture with:
- **Domain Ports (Gateways)**: Protocol interfaces for external DeFi integrations
- **Infrastructure Adapters**: Implementations connecting to real DeFi protocols
- **Application Queries/Commands**: CQRS pattern for data fetching and calculations
- **Data Providers**: CoinGecko, DeFiLlama, 1inch, Hyperliquid

**Total Service Components**: 50+ Python modules across 6 protocols

---

## 1. Domain Ports (Gateway Interfaces)

### 1.1 AaveGateway
**Path**: `src/app/domain/ports/aave_gateway.py`

```python
class AaveGateway(Protocol):
    async def get_markets(self, asset: str | None, chain: str) -> list[AaveMarket]
    async def get_market_details(self, asset: str, chain: str) -> AaveMarket
    async def get_user_position(self, address: str, chain: str) -> AavePosition
    async def get_health_factor(self, address: str, chain: str) -> HealthFactor
    async def get_available_to_borrow(self, address: str, asset: str, chain: str) -> Decimal
    async def get_protocol_stats(self, chain: str) -> dict
    async def get_supply_apy(self, asset: str, chain: str) -> Decimal
    async def get_borrow_apy(self, asset: str, chain: str, rate_type: str) -> Decimal
    async def get_liquidation_threshold(self, asset: str, chain: str) -> Decimal
    async def calculate_health_factor(
        self, collateral_usd: Decimal, debt_usd: Decimal, liquidation_threshold: Decimal
    ) -> HealthFactor
```

---

### 1.2 MorphoGateway
**Path**: `src/app/domain/ports/morpho_gateway.py`

```python
class MorphoGateway(Protocol):
    async def get_vaults(self, request: GetVaultsRequest) -> GetVaultsResponse
    async def get_vault_details(self, vault_address: str, chain: str) -> MorphoVault
    async def get_vault_apy(self, vault_address: str, chain: str) -> VaultAPYResponse
    async def get_markets(self, request: GetMarketsRequest) -> list[MorphoMarket]
    async def get_user_positions(self, address: str, chain: str) -> UserPositionsResponse
    async def compare_yields(self, asset: str, protocols: list[str], chain: str) -> YieldComparison
```

---

### 1.3 PerpetualGateway
**Path**: `src/app/domain/ports/perpetual_gateway.py`

```python
class PerpetualGateway(Protocol):
    async def get_markets(self, sort_by: str, limit: int) -> list[PerpMarket]
    async def get_order_book(self, symbol: str, depth: int) -> OrderBook
    async def get_funding_rates(self, sort_by: str, min_rate: float | None) -> FundingRatesResponse
    async def get_liquidations(self, symbol: str | None, hours: int, sort_by: str) -> LiquidationsResponse
    async def get_positions(self, address: str) -> PositionsResponse
    async def calculate_risk(self, request: CalculateRiskRequest) -> RiskMetrics
```

---

### 1.4 CurveGateway
**Path**: `src/app/domain/ports/curve_gateway.py`

```python
class CurveGateway(Protocol):
    async def get_pools(self, chain: str, sort_by: str, limit: int, min_tvl: float | None) -> list[Pool]
    async def get_pool_apy(self, pool_address: str, chain: str) -> PoolAPY
    async def get_swap_quote(self, from_token: str, to_token: str, amount: str, chain: str) -> SwapQuote
    async def get_gauges(self, chain: str, sort_by: str, min_apy: float | None) -> list[Gauge]
    async def get_tvl(self, chain: str) -> TVLData
```

---

### 1.5 LayerZeroGateway
**Path**: `src/app/domain/ports/layerzero_gateway.py`

```python
class LayerZeroGateway(Protocol):
    async def track_message(self, tx_hash: str) -> MessageTrackingResponse
    async def get_message_history(self, address: str, limit: int, status_filter: str | None) -> MessageHistoryResponse
    async def get_chains(self) -> ChainsResponse
    async def estimate_fees(self, source: str, destination: str, payload_size: int) -> MessageFee
    async def get_oft_transfers(self, address: str, limit: int) -> OFTTransfersResponse
```

---

### 1.6 AxelarGateway
**Path**: `src/app/domain/ports/axelar_gateway.py`

```python
class AxelarGateway(Protocol):
    async def get_routes(self, source: str, destination: str, token: str) -> list[BridgeRoute]
    async def estimate_transfer(self, request: EstimateTransferRequest) -> TransferEstimateResponse
    async def track_transfer(self, tx_hash: str) -> TransferTrackingResponse
    async def get_chains(self) -> ChainsResponse
    async def get_tokens(self, chain: str) -> TokensResponse
```

---

## 2. Infrastructure Adapters

### 2.1 AaveAdapter
**Path**: `src/app/infrastructure/adapters/external/aave_adapter.py`

Implements `AaveGateway` using Aave V3 subgraph and on-chain data.

**Dependencies**:
- Redis cache for market data
- TheGraph for historical data

---

### 2.2 MorphoAdapter
**Path**: `src/app/infrastructure/adapters/external/morpho_adapter.py`

Implements `MorphoGateway` using Morpho Blue API.

**Features**:
- MetaMorpho vault aggregation
- Multi-chain support (Ethereum, Base)

---

### 2.3 HyperliquidAdapter
**Path**: `src/app/infrastructure/adapters/external/hyperliquid_adapter.py`

Implements `PerpetualGateway` for Hyperliquid.

**API Integration**:
- REST API for market data
- WebSocket for real-time orderbook

---

### 2.4 CurveAdapter
**Path**: `src/app/infrastructure/adapters/external/curve_adapter.py`

Implements `CurveGateway` using Curve API.

---

### 2.5 LayerZeroAdapter
**Path**: `src/app/infrastructure/adapters/external/layerzero_adapter.py`

Implements `LayerZeroGateway` for cross-chain messaging.

---

### 2.6 AxelarAdapter
**Path**: `src/app/infrastructure/adapters/external/axelar_adapter.py`

Implements `AxelarGateway` for bridge operations.

---

## 3. Application Queries & Commands

### 3.1 Morpho Queries
**Path**: `src/app/application/queries/morpho/`

| Query | Description |
|-------|-------------|
| `GetVaults` | List MetaMorpho vaults |
| `GetVaultDetails` | Get vault with allocations |
| `GetVaultAPY` | APY breakdown |
| `GetMarkets` | Morpho Blue markets |
| `GetUserPositions` | User vault positions |
| `CompareYields` | Cross-protocol comparison |

---

### 3.2 Hyperliquid Queries & Commands
**Path**: `src/app/application/queries/perpetual/`, `src/app/application/commands/perpetual/`

| Query/Command | Description |
|---------------|-------------|
| `GetMarkets` | Perpetual markets |
| `GetOrderBook` | Order book depth |
| `GetFundingRates` | Funding with opportunities |
| `GetLiquidations` | Recent liquidations |
| `GetPositions` | User positions |
| `CalculateRisk` | Position risk calculation |

---

### 3.3 Curve Queries & Commands
**Path**: `src/app/application/queries/curve/`, `src/app/application/commands/curve/`

| Query/Command | Description |
|---------------|-------------|
| `GetPools` | Curve pools |
| `GetPoolAPY` | APY breakdown |
| `GetGauges` | Gauge rewards |
| `GetTVL` | Total value locked |
| `GetSwapQuote` | Swap quote with impact |

---

### 3.4 LayerZero Queries
**Path**: `src/app/application/queries/layerzero/`

| Query | Description |
|-------|-------------|
| `TrackMessage` | Message status |
| `GetMessageHistory` | Address history |
| `GetChains` | Supported chains |
| `EstimateFees` | Fee estimation |
| `GetOFTTransfers` | OFT transfers |

---

### 3.5 Axelar Queries
**Path**: `src/app/application/queries/axelar/`

| Query | Description |
|-------|-------------|
| `GetRoutes` | Bridge routes |
| `EstimateTransfer` | Cost estimation |
| `TrackTransfer` | Transfer status |
| `GetChains` | Supported chains |
| `GetTokens` | Chain tokens |

---

## 4. Data Providers

### 4.1 CoinGecko Provider
**Path**: `src/app/infrastructure/defi/providers/coingecko.py`

```python
class CoinGeckoClient:
    async def get_price(self, token_ids: list[str], vs_currencies: list[str]) -> dict
    async def get_token_info(self, token_id: str) -> dict
    async def get_market_chart(self, token_id: str, days: int) -> dict
    async def get_ohlcv(self, token_id: str, days: int) -> list
```

---

### 4.2 DeFiLlama Provider
**Path**: `src/app/infrastructure/defi/providers/defillama.py`

```python
class DefiLlamaClient:
    async def get_protocol_tvl(self, protocol: str) -> dict
    async def get_chain_tvl(self, chain: str) -> dict
    async def get_yields(self, pool_id: str) -> dict
    async def get_stablecoins(self) -> list
```

---

### 4.3 1inch Provider
**Path**: `src/app/infrastructure/defi/providers/oneinch.py`

```python
class OneInchClient:
    async def get_quote(self, src: str, dst: str, amount: str) -> dict
    async def get_swap_data(self, src: str, dst: str, amount: str, from_address: str) -> dict
    async def get_tokens(self, chain_id: int) -> dict
    async def get_protocols(self, chain_id: int) -> list
```

---

### 4.4 Hyperliquid Provider
**Path**: `src/app/infrastructure/defi/providers/hyperliquid.py`

```python
class HyperliquidClient:
    async def get_spot_quote(self, from_token: str, to_token: str, amount: float) -> SpotQuote
    async def get_market_data(self) -> dict
    async def get_orderbook(self, symbol: str) -> dict
    async def get_funding_rates(self) -> list
    async def get_user_positions(self, address: str) -> list
```

---

## 5. DeFi Tools (Agent Integration)

### 5.1 Swap Tools
**Path**: `src/app/infrastructure/defi/tools/swap_tools.py`

```python
async def get_swap_quote_tool(src_token, dst_token, amount, oneinch_client) -> str
async def explain_swap_tool(src_token, dst_token) -> str
async def get_token_info_tool(token, oneinch_client) -> str
```

---

### 5.2 Trading Tools
**Path**: `src/app/infrastructure/defi/tools/trading_tools.py`

Agent tools for perpetual trading analysis.

---

### 5.3 Portfolio Tools
**Path**: `src/app/infrastructure/defi/tools/portfolio_tools.py`

Tools for portfolio analysis and tracking.

---

### 5.4 Position Management Tools
**Path**: `src/app/infrastructure/defi/tools/position_management_tools.py`

Tools for managing DeFi positions.

---

### 5.5 Advanced Swap Tools
**Path**: `src/app/infrastructure/defi/tools/advanced_swap_tools.py`

Advanced swap routing and optimization.

---

## 6. Template Library

### 6.1 APR/APY Calculator
**Path**: `src/app/application/templates/library/defi/apr_apy_calculator.py`

Template for yield calculations.

---

### 6.2 Liquidity Analysis
**Path**: `src/app/application/templates/library/defi/liquidity_analysis.py`

Template for liquidity pool analysis.

---

### 6.3 Risk vs Reward Comparison
**Path**: `src/app/application/templates/library/defi/risk_vs_reward_comparison.py`

Template for risk-adjusted returns.

---

### 6.4 Protocol Deep Dive
**Path**: `src/app/application/templates/library/defi/protocol_deep_dive.py`

Template for protocol analysis.

---

### 6.5 Smart Contract Security
**Path**: `src/app/application/templates/library/defi/smart_contract_security_analysis.py`

Template for security analysis.

---

## 7. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │AaveRouter  │ │MorphoRouter│ │HyperliquidR│ │CurveRouter │ │LayerZero/  ││
│  │            │ │            │ │            │ │            │ │Axelar      ││
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘│
└────────┼──────────────┼──────────────┼──────────────┼──────────────┼────────┘
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Queries & Commands                                │  │
│  │                                                                        │  │
│  │  GetMarkets • GetPositions • GetVaults • TrackMessage • EstimateFee  │  │
│  │  CalculateRisk • GetSwapQuote • CompareYields • GetFundingRates     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Gateway Ports (Protocols)                          │  │
│  │                                                                        │  │
│  │  AaveGateway • MorphoGateway • PerpetualGateway • CurveGateway       │  │
│  │  LayerZeroGateway • AxelarGateway                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Entities & Value Objects                           │  │
│  │                                                                        │  │
│  │  AaveMarket • AavePosition • HealthFactor • RiskLevel                │  │
│  │  MorphoVault • MorphoMarket • VaultAPY • RiskTier                    │  │
│  │  PerpMarket • Position • FundingRate • OrderBook • RiskMetrics       │  │
│  │  Pool • Gauge • PoolAPY • SwapQuote • TVLData                        │  │
│  │  LZMessage • OFTTransfer • MessageStatus • MessageFee                │  │
│  │  AxelarTransfer • BridgeRoute • TransferEstimate                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Adapters                                      │  │
│  │                                                                        │  │
│  │  AaveAdapter • MorphoAdapter • HyperliquidAdapter • CurveAdapter     │  │
│  │  LayerZeroAdapter • AxelarAdapter                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Data Providers                                  │  │
│  │                                                                        │  │
│  │  CoinGeckoClient • DefiLlamaClient • OneInchClient • HyperliquidClient│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Agent Tools                                      │  │
│  │                                                                        │  │
│  │  SwapTools • TradingTools • PortfolioTools • PositionMgmtTools       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                      │
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │  Aave V3 │ │  Morpho  │ │Hyperliquid│ │  Curve   │ │LayerZero │         │
│  │ Subgraph │ │ Blue API │ │   API    │ │   API    │ │   API    │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │  Axelar  │ │CoinGecko │ │DeFiLlama │ │  1inch   │                       │
│  │   API    │ │   API    │ │   API    │ │   API    │                       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. IoC Providers

### 8.1 AaveProvider
**Path**: `src/app/setup/ioc/aave.py`

Registers `AaveGateway` and `AaveAdapter`.

### 8.2 MorphoProvider
**Path**: `src/app/setup/ioc/morpho.py`

Registers Morpho queries and gateway.

### 8.3 HyperliquidProvider
**Path**: `src/app/setup/ioc/hyperliquid.py`

Registers Hyperliquid adapter and queries.

### 8.4 CurveProvider
**Path**: `src/app/setup/ioc/curve.py`

Registers Curve gateway and queries.

### 8.5 LayerZeroProvider
**Path**: `src/app/setup/ioc/layerzero.py`

Registers LayerZero gateway and queries.

### 8.6 AxelarProvider
**Path**: `src/app/setup/ioc/axelar.py`

Registers Axelar gateway and queries.

---

## References

- **Domain Ports**: `src/app/domain/ports/`
- **Infrastructure Adapters**: `src/app/infrastructure/adapters/external/`
- **Application Queries**: `src/app/application/queries/`
- **Data Providers**: `src/app/infrastructure/defi/providers/`
- **Agent Tools**: `src/app/infrastructure/defi/tools/`
