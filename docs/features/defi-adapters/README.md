# DeFi Adapters

This directory contains documentation for DeFi protocol integrations in the Anvil Backend.

## Overview

The Anvil Backend integrates with multiple DeFi protocols to provide:
- Lending and borrowing data (Aave, Morpho)
- DEX liquidity and swap quotes (Curve)
- Perpetual futures trading (Hyperliquid)
- Cross-chain bridging (Axelar, LayerZero)
- NFT marketplace data (OpenSea)

## Documentation

| Document | Description |
|----------|-------------|
| [DEFI_ADAPTERS_GUIDE.md](./DEFI_ADAPTERS_GUIDE.md) | Complete guide for DeFi adapters |

## Architecture

All DeFi integrations follow the hexagonal architecture pattern:

```
Domain Layer
├── Ports (Interfaces)
│   └── *Gateway.py
├── Entities
│   └── Protocol-specific entities
└── Value Objects
    └── Protocol-specific value objects

Infrastructure Layer
├── Adapters
│   └── *_adapter.py (implements ports)
└── Clients
    └── *_client.py (API wrappers)
```

## Available Integrations

| Protocol | Type | Status |
|----------|------|--------|
| Aave V3 | Lending/Borrowing | ✅ Active |
| Morpho | Optimized Lending | ✅ Active |
| Curve Finance | DEX/Liquidity | ✅ Active |
| Hyperliquid | Perpetuals | ✅ Active |
| LayerZero | Cross-chain Messaging | ✅ Active |
| Axelar | Cross-chain Bridge | ✅ Active |
| OpenSea | NFT Marketplace | ✅ Active |

## Quick Start

See [DEFI_ADAPTERS_GUIDE.md](./DEFI_ADAPTERS_GUIDE.md) for:
- Implementation patterns
- Testing strategies
- Adding new adapters
- Configuration options

## Related Documentation

- [Frontend API Reference](../../frontend/FRONTEND_API_COMPLETE_REFERENCE.md)
- [User Modules Index](../../frontend/user-modules/USER_MODULES_INDEX.md)
- [Enterprise Libs Integration](../enterprise-libs-integration/)
