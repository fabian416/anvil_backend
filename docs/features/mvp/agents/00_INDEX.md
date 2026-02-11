# Anvil Chat Agent Specifications — Index

**Date**: 2026-02-02  
**Context**: Chat Response Enrichments for `POST /conversations/{id}/messages`  
**Total Specs**: 7

---

## Specifications

| # | Spec | File | Intent | Description |
|---|------|------|--------|-------------|
| 01 | **Join Waitlist** | `01_join_waitlist_spec.md` | N/A (post-processing) | Periodic CTA injected into chat responses (1 per 10-20 min) to convert guests → waitlist. A/B variants, Redis cooldown, dismiss tracking. |
| 02 | **Sentiment Analysis** | `02_sentiment_analysis_spec.md` | `HUNTER_SENTIMENT` | Token sentiment with chart_url, weighted score from CoinGecko + Fear & Greed + social + on-chain signals. |
| 03 | **Balance Overview** | `03_balance_overview_spec.md` | `BALANCE_CHECK` | Portfolio with per-token holdings, FIFO P&L, chart_url per token, AI recommendations (earn yield, take profit, diversify). |
| 04 | **Receive** | `04_receive_spec.md` | `RECEIVE` | QR code generation with EIP-681 URI, chain selector, fee estimates. Integrates existing GET /wallet/receive endpoint. |
| 05 | **Swap (available_swaps)** | `05_swap_available_swaps_spec.md` | `SWAP` | Multi-provider quote aggregation (Hyperliquid, 1inch, 0x) in parallel. User selects provider → execute via provider_id. |
| 06 | **Wallet QR Storage** | `06_wallet_qr_storage_spec.md` | `RECEIVE` | Pre-generated QR codes stored with wallet records. DigitalOcean Spaces CDN or local fallback. Celery task generates/migrates QRs every 3 min. |
| 07 | **Morpho Withdraw** | `07_morpho_withdraw_implementation_spec.md` | `LENDING_WITHDRAW` | Morpho Blue withdraw: MCP tool, Celery confirm task, LendingWorkflowAgent withdraw flow, execute integration. |
| 08 | **Money Market Positions** | `08_money_market_positions_spec.md` | Route to `LENDING_WORKFLOW` | “My money market positions” + withdraw: route to LendingWorkflow (Aave + Morpho supply positions), reuse existing execute flow. CTO methodology. |

---

## Common Architecture

All specs produce structured data in the `enrichment` field of the `UnifiedChatResponse`:

```
POST /api/v1/user/chat/conversations/{id}/messages
→ Intent Detection → Handler Routing → Handler → Response
                                                    │
                                                    ├── agent_message.content (text)
                                                    ├── routing (intent, handler, confidence)
                                                    └── enrichment
                                                        ├── sentiment_analysis  (spec 02)
                                                        ├── balance_overview    (spec 03)
                                                        ├── receive_info        (spec 04)
                                                        ├── swap_confirm        (spec 05)
                                                        └── join_waitlist       (spec 01, post-processing)
```

---

## Shared Components

| Component | Used By | Description |
|-----------|---------|-------------|
| `ChartURLBuilder` | Sentiment, Balance | Constructs `/api/v1/charts/{token}` URLs |
| `CoinGecko Client` | Sentiment, Balance, Swap | Prices, market data, OHLCV |
| `Redis Cache` | Waitlist CTA, Swap Quotes | Cooldowns, quote caching (5 min TTL) |
| `WalletRepository` | Receive, Balance, Swap | User address from Privy |
| `BalanceProvider` | Balance, Swap (from-tokens) | On-chain RPC balance reads |

---

## New Endpoints Required

| Endpoint | Spec | Description |
|----------|------|-------------|
| `GET /api/v1/charts/{token}` | 02, 03 | Token price chart image (PNG/SVG) |
| `GET /api/v1/wallet/receive/qr` | 04 | QR code image generation |
| `POST /api/v1/swap/execute` | 05 | Execute swap by provider_id (updated) |
| `POST /api/v1/chat/waitlist-cta/dismiss` | 01 | Dismiss CTA tracking |
| `POST /api/v1/waitlist/join` | 01 | Join waitlist |

---

## New Database Tables

| Table | Spec | Description |
|-------|------|-------------|
| `waitlist_entries` | 01 | Waitlist registrations with position, referral, A/B variant |

---

## Dependencies

```bash
pip install qrcode[pil] Pillow    # QR code generation (spec 04)
pip install matplotlib             # Chart rendering option A (spec 02, 03)
# Or: pip install cairosvg         # SVG chart rendering
```
