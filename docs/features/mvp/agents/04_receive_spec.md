# Receive — Chat Agent Response Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Chat Response Enrichment (conversations/messages)  
**Intent**: `RECEIVE`  
**Related**: Wallet Receive Endpoint (GET /api/v1/wallet/receive), Privy Embedded Wallets

---

## Overview

When a user asks to receive crypto in the chat (e.g., "I want to receive ETH", "give me my deposit address", "receive on Ethereum"), the unified chat router directs to the **Receive Handler** which calls the existing `GET /api/v1/wallet/receive` endpoint internally and enriches the response with a **QR code image** for easy scanning. The frontend renders the QR code, address, chain selector, and safety warning directly in the chat bubble as a structured card.

---

## Intent Detection

### Trigger Phrases

```
"I want to receive crypto"
"receive ETH"
"receive on ethereum"
"deposit address"
"show my wallet address"
"give me my QR code"
"receive USDC on Base"
"I need to receive {token} on {chain}"
"how do I deposit?"
"send me crypto"
```

### Entity Extraction

```python
intent = "RECEIVE"
confidence >= 0.90
entities = [
    {"type": "cryptocurrency", "value": "ETH", "confidence": 0.95},
    {"type": "blockchain", "value": "ethereum", "confidence": 0.90}
]
# If no chain specified → default to Base (lowest fees)
# If no token specified → show all supported tokens for selected chain
```

### Chain Resolution

```python
CHAIN_ALIASES = {
    "ethereum": 1, "eth": 1, "mainnet": 1,
    "base": 8453,
    "hyperevm": 998, "hyperliquid": 998, "hl": 998,
}

def resolve_chain_id(chain_text: str | None) -> int | None:
    """Resolve user's chain reference to chain_id."""
    if not chain_text:
        return None  # Show all chains
    return CHAIN_ALIASES.get(chain_text.lower())
```

---

## Response Schema

### Enrichment Block: `receive_info`

```python
class ReceiveInfoEnrichment(BaseModel):
    type: Literal["receive_info"] = "receive_info"
    address: str                          # User's Privy EVM address
    qr_data: str                          # EIP-681 URI for QR encoding
    qr_image_url: str                     # Server-generated QR code image URL
    selected_chain: ChainDisplay          # Currently selected chain
    available_chains: list[ChainDisplay]  # All supported chains
    supported_tokens: list[TokenDisplay]  # Tokens receivable on selected chain
    warning: str                          # Safety warning
    copy_actions: list[CopyAction]        # Quick copy buttons

class ChainDisplay(BaseModel):
    chain_id: int                         # 1, 8453, 998
    name: str                             # "Ethereum", "Base", "HyperEVM"
    icon: str                             # Icon identifier
    is_selected: bool                     # True for default/requested chain
    estimated_fee: str                    # "~$0.01" for Base, "~$5-15" for Ethereum
    confirmation_time: str                # "~2s" for Base, "~15s" for Ethereum

class TokenDisplay(BaseModel):
    symbol: str                           # "ETH", "USDC"
    name: str                             # "Ethereum", "USD Coin"
    address: str                          # Contract or "native"
    icon_url: str | None
    is_requested: bool                    # True if user asked for this specific token

class CopyAction(BaseModel):
    label: str                            # "Copy Address", "Copy QR Data"
    value: str                            # The string to copy
    icon: str                             # "copy", "qr"
```

### Example Response

```json
{
  "user_message": { "content": "I want to receive ETH on Ethereum", ... },
  "agent_message": {
    "content": "Here's your Ethereum deposit address! You can receive ETH and any ERC-20 tokens at this address on the Ethereum network. Scan the QR code or copy the address below.\n\n⚠️ Only send tokens on the Ethereum network to this address. Sending on the wrong network may result in permanent loss.",
    "agent_type": "receive_handler"
  },
  "routing": {
    "intent": "RECEIVE",
    "confidence": 0.95,
    "handler": "receive_handler"
  },
  "enrichment": {
    "receive_info": {
      "type": "receive_info",
      "address": "0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d",
      "qr_data": "ethereum:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d@1",
      "qr_image_url": "https://api.anvil.finance/api/v1/wallet/receive/qr?address=0x7a23...&chain_id=1&size=300",
      "selected_chain": {
        "chain_id": 1,
        "name": "Ethereum",
        "icon": "ethereum",
        "is_selected": true,
        "estimated_fee": "~$5-15",
        "confirmation_time": "~15 seconds"
      },
      "available_chains": [
        {
          "chain_id": 1,
          "name": "Ethereum",
          "icon": "ethereum",
          "is_selected": true,
          "estimated_fee": "~$5-15",
          "confirmation_time": "~15 seconds"
        },
        {
          "chain_id": 8453,
          "name": "Base",
          "icon": "base",
          "is_selected": false,
          "estimated_fee": "~$0.01",
          "confirmation_time": "~2 seconds"
        },
        {
          "chain_id": 998,
          "name": "HyperEVM",
          "icon": "hyperliquid",
          "is_selected": false,
          "estimated_fee": "~$0.001",
          "confirmation_time": "~1 second"
        }
      ],
      "supported_tokens": [
        {
          "symbol": "ETH",
          "name": "Ethereum",
          "address": "native",
          "icon_url": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
          "is_requested": true
        },
        {
          "symbol": "USDC",
          "name": "USD Coin",
          "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
          "icon_url": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
          "is_requested": false
        },
        {
          "symbol": "USDT",
          "name": "Tether",
          "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
          "icon_url": null,
          "is_requested": false
        },
        {
          "symbol": "DAI",
          "name": "Dai",
          "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
          "icon_url": null,
          "is_requested": false
        },
        {
          "symbol": "WBTC",
          "name": "Wrapped Bitcoin",
          "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
          "icon_url": null,
          "is_requested": false
        }
      ],
      "warning": "⚠️ Only send supported tokens on the Ethereum network to this address. Sending tokens on the wrong network may result in permanent loss of funds.",
      "copy_actions": [
        { "label": "Copy Address", "value": "0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d", "icon": "copy" },
        { "label": "Share QR", "value": "ethereum:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d@1", "icon": "qr" }
      ]
    }
  }
}
```

---

## QR Code Generation

### QR Image Endpoint

```
GET /api/v1/wallet/receive/qr
```

**Auth**: Required (JWT Bearer Token)  
**Response**: PNG image  
**Cache**: 24h (address doesn't change)

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| address | string | required | EVM address |
| chain_id | int | 8453 | Chain for EIP-681 encoding |
| size | int | 300 | Image size in pixels (100-500) |
| format | string | "png" | "png" or "svg" |
| logo | bool | true | Include Anvil logo in center |

### QR Data Format (EIP-681)

```python
def build_qr_data(address: str, chain_id: int) -> str:
    """Build EIP-681 URI for QR code."""
    # Standard format: ethereum:{address}@{chain_id}
    return f"ethereum:{address}@{chain_id}"

# Examples:
# Ethereum: ethereum:0x7a23...@1
# Base:     ethereum:0x7a23...@8453
# HyperEVM: ethereum:0x7a23...@998
```

### QR Code Generation (Server-Side)

```python
import qrcode
from io import BytesIO
from PIL import Image

class QRCodeGenerator:
    """Generate QR codes for deposit addresses."""

    def generate(
        self,
        data: str,
        size: int = 300,
        include_logo: bool = True,
    ) -> bytes:
        """Generate QR code PNG bytes."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High correction for logo overlay
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.LANCZOS)

        if include_logo:
            img = self._add_logo_overlay(img, size)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _add_logo_overlay(self, img: Image, size: int) -> Image:
        """Add Anvil logo in the center of the QR code."""
        logo_size = size // 5  # Logo is 20% of QR size
        logo = Image.open("assets/anvil-logo-small.png")
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # Center logo
        pos = ((size - logo_size) // 2, (size - logo_size) // 2)
        img.paste(logo, pos, logo if logo.mode == "RGBA" else None)
        return img
```

---

## Integration with Existing Endpoint

The chat handler **internally calls** the existing `GET /api/v1/wallet/receive` endpoint logic (reuses the same query handler) and wraps the result with QR-specific data:

```python
class ReceiveChatHandler:
    """Handles RECEIVE intent in chat context."""

    async def handle(self, message: str, context: ChatContext) -> ReceiveInfoEnrichment:
        # 1. Extract chain from user message
        chain_id = self._extract_chain(message, context.entities)
        token = self._extract_token(message, context.entities)

        # 2. Reuse existing ReceiveInfo query handler
        receive_info = await self._get_receive_info_handler.handle(
            GetReceiveInfoQuery(
                user_id=context.user_id,
                chain_id=chain_id,
            )
        )

        # 3. Build QR image URL
        selected_chain_id = chain_id or 8453  # Default to Base
        qr_data = f"ethereum:{receive_info.address}@{selected_chain_id}"
        qr_image_url = (
            f"{self._api_base}/api/v1/wallet/receive/qr"
            f"?address={receive_info.address}"
            f"&chain_id={selected_chain_id}"
            f"&size=300"
        )

        # 4. Build chain displays with fee estimates
        chains = [
            ChainDisplay(
                chain_id=c.chain_id,
                name=c.name,
                icon=c.icon,
                is_selected=(c.chain_id == selected_chain_id),
                estimated_fee=CHAIN_FEE_ESTIMATES[c.chain_id],
                confirmation_time=CHAIN_CONFIRMATION_TIMES[c.chain_id],
            )
            for c in receive_info.chains
        ]

        # 5. Mark requested token
        tokens = [
            TokenDisplay(
                symbol=t.symbol,
                name=t.name,
                address=t.address,
                icon_url=t.icon_url,
                is_requested=(token and t.symbol.upper() == token.upper()),
            )
            for t in receive_info.chains_by_id[selected_chain_id].supported_tokens
        ]

        return ReceiveInfoEnrichment(
            address=receive_info.address,
            qr_data=qr_data,
            qr_image_url=qr_image_url,
            selected_chain=next(c for c in chains if c.is_selected),
            available_chains=chains,
            supported_tokens=tokens,
            warning=receive_info.warning,
            copy_actions=[
                CopyAction(label="Copy Address", value=receive_info.address, icon="copy"),
                CopyAction(label="Share QR", value=qr_data, icon="qr"),
            ],
        )
```

### Fee Estimates (Static Config)

```python
CHAIN_FEE_ESTIMATES = {
    1: "~$5-15",       # Ethereum mainnet
    8453: "~$0.01",    # Base L2
    998: "~$0.001",    # HyperEVM
}

CHAIN_CONFIRMATION_TIMES = {
    1: "~15 seconds",
    8453: "~2 seconds",
    998: "~1 second",
}
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/wallet/receive_qr.py` | QR image endpoint |
| **Application** | `handlers/chat/receive_chat_handler.py` | Chat intent handler |
| **Application** | `queries/wallet/get_receive_info.py` | Existing query handler (reused) |
| **Application** | `services/qr_code_generator.py` | QR code PNG/SVG generation |
| **Domain** | `entities/receive_info.py` | ReceiveInfo, ChainInfo (existing) |
| **Infrastructure** | `adapters/wallet/privy_wallet_adapter.py` | Get user address (existing) |
| **Infrastructure** | `adapters/cache/redis_qr_cache.py` | Cache generated QR images |

---

## Chain Selection UX

When user switches chains in the chat card, frontend sends a follow-up:

```
POST /api/v1/user/chat/conversations/{id}/messages
{ "content": "__chain_switch:8453" }
```

This internal command triggers the receive handler again with the new chain_id, returning updated QR data and token list without a full new message — just an enrichment update.

Alternatively, the frontend can handle chain switching client-side by constructing the QR data locally:

```typescript
// Frontend-only chain switch (no backend call needed)
const switchChain = (chainId: number) => {
  const newQrData = `ethereum:${address}@${chainId}`;
  const newQrUrl = `${API_BASE}/api/v1/wallet/receive/qr?address=${address}&chain_id=${chainId}&size=300`;
  // Update UI with new QR
};
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Total response time | < 500ms |
| Wallet address lookup | < 100ms (DB query) |
| QR code generation | < 200ms (first time), <1ms (cached) |
| QR image serving | < 50ms (CDN cached) |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No wallet | "You don't have a wallet yet. Let me help you set one up!" + Privy connect CTA |
| Invalid chain | "I don't support that network yet. Available: Ethereum, Base, HyperEVM" |
| QR generation fails | Return address + qr_data without image URL (frontend generates client-side) |

---

## Frontend Rendering

```
┌─────────────────────────────────────────┐
│  📥 Receive ETH on Ethereum             │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │                                     ││
│  │        ┌───────────────┐            ││
│  │        │               │            ││
│  │        │   [QR CODE]   │            ││
│  │        │   (with logo) │            ││
│  │        │               │            ││
│  │        └───────────────┘            ││
│  │                                     ││
│  │  0x7a23B8c9D4e5F6a7b8c9d4...       ││
│  │  [📋 Copy]  [📤 Share]              ││
│  │                                     ││
│  │  Network: [Ethereum ▼]              ││
│  │  Fee: ~$5-15 · ~15 seconds          ││
│  │                                     ││
│  │  Supported: ETH · USDC · USDT ·    ││
│  │             DAI · WBTC              ││
│  │                                     ││
│  │  ⚠️ Only send on Ethereum network   ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Dependencies

```bash
pip install qrcode[pil] Pillow
# or for SVG output: pip install qrcode[svg]
```

---

## Open Items

- [ ] QR code style: black/white classic vs branded (dark mode compatible)
- [ ] Anvil logo asset for QR overlay
- [ ] Client-side QR generation as fallback (react-native-qrcode-svg)
- [ ] Deep link support: clicking QR opens wallet app with pre-filled address
- [ ] Notification when deposit received: "You received 0.5 ETH on Base!"
- [ ] Verify HyperEVM chain_id (998 vs 999) and USDC contract address
