# Wallet Receive Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-08  
**Status**: Specification  
**Intent**: RECEIVE  
**Recallium**: Memory #1696, #1697

---

## Overview

Backend endpoint to provide authenticated users with their deposit address, QR code data, and supported chain information. Since Privy creates EVM-compatible embedded wallets, the **same address works across all EVM chains** (Ethereum, Base, HyperEVM). The user selects the network to ensure they send on the correct chain.

---

## Endpoint

```
GET /api/v1/wallet/receive?chain_id={chain_id}
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)

### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| chain_id | int | No | null | Filter to specific chain. If null, returns all supported chains |

---

## Response Schema

```python
class SupportedToken(BaseModel):
    symbol: str                     # "ETH", "USDC"
    address: str                    # Contract address or "native"
    decimals: int                   # 18, 6, etc.
    icon_url: str | None = None

class ChainInfo(BaseModel):
    chain_id: int
    name: str                       # "Ethereum", "Base", "HyperEVM"
    network: str                    # "mainnet", "base", "hyperevm"
    icon: str                       # Icon identifier for frontend
    explorer_url: str               # With {address} placeholder resolved
    supported_tokens: list[SupportedToken]

class ReceiveResponse(BaseModel):
    address: str                    # User's Privy EVM address (same across all chains)
    qr_data: str                    # EIP-681 URI for QR encoding
    qr_image_url: str | None       # Optional: pre-rendered QR image URL
    chains: list[ChainInfo]         # Supported chains with tokens
    selected_chain_id: int          # Currently selected chain for QR
    warning: str                    # Safety warning for user
```

---

## Supported Chains

| Chain | chain_id | Tokens | Explorer |
|-------|----------|--------|----------|
| Ethereum | 1 | ETH, USDC, USDT, DAI, WBTC | etherscan.io |
| Base | 8453 | ETH, USDC, DAI | basescan.org |
| HyperEVM | 998 (TBD) | HYPE, USDC | explorer.hyperliquid.xyz |

**QR format**: EIP-681 → `ethereum:{address}@{chain_id}`

---

## Example Response

```json
{
  "address": "0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d",
  "qr_data": "ethereum:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d@8453",
  "qr_image_url": null,
  "selected_chain_id": 8453,
  "chains": [
    {
      "chain_id": 1,
      "name": "Ethereum",
      "network": "mainnet",
      "icon": "ethereum",
      "explorer_url": "https://etherscan.io/address/0x7a23B8c9...",
      "supported_tokens": [
        {"symbol": "ETH", "address": "native", "decimals": 18, "icon_url": null},
        {"symbol": "USDC", "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6, "icon_url": null},
        {"symbol": "USDT", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6, "icon_url": null},
        {"symbol": "DAI", "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "decimals": 18, "icon_url": null},
        {"symbol": "WBTC", "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "decimals": 8, "icon_url": null}
      ]
    },
    {
      "chain_id": 8453,
      "name": "Base",
      "network": "base",
      "icon": "base",
      "explorer_url": "https://basescan.org/address/0x7a23B8c9...",
      "supported_tokens": [
        {"symbol": "ETH", "address": "native", "decimals": 18, "icon_url": null},
        {"symbol": "USDC", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "decimals": 6, "icon_url": null},
        {"symbol": "DAI", "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb", "decimals": 18, "icon_url": null}
      ]
    },
    {
      "chain_id": 998,
      "name": "HyperEVM",
      "network": "hyperevm",
      "icon": "hyperliquid",
      "explorer_url": "https://explorer.hyperliquid.xyz/address/0x7a23B8c9...",
      "supported_tokens": [
        {"symbol": "HYPE", "address": "native", "decimals": 18, "icon_url": null},
        {"symbol": "USDC", "address": "0x...", "decimals": 6, "icon_url": null}
      ]
    }
  ],
  "warning": "Only send supported tokens on the selected network to this address. Sending tokens on the wrong network may result in permanent loss."
}
```

---

## Agent Integration

RECEIVE intent triggers `receive_card` UI component with QR + address + chain selector:

```python
async def handle_receive_intent(user_id, conversation_id, params):
    receive_info = await get_receive_info_handler.handle(
        GetReceiveInfoQuery(user_id=user_id, chain_id=params.get("chain_id"))
    )
    return AgentResponse(
        message="Here's your wallet address to receive tokens:",
        type="receive",
        data={...},
        ui_component="receive_card",
    )
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/wallet/receive.py` | HTTP endpoint + validation |
| **Application** | `queries/wallet/get_receive_info.py` | Query handler (CQRS) |
| **Domain** | `ports/wallet/wallet_repository.py` | Existing port (get_primary) |
| **Domain** | `entities/receive_info.py` | ReceiveInfo value object |
| **Infrastructure** | `adapters/wallet/chain_config.py` | Chain registry + token lists |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | NO_WALLET | User has no Privy wallet set up |
| 400 | UNSUPPORTED_CHAIN | Invalid chain_id parameter |

---

## Open Items

- [ ] HyperEVM mainnet chain_id (998 vs 999?)
- [ ] USDC contract address on HyperEVM
- [ ] QR rendering: backend or frontend? (spec defaults to frontend)
- [ ] Deposit monitoring/notification when funds arrive (future)
