# Anvil Frontend API Specs — Master Index

**Date**: 2026-02-09  
**Status**: Complete  
**Purpose**: Backend API specifications for all frontend shortcut screens and core features.

---

## Endpoint Inventory

| # | Spec File | Feature | Status | Recallium |
|---|-----------|---------|--------|-----------|
| 1 | `01_chat_mode_spec.md` | Chat Mode (casual/power user/degen) | 🆕 NEW | Stored this session |
| 2 | `02_activities_spec.md` | Activity Feed (GET list + detail) | 🆕 NEW | Stored this session |
| 3 | `03_receive_spec.md` | Receive (QR + address + chain selector) | ✅ EXISTS | #1696, #1697 |
| 4 | `04_send_spec.md` | Send (tokens → preview → execute) | ✅ EXISTS | #1699, #1700, #1701 |
| 5 | `05_swap_spec.md` | Swap (defaults → from → to) | ✅ EXISTS | #1702–#1706 |
| 6 | `06_balance_spec.md` | Balance Dashboard (portfolio + P&L) | ✅ EXISTS | #1706–#1710 |
| 7 | `07_cashout_spec.md` | Cash Out (off-ramp USDC → fiat) | 🆕 NEW | Stored this session |

---

## Shortcut → Endpoint Mapping

| Shortcut Button | Primary Endpoint | Screen |
|----------------|------------------|--------|
| **Cash In** | `POST /conversations/{id}/messages` (buy intent) | Chat-based buy flow (MoonPay) |
| **Cash Out** | `GET /api/v1/wallet/cashout` | Cash Out screen |
| **Swap** | `GET /api/v1/swap/defaults` | Swap screen |
| **Send** | `GET /api/v1/wallet/send/tokens` | Send screen |
| **Receive** | `GET /api/v1/wallet/receive` | Receive screen (QR) |
| **Portfolio** | `GET /api/v1/wallet/balance` | Balance dashboard |
| **Activity** | `GET /api/v1/activities` | Activity feed |

---

## Shared Infrastructure

All endpoints reuse these core components:

| Component | Used By |
|-----------|---------|
| `RPCBalanceProvider` | Send, Swap, Balance, Cash Out |
| `CoinGeckoClient` | Send, Swap, Balance, Activities |
| `ChainRegistry` | Send, Swap, Receive |
| `WalletRepository` | All authenticated endpoints |
| `HyperliquidClient` | Swap (defaults + to-tokens) |

---

## Auth Pattern

All endpoints require **JWT Bearer Token** via Privy authentication. Standard rate limit: 200 requests/hour per user.
